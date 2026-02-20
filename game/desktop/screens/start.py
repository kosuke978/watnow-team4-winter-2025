"""
スタート画面 — タイトルとメニュー
"""

from ursina import Text, Button, color, application, window

from screens.base import Screen


class StartScreen(Screen):
    def __init__(self, manager):
        super().__init__(manager)

        self._add(Text(
            text='Ball Rolling Game',
            position=(0, 0.3),
            origin=(0, 0),
            scale=3,
            color=color.white,
        ))

        self._add(Text(
            text='Tilt the board and roll the ball into the hole!',
            position=(0, 0.2),
            origin=(0, 0),
            scale=1.2,
            color=color.light_gray,
        ))

        start_btn = self._add(Button(
            text='Start',
            scale=(0.3, 0.08),
            position=(0, 0.02),
            color=color.azure,
        ))
        start_btn.on_click = lambda: self.manager.switch('stage_select')

        howto_btn = self._add(Button(
            text='How to Play',
            scale=(0.3, 0.08),
            position=(0, -0.08),
            color=color.azure,
        ))
        howto_btn.on_click = lambda: self.manager.switch('how_to_play')

        quit_btn = self._add(Button(
            text='Quit',
            scale=(0.3, 0.08),
            position=(0, -0.18),
            color=color.gray,
        ))
        quit_btn.on_click = lambda: application.quit()

    def on_show(self, **kwargs):
        super().on_show()
        window.color = color.rgb(30, 30, 50)

    def input(self, key):
        if key == 'escape':
            application.quit()
