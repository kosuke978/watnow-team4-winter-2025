"""
ソロゲーム画面 — 1ボード、1ボール、キーボード or スマホ操作
"""

from ursina import Vec2, color

from screens.game_base import GameScreenBase
from input_handler import InputHandler


class SoloGameScreen(GameScreenBase):

    def _create_input(self):
        self.input_handler = InputHandler(self.webrtc)

    def _get_board_tilt(self, dt) -> Vec2:
        return self.input_handler.update(dt)

    def _on_reset(self):
        self.input_handler.reset()

    def _update_status(self):
        status, connected = self.input_handler.get_status()
        self.status_text.text = status
        self.status_text.color = color.lime if connected else color.light_gray
