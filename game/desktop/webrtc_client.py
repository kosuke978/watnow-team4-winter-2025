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
        self._button_queue: dict[int, list[str]] = {}  # player_id → [button, ...]
        self._player_names: dict[int, str] = {}       # player_id → name
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
        # ゲームクライアントとして接続（プレイヤー枠を消費しない）
        sep = "&" if "?" in self.signaling_url else "?"
        url = f"{self.signaling_url}{sep}role=game"
        async with websockets.connect(url) as ws:
            self._status = "connected"
            print(f"[WS] Connected to server: {self.signaling_url}")

            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                msg_type = msg.get("type")
                if msg_type == "sensor_data":
                    self._on_sensor_message(msg)
                elif msg_type == "button":
                    self._on_button_message(msg)
                elif msg_type == "player_name":
                    self._on_player_name_message(msg)

    def _on_player_name_message(self, msg: dict):
        player_id = msg.get("player_id", 1)
        name = msg.get("player_name", "")
        if name:
            with self._lock:
                self._player_names[player_id] = name
            print(f"[WS] P{player_id} name: {name}")

    def get_player_name(self, player_id: int) -> str | None:
        """指定player_idの名前を返す。未設定ならNone。"""
        with self._lock:
            return self._player_names.get(player_id)

    def _on_button_message(self, msg: dict):
        button = msg.get("button", "")
        player_id = msg.get("player_id", 1)
        if button:
            with self._lock:
                self._button_queue.setdefault(player_id, []).append(button)

    def poll_buttons(self, player_id: int | None = None) -> list[str]:
        """メインスレッドから呼び出し: 溜まったボタンイベントを返してキューをクリアする。
        player_id指定時はそのプレイヤーのみ。Noneなら全プレイヤー分を返す。"""
        with self._lock:
            if player_id is not None:
                buttons = self._button_queue.pop(player_id, [])
            else:
                buttons = []
                for blist in self._button_queue.values():
                    buttons.extend(blist)
                self._button_queue.clear()
        return buttons

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
