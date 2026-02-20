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
        self._sensor_data: dict[int, SensorData] = {}
        self._has_data: dict[int, bool] = {}
        self._lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._status = "disconnected"

    @property
    def status(self) -> str:
        return self._status

    @property
    def is_connected(self) -> bool:
        return self._status == "connected"

    def get_latest_sensor_data(self, player_id: int | None = None) -> SensorData | None:
        """指定player_idのデータを返す。Noneなら最初に見つかったデータを返す（後方互換）。"""
        with self._lock:
            if player_id is not None:
                if not self._has_data.get(player_id, False):
                    return None
                sd = self._sensor_data[player_id]
            else:
                # 後方互換: 最初に見つかったデータを返す
                for pid, has in self._has_data.items():
                    if has:
                        sd = self._sensor_data[pid]
                        break
                else:
                    return None
            return SensorData(
                acceleration_x=sd.acceleration_x,
                acceleration_y=sd.acceleration_y,
                acceleration_z=sd.acceleration_z,
                pitch=sd.pitch,
                roll=sd.roll,
                yaw=sd.yaw,
                calibrated=sd.calibrated,
                timestamp=sd.timestamp,
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
                with self._lock:
                    self._has_data.clear()
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
        player_id = msg.get("player_id", 1)
        accel = msg.get("acceleration", {})
        rot = msg.get("rotation", {})
        with self._lock:
            if player_id not in self._sensor_data:
                self._sensor_data[player_id] = SensorData()
            sd = self._sensor_data[player_id]
            sd.acceleration_x = accel.get("x", 0.0)
            sd.acceleration_y = accel.get("y", 0.0)
            sd.acceleration_z = accel.get("z", 0.0)
            sd.pitch = rot.get("pitch", 0.0)
            sd.roll = rot.get("roll", 0.0)
            sd.yaw = rot.get("yaw", 0.0)
            sd.calibrated = msg.get("calibrated", False)
            sd.timestamp = msg.get("timestamp", 0.0)
            self._has_data[player_id] = True
