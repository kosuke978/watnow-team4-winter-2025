"""
協力ゲーム画面 — 2人で1つのボードを操作（キーボード + スマホ加算合成）
"""

import math

from ursina import Vec2, held_keys, color

from screens.game_base import GameScreenBase


class CoopGameScreen(GameScreenBase):

    def _create_input(self):
        self.max_tilt = 12
        self.tilt_speed = 25
        self.motion_scale = 1.0
        self.kb_tilt = Vec2(0, 0)
        self.phone_tilt = Vec2(0, 0)

    def _get_board_tilt(self, dt) -> Vec2:
        # P1: キーボード
        if held_keys['left arrow']:
            self.kb_tilt.x = max(self.kb_tilt.x - self.tilt_speed * dt, -self.max_tilt)
        if held_keys['right arrow']:
            self.kb_tilt.x = min(self.kb_tilt.x + self.tilt_speed * dt, self.max_tilt)
        if held_keys['up arrow']:
            self.kb_tilt.y = min(self.kb_tilt.y + self.tilt_speed * dt, self.max_tilt)
        if held_keys['down arrow']:
            self.kb_tilt.y = max(self.kb_tilt.y - self.tilt_speed * dt, -self.max_tilt)

        keyboard_active = (
            held_keys['left arrow'] or held_keys['right arrow'] or
            held_keys['up arrow'] or held_keys['down arrow']
        )
        if not keyboard_active:
            self.kb_tilt.x *= 0.92
            self.kb_tilt.y *= 0.92

        # P2: スマホセンサー
        sensor = self.webrtc.get_latest_sensor_data()
        if sensor is not None:
            self.phone_tilt.x = max(-self.max_tilt, min(
                self.max_tilt, math.degrees(-sensor.roll) * self.motion_scale))
            self.phone_tilt.y = max(-self.max_tilt, min(
                self.max_tilt, math.degrees(sensor.pitch) * self.motion_scale))
        else:
            self.phone_tilt.x *= 0.92
            self.phone_tilt.y *= 0.92

        # 加算合成
        combined = Vec2(
            max(-self.max_tilt, min(self.max_tilt, self.kb_tilt.x + self.phone_tilt.x)),
            max(-self.max_tilt, min(self.max_tilt, self.kb_tilt.y + self.phone_tilt.y)),
        )
        return combined

    def _on_reset(self):
        self.kb_tilt = Vec2(0, 0)
        self.phone_tilt = Vec2(0, 0)

    def _update_status(self):
        if self.webrtc.is_connected:
            self.status_text.text = 'P1: Keyboard | P2: Phone'
            self.status_text.color = color.lime
        else:
            self.status_text.text = 'P1: Keyboard | P2: Waiting...'
            self.status_text.color = color.light_gray
