"""
スタート画面 — タイトルとメニュー
"""

import os
import math

from ursina import Entity, Text, camera, color, application, window, Audio, invoke, time

from screens.base import Screen
from stage_builder import list_stages

STAGES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'stages')


class StartScreen(Screen):
    def __init__(self, manager, webrtc_client=None):
        super().__init__(manager)
        self._stage_paths = list_stages(STAGES_DIR)
        self.webrtc = webrtc_client
        self._click_switch_delay = 0.06
        self._game_start_se = Audio(
            'assets/bgm/gamestart.mp3',
            loop=False,
            autoplay=False,
        )
        self._select_se = Audio(
            'assets/bgm/selrct.mp3',
            loop=False,
            autoplay=False,
        )

        def _start_game(screen_name, game_mode):
            if not manager.bgm_muted:
                if self._game_start_se.playing:
                    self._game_start_se.stop()
                self._game_start_se.play()
                invoke(
                    manager.switch,
                    screen_name,
                    stage_path=self._stage_paths[0],
                    stage_index=0,
                    game_mode=game_mode,
                    delay=self._click_switch_delay,
                )
                return
            manager.switch(
                screen_name,
                stage_path=self._stage_paths[0],
                stage_index=0,
                game_mode=game_mode,
            )

        def _open_how_to_play():
            if not manager.bgm_muted:
                if self._select_se.playing:
                    self._select_se.stop()
                self._select_se.play()
                invoke(manager.switch, 'how_to_play', delay=self._click_switch_delay)
                return
            manager.switch('how_to_play')

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
        alone.on_click = lambda: _start_game('game_solo', 'solo')

        battle = self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='battleB',
            scale=(0.18, 0.07),
            position=(0.05, btn_y),
            collider='box',
        ))
        battle.on_click = lambda: _start_game('game_versus', 'versus')

        team = self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='teamB',
            scale=(0.18, 0.07),
            position=(0.30, btn_y),
            collider='box',
        ))
        team.on_click = lambda: _start_game('game_coop', 'coop')

        # --- howB 画像（ボタン群の下） ---
        howB = self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='howB',             # assets/howB.png  135x41px → 比率 ≈ 3.29
            scale=(0.20, 0.06),
            position=(0.2, btn_y - 0.1),  # btn_y(-0.1) より下 → -0.2
            collider='box',
        ))
        howB.on_click = _open_how_to_play

        # --- ranking 画像（howB と同サイズ・左右対称位置） ---
        self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='assets/ui/ranking.png',
            scale=(0.15, 0.045),
            position=(-0.2, btn_y - 0.106), # btn_y(-0.1) より下 → -0.2
        ))


        # --- woman（左）・ufo（右） ---
        self._woman = self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='woman',            # assets/woman.png  150x150px → 正方形
            scale=(0.18, 0.18),
            position=(-0.50, 0.01),
        ))
        self._woman_base_y = 0.01

        self._ufo = self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='ufo',              # assets/ufo.png  120x100px → 比率 1.2:1
            scale=(0.18, 0.15),
            position=(0.50, -0.01),
        ))
        self._ufo_base_y = -0.01

        # --- P1/P2 接続ステータス ---
        _status_font = 'assets/fonts/DotGothic16-Regular.ttf'
        self.p1_status = self._add(Text(
            text='P1: ---',
            position=(-0.55, -0.30),
            origin=(-0.5, 0),
            scale=0.9,
            color=color.light_gray,
            font=_status_font,
        ))
        self.p2_status = self._add(Text(
            text='P2: ---',
            position=(0.55, -0.30),
            origin=(0.5, 0),
            scale=0.9,
            color=color.light_gray,
            font=_status_font,
        ))

        # --- BGM（manager経由でhow_to_playと共有） ---
        manager.bgm_muted = False
        manager.start_bgm = Audio(
            'assets/bgm/start-bgm.mp3',
            loop=True,
            autoplay=False,
        )

        # --- bgmB（右上）: クリックで全画面BGM ON/OFF切替 ---
        self._bgm_btn = self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='assets/bgmB',
            scale=(0.10, 0.10),
            position=(0.54, 0.30),
            collider='box',
        ))
        def _toggle_bgm():
            manager.bgm_muted = not manager.bgm_muted
            if manager.bgm_muted:
                self._bgm_btn.texture = 'assets/bgmB-delete'
                manager.start_bgm.stop()
            else:
                self._bgm_btn.texture = 'assets/bgmB'
                manager.start_bgm.play()
        self._bgm_btn.on_click = _toggle_bgm

    def on_show(self, **kwargs):
        super().on_show()
        window.color = color.rgb(30, 30, 50)
        # ミュート状態を反映してボタン画像を同期
        self._bgm_btn.texture = 'assets/bgmB-delete' if self.manager.bgm_muted else 'assets/bgmB'
        if not self.manager.bgm_muted:
            self.manager.start_bgm.play()

    def on_hide(self):
        super().on_hide()

    def update(self):
        if self._woman:
            self._woman.y = self._woman_base_y + math.sin(time.time() * 6.8) * 0.008
        if self._ufo:
            self._ufo.y = self._ufo_base_y + math.sin(time.time() * 6.8) * 0.008

        if not self.webrtc:
            return
        p1 = self.webrtc.get_latest_sensor_data(player_id=1) is not None
        p2 = self.webrtc.get_latest_sensor_data(player_id=2) is not None
        p1_name = self.webrtc.get_player_name(1)
        p2_name = self.webrtc.get_player_name(2)
        self.p1_status.text = f'P1({p1_name}): Connected' if p1 else 'P1: ---'
        self.p1_status.color = color.lime if p1 else color.light_gray
        self.p2_status.text = f'P2({p2_name}): Connected' if p2 else 'P2: ---'
        self.p2_status.color = color.lime if p2 else color.light_gray

    def input(self, key):
        if key == 'escape':
            application.quit()
