"""
協力ゲーム画面 — 2人で1つのボードを操作
P1スマホ=上下(pitch)、P2スマホ=左右(roll)、キーボードでも操作可
"""

import math

from ursina import Vec2, Text, Entity, camera, held_keys, color

from screens.game_base import GameScreenBase


class CoopGameScreen(GameScreenBase):

    def _create_input(self):
        self.max_tilt = 12
        self.tilt_speed = 25
        self.motion_scale = 1.0
        self.kb_tilt = Vec2(0, 0)
        self.p1_phone_tilt_y = 0.0
        self.p2_phone_tilt_x = 0.0

    # --- モード名（右上） ---
        _blue_color = color.hex('#1D09FF')
        self._add(Text(
            text='協 力',
            position=(0.58, 0.32),
            origin=(0.5, 0),
            font='assets/fonts/DotGothic16-Regular.ttf',
            scale=1.6,
            color=_blue_color,
        ))
        # 下線
        self._add(Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.11, 0.003),
            position=(0.53, 0.295),
            color=_blue_color,
        ))

        # 1p&2p.png（ステージ番号の下・左側）
        self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='assets/1p&2p',
            scale=(0.2028, 0.13),
            position=(-0.50, 0.22),
        ))

    def _get_board_tilt(self, dt) -> Vec2:
        # キーボード（フォールバック）
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

        # P1スマホ: 上下(pitch)のみ
        sensor_p1 = self.webrtc.get_latest_sensor_data(player_id=1)
        if sensor_p1 is not None:
            self.p1_phone_tilt_y = max(-self.max_tilt, min(
                self.max_tilt, math.degrees(-sensor_p1.pitch) * self.motion_scale))
        else:
            self.p1_phone_tilt_y *= 0.92

        # P2スマホ: 左右(roll)のみ
        sensor_p2 = self.webrtc.get_latest_sensor_data(player_id=2)
        if sensor_p2 is not None:
            self.p2_phone_tilt_x = max(-self.max_tilt, min(
                self.max_tilt, math.degrees(sensor_p2.roll) * self.motion_scale))
        else:
            self.p2_phone_tilt_x *= 0.92

        # スマホ入力 + キーボード（フォールバック）を合成
        combined = Vec2(
            max(-self.max_tilt, min(self.max_tilt, self.kb_tilt.x + self.p2_phone_tilt_x)),
            max(-self.max_tilt, min(self.max_tilt, self.kb_tilt.y + self.p1_phone_tilt_y)),
        )
        return combined

    def _on_reset(self):
        self.kb_tilt = Vec2(0, 0)
        self.p1_phone_tilt_y = 0.0
        self.p2_phone_tilt_x = 0.0

    def _update_status(self):
        pass
