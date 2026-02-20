"""
WebSocket クライアント — シグナリングサーバー経由で iOS センサーデータを受信
バックグラウンドスレッドで asyncio ループを実行し、Ursina メインスレッドと共存する。
"""

import asyncio
import json
import threading
from dataclasses import dataclass

import websockets


@dataclass
class SensorData:
    acceleration_x: float = 0.0
    acceleration_y: float = 0.0
    acceleration_z: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    yaw: float = 0.0
    calibrated: bool = False
    timestamp: float = 0.0


class WebRTCClient:
    """WebSocket リレー経由でセンサーデータを受信するクライアント。
    インターフェースは旧 WebRTC 版と互換。"""

    def __init__(self, signaling_url: str = "ws://localhost:8080/ws"):
        self.signaling_url = signaling_url
        self._sensor_data = SensorData()
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._status = "disconnected"
        self._has_data = False

    @property
    def status(self) -> str:
        return self._status

    @property
    def is_connected(self) -> bool:
        return self._status == "connected"

    def get_latest_sensor_data(self) -> SensorData | None:
        if not self._has_data:
            return None
        with self._lock:
            return SensorData(
                acceleration_x=self._sensor_data.acceleration_x,
                acceleration_y=self._sensor_data.acceleration_y,
                acceleration_z=self._sensor_data.acceleration_z,
                pitch=self._sensor_data.pitch,
                roll=self._sensor_data.roll,
                yaw=self._sensor_data.yaw,
                calibrated=self._sensor_data.calibrated,
                timestamp=self._sensor_data.timestamp,
            )

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=3)

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._connect_loop())

    async def _connect_loop(self):
        while self._running:
            try:
                self._status = "connecting"
                await self._listen()
            except Exception as e:
                print(f"[WS] Error: {e}")
            finally:
                self._status = "disconnected"
                self._has_data = False
            if self._running:
                print("[WS] Reconnecting in 3s...")
                await asyncio.sleep(3)

    async def _listen(self):
        async with websockets.connect(self.signaling_url) as ws:
            self._status = "connected"
            print(f"[WS] Connected to server: {self.signaling_url}")

            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                if msg.get("type") == "sensor_data":
                    self._on_sensor_message(msg)

    def _on_sensor_message(self, msg: dict):
        accel = msg.get("acceleration", {})
        rot = msg.get("rotation", {})
        with self._lock:
            self._sensor_data.acceleration_x = accel.get("x", 0.0)
            self._sensor_data.acceleration_y = accel.get("y", 0.0)
            self._sensor_data.acceleration_z = accel.get("z", 0.0)
            self._sensor_data.pitch = rot.get("pitch", 0.0)
            self._sensor_data.roll = rot.get("roll", 0.0)
            self._sensor_data.yaw = rot.get("yaw", 0.0)
            self._sensor_data.calibrated = msg.get("calibrated", False)
            self._sensor_data.timestamp = msg.get("timestamp", 0.0)
        self._has_data = True
