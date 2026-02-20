"""
使い方画面 — 操作説明
"""

from ursina import Text, Button, color, window

from screens.base import Screen


class HowToPlayScreen(Screen):
    def __init__(self, manager):
        super().__init__(manager)

        self._add(Text(
            text='How to Play',
            position=(0, 0.4),
            origin=(0, 0),
            scale=2.5,
            color=color.white,
        ))

        instructions = (
            '[Controls]\n'
            '\n'
            'Arrow Keys ... Tilt the board\n'
            'Phone      ... Tilt to control (WebSocket)\n'
            'R          ... Reset\n'
            'ESC        ... Back\n'
            '\n'
            '[Rules]\n'
            '\n'
            'Tilt the board to roll the ball.\n'
            'Get it into the goal hole to clear!\n'
            'Fall off the edge and you start over!'
        )
        self._add(Text(
            text=instructions,
            position=(0, 0.18),
            origin=(0, 0),
            scale=1.2,
            color=color.light_gray,
        ))

        back_btn = self._add(Button(
            text='Back',
            scale=(0.2, 0.06),
            position=(0, -0.35),
            color=color.gray,
        ))
        back_btn.on_click = lambda: self.manager.switch('start')

    def on_show(self, **kwargs):
        super().on_show()
        window.color = color.rgb(30, 30, 50)

    def input(self, key):
        if key == 'escape':
            self.manager.switch('start')
