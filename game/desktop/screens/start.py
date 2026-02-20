"""
スタート画面 — タイトルとメニュー
"""

from ursina import Entity, camera, color, application, window

from screens.base import Screen


class StartScreen(Screen):
    def __init__(self, manager):
        super().__init__(manager)

        # --- TVFrame 背景（画面全体を覆う） ---
        self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='TVFrame',
            scale=(window.aspect_ratio, 1),
            z=0.5,
        ))

        # --- タイトル画像 ---
        self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='title',            # assets/title.png  1195x804px
            scale=(0.48, 0.32),
            position=(0, 0.15),
        ))

        # --- ボタン（横並び・Entity） ---
        # aloneB: 249x55px → w=0.32, battleB/teamB: 144x56px → w=0.18
        # 均一ギャップ g=0.05 で中央揃え配置
        #   total = 0.32+0.18+0.18 + 0.05*2 = 0.78
        #   x_left = -0.78/2 = -0.39
        #   aloneB  center = -0.39 + 0.32/2       = -0.23
        #   battleB center = -0.23 + 0.32/2 + 0.05 + 0.18/2 = 0.07
        #   teamB   center =  0.07 + 0.18/2 + 0.05 + 0.18/2 = 0.30
        btn_y = -0.07
        alone = self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='aloneB',
            scale=(0.32, 0.07),
            position=(-0.23, btn_y),
            collider='box',
        ))
        alone.on_click = lambda: manager.switch('game')

        battle = self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='battleB',
            scale=(0.18, 0.07),
            position=(0.05, btn_y),
            collider='box',
        ))
        battle.on_click = lambda: manager.switch('game')

        team = self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='teamB',
            scale=(0.18, 0.07),
            position=(0.30, btn_y),
            collider='box',
        ))
        team.on_click = lambda: manager.switch('game')

        # --- howB 画像（ボタン群の下） ---
        howB = self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='howB',             # assets/howB.png  135x41px → 比率 ≈ 3.29
            scale=(0.20, 0.06),
            position=(0, btn_y - 0.1),  # btn_y(-0.1) より下 → -0.2
        ))
        howB.on_click = lambda: manager.switch('how_to_play')


        # --- woman（左）・ufo（右） ---
        self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='woman',            # assets/woman.png  150x150px → 正方形
            scale=(0.18, 0.18),
            position=(-0.50, 0.01),
        ))

        self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='ufo',              # assets/ufo.png  120x100px → 比率 1.2:1
            scale=(0.18, 0.15),
            position=(0.50, -0.01),
        ))

    def on_show(self, **kwargs):
        super().on_show()
        window.color = color.rgb(30, 30, 50)

    def input(self, key):
        if key == 'escape':
            application.quit()
