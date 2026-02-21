"""
ソロゲーム画面 — 1ボード、1ボール、キーボード or スマホ操作
"""

from ursina import Vec2, Text, Entity, camera, color

from screens.game_base import GameScreenBase
from input_handler import InputHandler


class SoloGameScreen(GameScreenBase):

    def __init__(self, manager, webrtc_client, stages_dir):
        super().__init__(manager, webrtc_client, stages_dir)

        # --- モード名（右上） ---
        _mode_color = color.hex('#159151')
        self._add(Text(
            text='ひとりで',
            position=(0.60, 0.32),
            origin=(0.5, 0),
            font='assets/fonts/DotGothic16-Regular.ttf',
            scale=1.6,
            color=_mode_color,
        ))
        # 下線
        self._add(Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.16, 0.003),
            position=(0.52, 0.295),
            color=_mode_color,
        ))

    def _create_input(self):
        self.input_handler = InputHandler(self.webrtc, player_id=1)

    def _get_board_tilt(self, dt) -> Vec2:
        return self.input_handler.update(dt)

    def _on_reset(self):
        self.input_handler.reset()

    def _update_status(self):
        status, connected = self.input_handler.get_status()
        self.status_text.text = status
        self.status_text.color = color.lime if connected else color.light_gray
