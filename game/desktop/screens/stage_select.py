"""
ステージ選択画面 — モード切替タブ＋ステージ一覧
"""

from ursina import Text, Button, color, window

from screens.base import Screen
from stage_builder import list_stages, load_stage


class StageSelectScreen(Screen):
    MODES = [
        ('solo', 'Solo'),
        ('coop', 'Co-op'),
        ('versus', 'Versus'),
    ]

    def __init__(self, manager, stages_dir):
        super().__init__(manager)
        self.stages_dir = stages_dir
        self.current_mode = 'solo'

        self._add(Text(
            text='Stage Select',
            position=(0, 0.4),
            origin=(0, 0),
            scale=2.5,
            color=color.white,
        ))

        # モードタブ
        self.mode_tabs = {}
        tab_positions = [-0.2, 0, 0.2]
        for i, (mode_key, mode_label) in enumerate(self.MODES):
            btn = self._add(Button(
                text=mode_label,
                scale=(0.18, 0.06),
                position=(tab_positions[i], 0.28),
                color=color.azure if mode_key == 'solo' else color.dark_gray,
            ))
            btn.on_click = lambda m=mode_key: self._select_mode(m)
            self.mode_tabs[mode_key] = btn

        # ステージ一覧
        self.stage_buttons = []
        stage_paths = list_stages(self.stages_dir)
        for i, path in enumerate(stage_paths):
            stage_data = load_stage(path)
            btn = self._add(Button(
                text=stage_data.name,
                scale=(0.4, 0.07),
                position=(0, 0.15 - i * 0.09),
                color=color.rgb(60, 60, 90),
            ))
            btn.on_click = lambda p=path, idx=i: self._start_stage(p, idx)
            self.stage_buttons.append(btn)

        # 戻るボタン
        back_btn = self._add(Button(
            text='Back',
            scale=(0.2, 0.06),
            position=(0, -0.4),
            color=color.gray,
        ))
        back_btn.on_click = lambda: self.manager.switch('start')

    def _select_mode(self, mode):
        self.current_mode = mode
        for key, btn in self.mode_tabs.items():
            btn.color = color.azure if key == mode else color.dark_gray

    def _start_stage(self, path, index):
        self.manager.switch(
            'game',
            stage_path=path,
            stage_index=index,
            game_mode=self.current_mode,
        )

    def on_show(self, **kwargs):
        super().on_show()
        window.color = color.rgb(30, 30, 50)

    def input(self, key):
        if key == 'escape':
            self.manager.switch('start')
