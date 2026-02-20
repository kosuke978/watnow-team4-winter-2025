"""
UI表示 — タイトル・ステータス・クリア画面などのテキストUI
"""

from ursina import Text, color


class GameUI:
    def __init__(self):
        self.title_text = Text(
            text='Ball Rolling Game',
            position=(0, 0.45),
            origin=(0, 0),
            scale=2,
            color=color.white,
        )
        self.instruction_text = Text(
            text='Arrow keys or phone to tilt, R to reset, ESC to quit',
            position=(0, 0.38),
            origin=(0, 0),
            scale=1,
            color=color.light_gray,
        )
        self.status_text = Text(
            text='',
            position=(-0.85, -0.45),
            origin=(-0.5, 0),
            scale=0.8,
            color=color.light_gray,
        )
        self.win_text = Text(
            text='',
            position=(0, 0),
            origin=(0, 0),
            scale=3,
            color=color.yellow,
        )
        self.stage_text = Text(
            text='',
            position=(0, 0.32),
            origin=(0, 0),
            scale=1,
            color=color.light_gray,
        )

    def show_playing(self, status: str, is_connected: bool):
        self.status_text.text = status
        self.status_text.color = color.lime if is_connected else color.light_gray
        self.win_text.text = ''

    def show_clear(self, next_stage: bool = False):
        if next_stage:
            self.win_text.text = 'Clear!\nPress N for next stage / R to retry'
        else:
            self.win_text.text = 'Clear!\nPress R to retry'

    def show_stage_name(self, name: str):
        self.stage_text.text = name

    def update_status(self, text: str, connected: bool):
        self.status_text.text = text
        self.status_text.color = color.lime if connected else color.light_gray

    def clear_win(self):
        self.win_text.text = ''
