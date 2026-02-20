"""
結果画面 — 対戦 / 協力・一人で の2バリエーション
"""

from ursina import Text, Button, color, window

from screens.base import Screen


class ResultScreen(Screen):
    def __init__(self, manager):
        super().__init__(manager)

        self.title = self._add(Text(
            text='',
            position=(0, 0.3),
            origin=(0, 0),
            scale=3,
            color=color.yellow,
        ))

        self.mode_label = self._add(Text(
            text='',
            position=(0, 0.18),
            origin=(0, 0),
            scale=1,
            color=color.light_gray,
        ))

        self.info_text = self._add(Text(
            text='',
            position=(0, 0.08),
            origin=(0, 0),
            scale=1.5,
            color=color.white,
        ))

        # ボタン
        self.retry_btn = self._add(Button(
            text='Retry',
            scale=(0.25, 0.07),
            position=(-0.15, -0.1),
            color=color.azure,
        ))

        self.next_btn = self._add(Button(
            text='Next Stage',
            scale=(0.25, 0.07),
            position=(0.15, -0.1),
            color=color.azure,
        ))

        self.menu_btn = self._add(Button(
            text='Stage Select',
            scale=(0.25, 0.07),
            position=(0, -0.22),
            color=color.gray,
        ))

        # 状態
        self.game_mode = 'solo'
        self.stage_path = None
        self.stage_index = 0
        self.next_stage_path = None

    def on_show(self, game_mode='solo', cleared=True, stage_index=0,
                stage_path=None, next_stage_path=None, elapsed_time=0,
                **kwargs):
        self.game_mode = game_mode
        self.stage_path = stage_path
        self.stage_index = stage_index
        self.next_stage_path = next_stage_path

        if game_mode == 'versus':
            self._show_versus_result(elapsed_time)
        else:
            self._show_solo_coop_result(cleared, elapsed_time, game_mode)

        # ボタン設定
        self.retry_btn.on_click = lambda: self.manager.switch(
            'game',
            stage_path=self.stage_path,
            stage_index=self.stage_index,
            game_mode=self.game_mode,
        )

        if next_stage_path:
            self.next_btn.on_click = lambda: self.manager.switch(
                'game',
                stage_path=self.next_stage_path,
                stage_index=self.stage_index + 1,
                game_mode=self.game_mode,
            )

        self.menu_btn.on_click = lambda: self.manager.switch('stage_select')

        super().on_show()

        # 次ステージがなければボタンを非表示
        if not next_stage_path:
            self.next_btn.enabled = False

        window.color = color.rgb(30, 30, 50)

    def _show_versus_result(self, elapsed_time):
        self.title.text = 'Versus Result'
        self.title.color = color.yellow
        self.mode_label.text = 'Mode: Versus'
        time_str = f'{elapsed_time:.1f}s'
        self.info_text.text = f'Time: {time_str}'

    def _show_solo_coop_result(self, cleared, elapsed_time, game_mode):
        if cleared:
            self.title.text = 'Clear!'
            self.title.color = color.yellow
        else:
            self.title.text = 'Game Over'
            self.title.color = color.red

        mode_names = {'solo': 'Solo', 'coop': 'Co-op'}
        mode_name = mode_names.get(game_mode, game_mode)
        self.mode_label.text = f'Mode: {mode_name}'
        time_str = f'{elapsed_time:.1f}s'
        self.info_text.text = f'Time: {time_str}'

    def input(self, key):
        if key == 'escape':
            self.manager.switch('stage_select')
