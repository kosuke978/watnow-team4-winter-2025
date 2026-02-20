"""
使い方画面 — 操作説明（レトロTVコンソール風UI）
背景画像: assets/ui/tv_frame.png
"""

from ursina import Entity, Text, Button, color, window, camera

from screens.base import Screen

# 背景画像のアスペクト比（1280x832）
_IMG_AR = 1280 / 832


def _panel(col, scale, pos, rot=0, model='quad'):
    """非インタラクティブな色付きパネル"""
    return Button(
        model=model,
        scale=scale,
        position=pos,
        rotation_z=rot,
        color=col,
        highlight_color=col,
        pressed_color=col,
    )


class HowToPlayScreen(Screen):
    def __init__(self, manager):
        super().__init__(manager)

        # ─── TVフレーム背景画像 ───
        self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='assets/ui/tv_frame',
            scale=(_IMG_AR, 1),
            z=1,
        ))

        # ═══════════════════════════════════════
        # テキスト
        # ═══════════════════════════════════════

        # タイトル「使い方」+ ?アイコン
        self._add(Text(
            text='使い方',
            position=(-0.53, 0.32),
            origin=(-0.5, 0),
            scale=2.2,
            font='assets/fonts/DotGothic16-Regular.ttf',
            color=color.black,
        ))
        self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='assets/ui/question_mark',
            scale=(0.04, 0.04),
            position=(-0.34, 0.325),
        ))

        # 説明文
        self._add(Text(
            text=(
                'スマートフォンを傾けると、画面内の台も同じように傾き、ボールが転がります。\n'
                '傾き方をうまく調整して、ボールを穴へ導きましょう。'
            ),
            position=(-0.53, 0.22),
            origin=(-0.5, 0),
            scale=1.1,
            font='assets/fonts/DotGothic16-Regular.ttf',
            color=color.black,
        ))

        # ═══════════════════════════════════════
        # 左側：傾いたボード（画面上のステージ）
        # ═══════════════════════════════════════

        # 傾いた板（黒い斜め板）
        self._add(_panel(
            color.black, (0.48, 0.025),
            (-0.25, 0.0), rot=18,
        ))

        # ゴーストキャラ（ボード上）
        self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='assets/ui/ghost',
            scale=(0.07, 0.07),
            position=(-0.33, 0.07),
        ))

        # 矢印（左側）
        self._add(Text(
            text='\u2191', position=(-0.06, 0.07),
            origin=(0, 0), scale=2.0,
            color=color.rgb(50, 50, 50),
        ))
        self._add(Text(
            text='\u2193', position=(-0.44, -0.09),
            origin=(0, 0), scale=2.0,
            color=color.rgb(50, 50, 50),
        ))

        # ラベル「画面上のステージ」
        self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='assets/ui/label_stage',
            scale=(0.34, 0.085),
            position=(-0.25, -0.22),
        ))

        # ═══════════════════════════════════════
        # 右側：スマートフォン
        # ═══════════════════════════════════════

        # スマートフォン（ゴースト込みの1枚画像）
        self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='assets/ui/smartphone',
            scale=(0.12, 0.42),
            position=(0.35, 0.0),
            rotation_z=-65,
        ))

        # 矢印（右側）
        self._add(Text(
            text='\u2193', position=(0.16, -0.09),
            origin=(0, 0), scale=2.0,
            color=color.rgb(50, 50, 50),
        ))
        self._add(Text(
            text='\u2191', position=(0.54, 0.07),
            origin=(0, 0), scale=2.0,
            color=color.rgb(50, 50, 50),
        ))

        # ラベル「スマートフォン」
        self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='assets/ui/label_phone',
            scale=(0.30, 0.085),
            position=(0.38, -0.22),
        ))

    def on_show(self, **kwargs):
        super().on_show()
        window.color = color.rgb(132, 16, 16)

    def input(self, key):
        if key == 'escape':
            self.manager.switch('start')
