"""
入力ハンドラー — キーボード＋WebSocketセンサー入力を統合
"""

import math

from ursina import Vec2, held_keys

from webrtc_client import WebRTCClient


class InputHandler:
    def __init__(self, webrtc_client: WebRTCClient, player_id: int | None = None,
                 max_tilt: float = 12, tilt_speed: float = 25, motion_scale: float = 1.0):
        self.webrtc = webrtc_client
        self.player_id = player_id
        self.max_tilt = max_tilt
        self.tilt_speed = tilt_speed
        self.motion_scale = motion_scale
        self.board_tilt = Vec2(0, 0)

    def reset(self):
        self.board_tilt = Vec2(0, 0)

    def update(self, dt) -> Vec2:
        # キーボード入力
        if held_keys['left arrow']:
            self.board_tilt.x = max(self.board_tilt.x - self.tilt_speed * dt, -self.max_tilt)
        if held_keys['right arrow']:
            self.board_tilt.x = min(self.board_tilt.x + self.tilt_speed * dt, self.max_tilt)
        if held_keys['up arrow']:
            self.board_tilt.y = min(self.board_tilt.y + self.tilt_speed * dt, self.max_tilt)
        if held_keys['down arrow']:
            self.board_tilt.y = max(self.board_tilt.y - self.tilt_speed * dt, -self.max_tilt)

        keyboard_active = (
            held_keys['left arrow'] or held_keys['right arrow'] or
            held_keys['up arrow'] or held_keys['down arrow']
        )

        # モーション入力
        sensor = self.webrtc.get_latest_sensor_data(self.player_id)
        if sensor is not None:
            self.board_tilt.x = max(-self.max_tilt, min(
                self.max_tilt, math.degrees(sensor.roll) * self.motion_scale))
            self.board_tilt.y = max(-self.max_tilt, min(
                self.max_tilt, math.degrees(-sensor.pitch) * self.motion_scale))
        elif not keyboard_active:
            self.board_tilt.x *= 0.92
            self.board_tilt.y *= 0.92

        return self.board_tilt

    def get_status(self) -> tuple[str, bool]:
        return f'Controller: {self.webrtc.status}', self.webrtc.is_connected
