"""
結果画面 — 対戦 / 協力・一人で の2バリエーション
"""

from ursina import Entity, Text, Button, color, window, camera, Audio, invoke

from screens.base import Screen


class ResultScreen(Screen):
    def __init__(self, manager):
        super().__init__(manager)
        self._versus = []
        self._solo = []

        # ========================================
        # 対戦モード — 背景画像 + テキストオーバーレイ
        # ========================================

        self._vs_bg = self._add_vs(Entity(
            model='quad',
            texture='assets/ui/result_versus_bg.png',
            parent=camera.ui,
            z=1,
        ))

        self._p1_score = self._add_vs(Text(
            text='0',
            position=(-0.2, -0.08),
            origin=(0, 0),
            scale=3,
            color=color.rgb(30, 30, 30),
        ))

        self._p2_score = self._add_vs(Text(
            text='0',
            position=(0.33, -0.08),
            origin=(0, 0),
            scale=3,
            color=color.rgb(30, 30, 30),
        ))

        # win / lose バッジ（スコアに応じてテクスチャを切替）
        self._vs_left_badge = self._add_vs(Entity(
            model='quad',
            parent=camera.ui,
            scale=(0.20, 0.12),
            position=(-0.25, 0.12),
        ))
        self._vs_right_badge = self._add_vs(Entity(
            model='quad',
            parent=camera.ui,
            scale=(0.20, 0.12),
            position=(0.30, 0.12),
        ))
        self._vs_draw_badge = self._add_vs(Entity(
            model='quad',
            texture='assets/draw',
            parent=camera.ui,
            scale=(0.47, 0.12),
            position=(0, 0.12),
        ))

        self._vs_retry = self._add_vs(Button(
            text='もう一回',
            scale=(0.18, 0.045),
            position=(-0.13, -0.22),
            color=color.rgb(160, 130, 60),
            highlight_color=color.rgb(190, 160, 80),
            text_color=color.black,
        ))
        self._vs_end = self._add_vs(Button(
            text='おわる',
            scale=(0.18, 0.045),
            position=(0.13, -0.22),
            color=color.rgb(160, 130, 60),
            highlight_color=color.rgb(190, 160, 80),
            text_color=color.black,
        ))

        # ========================================
        # ソロ / 協力モード — 背景画像 + テキストオーバーレイ
        # ========================================

        self._solo_bg = self._add_solo(Entity(
            model='quad',
            texture='assets/ui/result_solo_bg.png',
            parent=camera.ui,
            z=1,
        ))

        # ステージ番号（「ステージ」の右側に表示）
        self._solo_stage_num = self._add_solo(Text(
            text='1',
            position=(0.1, -0.12),
            origin=(0, 0),
            scale=3,
            color=color.black,
        ))

        # ▷もう一回（テキストボタン・背景透明）
        self._solo_retry = self._add_solo(Button(
            text='▷もう一回',
            scale=(0.2, 0.05),
            position=(-0.18, -0.24),
            color=color.clear,
            highlight_color=color.rgba(255, 255, 255, 30),
            text_color=color.black,
        ))

        # ▷おわる（テキストボタン・背景透明）
        self._solo_end = self._add_solo(Button(
            text='▷おわる',
            scale=(0.2, 0.05),
            position=(0.18, -0.24),
            color=color.clear,
            highlight_color=color.rgba(255, 255, 255, 30),
            text_color=color.black,
        ))

        # BGM
        self._bgm = Audio('assets/bgm/result-bgm.mp3', loop=True, autoplay=False)
        self._select_se = Audio('assets/bgm/selrct.mp3', loop=False, autoplay=False)
        self._click_switch_delay = 0.06

        # 状態
        self.game_mode = 'solo'
        self.stage_path = None
        self.stage_index = 0
        self.next_stage_path = None

    def _add_vs(self, entity):
        self._versus.append(entity)
        return self._add(entity)

    def _add_solo(self, entity):
        self._solo.append(entity)
        return self._add(entity)

    def _switch_with_select_se(self, name, **kwargs):
        if not getattr(self.manager, 'bgm_muted', False):
            if self._select_se.playing:
                self._select_se.stop()
            self._select_se.play()
            invoke(self.manager.switch, name, delay=self._click_switch_delay, **kwargs)
            return
        self.manager.switch(name, **kwargs)

    def on_show(self, game_mode='solo', cleared=True, stage_index=0,
                stage_path=None, next_stage_path=None, elapsed_time=0,
                p1_score=0, p2_score=0, **kwargs):
        self.game_mode = game_mode
        self.stage_path = stage_path
        self.stage_index = stage_index
        self.next_stage_path = next_stage_path

        super().on_show()
        if not getattr(self.manager, 'bgm_muted', False):
            self._bgm.play()

        if game_mode == 'versus':
            for e in self._solo:
                e.enabled = False
            self._show_versus(p1_score, p2_score)
        else:
            for e in self._versus:
                e.enabled = False
            self._show_solo_coop(cleared, elapsed_time, game_mode)

    def _show_versus(self, p1_score, p2_score):
        self._vs_bg.scale = (window.aspect_ratio, 1)

        self._p1_score.text = str(p1_score)
        self._p2_score.text = str(p2_score)

        # win / lose バッジ配置
        # win.png: 261x160px → scale (0.20, 0.12)
        # lose.png: 247x117px → scale (0.25, 0.12)
        if p1_score > p2_score:
            self._vs_left_badge.texture  = 'assets/win'
            self._vs_left_badge.scale    = (0.25, 0.15)
            self._vs_right_badge.texture = 'assets/lose'
            self._vs_right_badge.scale   = (0.25, 0.12)
            self._vs_left_badge.enabled  = True
            self._vs_right_badge.enabled = True
        elif p2_score > p1_score:
            self._vs_left_badge.texture  = 'assets/lose'
            self._vs_left_badge.scale    = (0.25, 0.12)
            self._vs_right_badge.texture = 'assets/win'
            self._vs_right_badge.scale   = (0.25, 0.15)
            self._vs_left_badge.enabled  = True
            self._vs_right_badge.enabled = True
        else:
            # 引き分け: 中央に draw.png を表示
            self._vs_left_badge.enabled  = False
            self._vs_right_badge.enabled = False
            self._vs_draw_badge.enabled  = True
            return

        self._vs_draw_badge.enabled = False

        if self.stage_path:
            self._vs_retry.on_click = lambda: self._switch_with_select_se(
                'game_versus', stage_path=self.stage_path,
                stage_index=self.stage_index, game_mode='versus',
            )
        else:
            self._vs_retry.on_click = lambda: self._switch_with_select_se('start')
        self._vs_end.on_click = lambda: self._switch_with_select_se('start')

    def _show_solo_coop(self, cleared, elapsed_time, game_mode):
        self._solo_bg.scale = (window.aspect_ratio, 1)

        # cleared=True: 最終クリアステージ番号（+1）
        # cleared=False: タイムアップ時はクリアできたステージ数をそのまま
        self._solo_stage_num.text = str(self.stage_index + 1 if cleared else self.stage_index)

        if self.stage_path:
            self._solo_retry.on_click = lambda: self._switch_with_select_se(
                f'game_{self.game_mode}', stage_path=self.stage_path,
                stage_index=self.stage_index, game_mode=self.game_mode,
            )
        else:
            self._solo_retry.on_click = lambda: self._switch_with_select_se('start')
        self._solo_end.on_click = lambda: self._switch_with_select_se('start')

    def on_hide(self):
        super().on_hide()
        self._bgm.stop()

    def input(self, key):
        if key == 'escape':
            self.manager.switch('start')
