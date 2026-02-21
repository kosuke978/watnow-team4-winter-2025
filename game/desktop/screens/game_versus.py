"""
対戦ゲーム画面 — 2ボード並列、P1/P2それぞれスマホ操作（キーボードはフォールバック）
複数ボール対応: 各プレイヤーが複数ボールを同時操作し、全ゴールで先にクリアした方が勝ち
"""

import math
import random

from ursina import (
    Entity, Text, DirectionalLight, AmbientLight,
    Vec2, Vec3, color, camera, window, time, held_keys, Audio, destroy,
)
from ursina.prefabs.sky import Sky
from panda3d.core import TransparencyAttrib

from screens.base import Screen
from stage_builder import load_stage, build_stage, clear_stage, list_stages
from physics import BallPhysics
from results import ResultSessionManager, ResultApiError

_BALL_TEXTURES = [
    'assets/pinkE.png',
    'assets/purpleE.png',
    'assets/yellowE.png',
    'assets/greenE.png',
    'assets/grayE.png',
    'assets/blueE.png',
]


class VersusGameScreen(Screen):

    def __init__(self, manager, webrtc_client, stages_dir):
        super().__init__(manager)
        self.stages_dir = stages_dir
        self.webrtc = webrtc_client

    # --- モード名（右上） ---
        _red_color = color.hex('#FF090D')
        self._add(Text(
            text='対 戦',
            position=(0.58, 0.32),
            origin=(0.5, 0),
            font='assets/fonts/DotGothic16-Regular.ttf',
            scale=1.6,
            color=_red_color,
        ))
        # 下線
        self._add(Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.11, 0.003),
            position=(0.53, 0.295),
            color=_red_color,
        ))

        # 1p.png（ステージ番号の下・左側）
        self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='assets/1p',
            scale=(0.132, 0.08),
            position=(-0.52, 0.22),
        ))

        # 2p.png（モード名の下・右側）
        self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='assets/2p',
            scale=(0.14, 0.08),
            position=(0.52, 0.22),
        ))

        # ボード間隔
        self.board_offset = 7

        # 背景Sky（シャドウパイプラインの影響を受けない背景）
        self.sky = Sky(texture='sky_gold')

        # P1 ボード（左）
        self.p1_pivot = Entity(position=(-self.board_offset, 0, 0))

        # P2 ボード（右）
        self.p2_pivot = Entity(position=(self.board_offset, 0, 0))

        # ライト
        self.dir_light = DirectionalLight(
            y=2, z=3, shadows=True, rotation=(45, -45, 45),
        )
        self.amb_light = AmbientLight(color=color.rgba(100, 100, 100, 0.1))

        self._scene = [
            self.sky, self.p1_pivot, self.p2_pivot,
            self.dir_light, self.amb_light,
        ]

        # TVフレーム（camera.ui 上のオーバーレイ、中央は透過で3Dシーンが見える）
        self.tv_bg = Entity(
            parent=camera.ui,
            model='quad',
            texture='TVFrameGame',
            scale=(window.aspect_ratio, 1),
            z=1,
        )
        self.tv_bg.setTransparency(TransparencyAttrib.MAlpha)
        self._scene.append(self.tv_bg)

        # --- tokei 画像（上部中央） ---
        self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='assets/tokei',
            scale=(0.27, 0.10),
            position=(0, 0.30),
        ))

        # --- カウントダウンタイマー（tokei の上に重ねて表示） ---
        self.timer_text = self._add(Text(
            text='60',
            position=(0, 0.30),
            origin=(0, 0),
            font='assets/fonts/VT323-Regular.ttf',
            scale=3,
            color=color.black,
        ))


        self.stage_text = self._add(Text(
            text='',
            position=(0, 0.45),
            origin=(0, 0),
            scale=1.5,
            color=color.white,
        ))
        self.instruction_text = self._add(Text(
            text='P1: Arrows / P2: WASD / R: Reset / ESC: Back',
            position=(0, 0.38),
            origin=(0, 0),
            scale=0.8,
            color=color.light_gray,
        ))

        # P1/P2 ラベル（非表示）
        self.p1_label = Text(
            text='', enabled=False,
        )
        self.p2_label = Text(
            text='', enabled=False,
        )

        # スコア表示
        self.score_text = self._add(Text(
            text='0 - 0',
            position=(0, -0.42),
            origin=(0, 0),
            scale=1.2,
            color=color.black,
        ))

        # 勝利テキスト
        self.win_text = self._add(Text(
            text='',
            position=(0, 0),
            origin=(0, 0),
            scale=3,
            color=color.yellow,
        ))
        self.countdown_text = self._add(Text(
            text='',
            position=(0, 0.03),
            origin=(0, 0),
            font='assets/fonts/VT323-Regular.ttf',
            scale=8,
            color=color.white,
            enabled=False,
        ))

        # --- ステージ番号（左上） ---
        self.stage_num_text = self._add(Text(
            text='ステージ1',
            position=(-0.60, 0.32),
            origin=(-0.5, 0),
            font='assets/fonts/DotGothic16-Regular.ttf',
            scale=1.6,
            color=color.black,
        ))
        # 下線
        self._add(Entity(
            parent=camera.ui,
            model='quad',
            scale=(0.20, 0.003),
            position=(-0.50, 0.295),
            color=color.black,
        ))

        # ゲーム状態
        self.stage_data = None
        self.p1_stage_entities = {}
        self.p2_stage_entities = {}
        self.game_mode = 'versus'
        self.stage_index = 0
        self.stage_path = None

        self.p1_score = 0
        self.p2_score = 0

        # 複数ボール（各プレイヤー）
        self.p1_balls = []
        self.p1_ball_physics = []
        self.p1_ball_states = []      # 'playing' / 'goaled' / 'falling'
        self.p1_ball_fall_speeds = []
        self.p1_ball_starts = []

        self.p2_balls = []
        self.p2_ball_physics = []
        self.p2_ball_states = []
        self.p2_ball_fall_speeds = []
        self.p2_ball_starts = []

        # ラウンド終了後の遷移タイマー
        self.round_over = False
        self.round_timer = 0

        # 入力
        self.max_tilt = 12
        self.tilt_speed = 25
        self.motion_scale = 1.0
        self.p1_tilt = Vec2(0, 0)
        self.p2_tilt = Vec2(0, 0)

        self.elapsed_time = 0
        self.timer = 60.0
        self._countdown_active = False
        self._countdown_remaining = 0.0
        self._countdown_last_display = None
        self._countdown_go_timer = 0.0

        # 結果保存API連携
        self.result_session = ResultSessionManager()
        self.player_name = 'guest'

        # BGM
        self._bgm = Audio('assets/bgm/game-bgm.mp3', loop=True, autoplay=False)
        self._fall_se = Audio('assets/bgm/fall.mp3', loop=False, autoplay=False)
        self._fall_goal_se = Audio('assets/bgm/fall_goal.mp3', loop=False, autoplay=False)
        self._countdown_tick_se = Audio('assets/bgm/select.mp3', loop=False, autoplay=False)
        self._countdown_go_se = Audio('assets/bgm/game_start.mp3', loop=False, autoplay=False)
        self._timeup_se = Audio('assets/bgm/timeup.mp3', loop=False, autoplay=False)

    def on_show(self, stage_path=None, stage_index=0, game_mode='versus', **kwargs):
        super().on_show()
        for e in self._scene:
            e.enabled = True
        if hasattr(self.manager, 'start_bgm'):
            self.manager.start_bgm.stop()
        if not getattr(self.manager, 'bgm_muted', False):
            self._bgm.play()

        # カメラ: 俯瞰で両ボードが見える位置
        camera.position = (0, 34, -28)
        camera.rotation_x = 50

        self.game_mode = game_mode
        self.stage_index = stage_index
        self.p1_score = 0
        self.p2_score = 0
        self.player_name = kwargs.get('player_name', 'guest')

        if self.result_session.session_id is None:
            try:
                self.result_session.on_game_start(self.player_name)
            except ResultApiError as e:
                print(f'[result-api] start failed: {e}')

        # ゲーム開始時のみタイマーをリセット
        self.timer = 60.0
        self.timer_text.text = '60'

        if stage_path:
            self.stage_path = stage_path
            self._load_stage(stage_path)

    def on_hide(self):
        super().on_hide()
        for e in self._scene:
            e.enabled = False
        self._bgm.stop()
        self._fall_se.stop()
        self._fall_goal_se.stop()
        self._countdown_tick_se.stop()
        self._countdown_go_se.stop()
        self._timeup_se.stop()

    def _load_stage(self, path):
        if self.p1_stage_entities:
            clear_stage(self.p1_stage_entities)
        if self.p2_stage_entities:
            clear_stage(self.p2_stage_entities)

        # 既存ボールを破棄
        for b in self.p1_balls:
            destroy(b)
        for b in self.p2_balls:
            destroy(b)
        self.p1_balls.clear()
        self.p1_ball_physics.clear()
        self.p1_ball_states.clear()
        self.p1_ball_fall_speeds.clear()
        self.p1_ball_starts.clear()
        self.p2_balls.clear()
        self.p2_ball_physics.clear()
        self.p2_ball_states.clear()
        self.p2_ball_fall_speeds.clear()
        self.p2_ball_starts.clear()

        self.stage_data = load_stage(path)

        # P1/P2 ボード構築
        self.p1_stage_entities = build_stage(self.stage_data, self.p1_pivot)
        self.p2_stage_entities = build_stage(self.stage_data, self.p2_pivot)

        # 複数ボール生成（P1/P2 それぞれ同じレイアウト）
        textures = random.sample(
            _BALL_TEXTURES,
            min(len(self.stage_data.ball_starts), len(_BALL_TEXTURES)),
        )
        for i, bs in enumerate(self.stage_data.ball_starts):
            tex = textures[i % len(textures)]
            # P1
            p1_ball = Entity(
                parent=self.p1_pivot, model='sphere',
                color=color.white, scale=bs.radius * 2, texture=tex,
            )
            self.p1_balls.append(p1_ball)
            self.p1_ball_physics.append(BallPhysics(self.stage_data))
            self.p1_ball_states.append('playing')
            self.p1_ball_fall_speeds.append(0)
            self.p1_ball_starts.append(bs.start)
            # P2
            p2_ball = Entity(
                parent=self.p2_pivot, model='sphere',
                color=color.white, scale=bs.radius * 2, texture=tex,
            )
            self.p2_balls.append(p2_ball)
            self.p2_ball_physics.append(BallPhysics(self.stage_data))
            self.p2_ball_states.append('playing')
            self.p2_ball_fall_speeds.append(0)
            self.p2_ball_starts.append(bs.start)

        self.stage_text.text = self.stage_data.name
        self.stage_num_text.text = f'ステージ{self.stage_index + 1}'

        self._reset_round()
        self._start_countdown()

    def _reset_player_balls(self, balls, physics_list, states, fall_speeds, starts):
        """指定プレイヤーの全ボールを初期位置にリセット"""
        for i, ball in enumerate(balls):
            sx, sz = starts[i]
            ball.position = Vec3(
                sx,
                self.stage_data.board_thickness / 2 + self.stage_data.ball_starts[i].radius,
                sz,
            )
            ball.rotation = Vec3(0, 0, 0)
            ball.visible = True
            physics_list[i].reset()
            states[i] = 'playing'
            fall_speeds[i] = 0

    def _reset_round(self):
        self._reset_player_balls(
            self.p1_balls, self.p1_ball_physics,
            self.p1_ball_states, self.p1_ball_fall_speeds, self.p1_ball_starts,
        )
        self._reset_player_balls(
            self.p2_balls, self.p2_ball_physics,
            self.p2_ball_states, self.p2_ball_fall_speeds, self.p2_ball_starts,
        )
        self.p1_pivot.rotation = Vec3(0, 0, 0)
        self.p2_pivot.rotation = Vec3(0, 0, 0)
        self.p1_tilt = Vec2(0, 0)
        self.p2_tilt = Vec2(0, 0)
        self.round_over = False
        self.round_timer = 0
        self.elapsed_time = 0
        self.win_text.text = ''
        self._update_score_display()

    def _update_score_display(self):
        self.score_text.text = f'{self.p1_score} - {self.p2_score}'

    def _go_to_result(self):
        stage_paths = list_stages(self.stages_dir)
        next_index = self.stage_index + 1
        has_next = next_index < len(stage_paths)

        # 次のステージがあれば自動で進む（スコアは引き継ぐ）
        if has_next:
            next_path = stage_paths[next_index]
            self.stage_index = next_index
            self.stage_path = next_path
            self._load_stage(next_path)
            return

        # 最終ステージ終了 → リザルト画面へ
        try:
            self.result_session.on_game_finish()
        except ResultApiError as e:
            print(f'[result-api] finish failed: {e}')

        self.manager.switch(
            'result',
            game_mode='versus',
            cleared=True,
            stage_index=self.stage_index,
            stage_path=self.stage_path,
            next_stage_path=None,
            elapsed_time=self.elapsed_time,
            p1_score=self.p1_score,
            p2_score=self.p2_score,
        )

    # ------------------------------------------------------------------
    # 入力
    # ------------------------------------------------------------------

    def _update_p1_input(self, dt):
        """P1: スマホ(player_id=1) or キーボード（フォールバック）"""
        sensor = self.webrtc.get_latest_sensor_data(player_id=1)
        if sensor is not None:
            self.p1_tilt.x = max(-self.max_tilt, min(
                self.max_tilt, math.degrees(sensor.roll) * self.motion_scale))
            self.p1_tilt.y = max(-self.max_tilt, min(
                self.max_tilt, math.degrees(-sensor.pitch) * self.motion_scale))
        else:
            # キーボードフォールバック
            if held_keys['left arrow']:
                self.p1_tilt.x = max(self.p1_tilt.x - self.tilt_speed * dt, -self.max_tilt)
            if held_keys['right arrow']:
                self.p1_tilt.x = min(self.p1_tilt.x + self.tilt_speed * dt, self.max_tilt)
            if held_keys['up arrow']:
                self.p1_tilt.y = min(self.p1_tilt.y + self.tilt_speed * dt, self.max_tilt)
            if held_keys['down arrow']:
                self.p1_tilt.y = max(self.p1_tilt.y - self.tilt_speed * dt, -self.max_tilt)

            keyboard_active = (
                held_keys['left arrow'] or held_keys['right arrow'] or
                held_keys['up arrow'] or held_keys['down arrow']
            )
            if not keyboard_active:
                self.p1_tilt.x *= 0.92
                self.p1_tilt.y *= 0.92

    def _update_p2_input(self, dt):
        """P2: スマホ(player_id=2) or WASD（フォールバック）"""
        sensor = self.webrtc.get_latest_sensor_data(player_id=2)
        if sensor is not None:
            self.p2_tilt.x = max(-self.max_tilt, min(
                self.max_tilt, math.degrees(sensor.roll) * self.motion_scale))
            self.p2_tilt.y = max(-self.max_tilt, min(
                self.max_tilt, math.degrees(-sensor.pitch) * self.motion_scale))
        else:
            # WASDフォールバック
            if held_keys['a']:
                self.p2_tilt.x = max(self.p2_tilt.x - self.tilt_speed * dt, -self.max_tilt)
            if held_keys['d']:
                self.p2_tilt.x = min(self.p2_tilt.x + self.tilt_speed * dt, self.max_tilt)
            if held_keys['w']:
                self.p2_tilt.y = min(self.p2_tilt.y + self.tilt_speed * dt, self.max_tilt)
            if held_keys['s']:
                self.p2_tilt.y = max(self.p2_tilt.y - self.tilt_speed * dt, -self.max_tilt)

            wasd_active = (
                held_keys['a'] or held_keys['d'] or
                held_keys['w'] or held_keys['s']
            )
            if not wasd_active:
                self.p2_tilt.x *= 0.92
                self.p2_tilt.y *= 0.92

    def _update_labels(self):
        p1_phone = self.webrtc.get_latest_sensor_data(player_id=1) is not None
        p2_phone = self.webrtc.get_latest_sensor_data(player_id=2) is not None
        self.p1_label.text = 'P1: Phone' if p1_phone else 'P1: Keyboard'
        self.p2_label.text = 'P2: Phone' if p2_phone else 'P2: WASD'

    def _start_countdown(self, seconds=3):
        self._countdown_active = True
        self._countdown_remaining = float(seconds)
        self._countdown_last_display = None
        self._countdown_go_timer = 0.0
        self.countdown_text.enabled = True
        self.countdown_text.text = ''

    def _update_countdown(self, dt) -> bool:
        if not self._countdown_active:
            return False

        if self._countdown_go_timer > 0:
            self._countdown_go_timer -= dt
            if self._countdown_go_timer <= 0:
                self.countdown_text.enabled = False
                self._countdown_active = False
            return True

        current = max(1, int(math.ceil(self._countdown_remaining)))
        if current != self._countdown_last_display:
            self._countdown_last_display = current
            self.countdown_text.text = str(current)
            if not getattr(self.manager, 'bgm_muted', False):
                self._countdown_tick_se.stop()
                self._countdown_tick_se.play()

        self._countdown_remaining -= dt
        if self._countdown_remaining <= 0:
            self.countdown_text.text = 'GO!'
            self._countdown_go_timer = 0.5
            if not getattr(self.manager, 'bgm_muted', False):
                self._countdown_go_se.stop()
                self._countdown_go_se.play()

        return True

    # ------------------------------------------------------------------
    # メインループ
    # ------------------------------------------------------------------

    def _update_player_balls(self, balls, physics_list, states, fall_speeds, starts, tilt, dt):
        """1プレイヤー分のボール更新。全ゴールしたら True を返す"""
        for i, ball in enumerate(balls):
            state = states[i]

            if state == 'playing':
                result = physics_list[i].update(ball, tilt, dt)
                if result == 'goal':
                    if not getattr(self.manager, 'bgm_muted', False):
                        self._fall_goal_se.stop()
                        self._fall_goal_se.play()
                    states[i] = 'goaled'
                    fall_speeds[i] = 0
                elif result == 'fell':
                    if not getattr(self.manager, 'bgm_muted', False):
                        self._fall_se.stop()
                        self._fall_se.play()
                    states[i] = 'falling'
                    fall_speeds[i] = 0

            elif state == 'falling':
                fall_speeds[i] += 15 * dt
                ball.y -= fall_speeds[i] * dt
                if ball.y < -5:
                    sx, sz = starts[i]
                    ball.position = Vec3(
                        sx,
                        self.stage_data.board_thickness / 2 + self.stage_data.ball_starts[i].radius,
                        sz,
                    )
                    ball.rotation = Vec3(0, 0, 0)
                    physics_list[i].reset()
                    states[i] = 'playing'
                    fall_speeds[i] = 0

            elif state == 'goaled':
                fall_speeds[i] += 5 * dt
                ball.y -= fall_speeds[i] * dt

        # playing ボール同士の衝突判定
        playing_indices = [i for i, s in enumerate(states) if s == 'playing']
        for a in range(len(playing_indices)):
            for b in range(a + 1, len(playing_indices)):
                ia, ib = playing_indices[a], playing_indices[b]
                BallPhysics.collide_balls(
                    balls[ia], balls[ib],
                    physics_list[ia], physics_list[ib],
                )

        return (all(s == 'goaled' for s in states)
                and all(b.y < 0 for b in balls))

    def update(self):
        if not self.p1_balls:
            return
        dt = time.dt

        # ラウンド終了後 → リザルト画面へ
        if self.round_over:
            self.round_timer += dt
            if self.round_timer > 1.5:
                self._go_to_result()
            return
        if self._update_countdown(dt):
            return

        self.elapsed_time += dt

        # カウントダウンタイマー（60秒で対戦）
        self.timer -= dt
        if self.timer <= 0:
            self.timer = 0
            self.timer_text.text = '0'
            if not getattr(self.manager, 'bgm_muted', False):
                self._timeup_se.stop()
                self._timeup_se.play()
            self.manager.switch(
                'result',
                game_mode='versus',
                cleared=False,
                stage_index=self.stage_index,
                stage_path=self.stage_path,
                next_stage_path=None,
                elapsed_time=self.elapsed_time,
                p1_score=self.p1_score,
                p2_score=self.p2_score,
            )
            return
        self.timer_text.text = str(int(self.timer) + 1)

        # 入力更新
        self._update_p1_input(dt)
        self._update_p2_input(dt)
        self._update_labels()

        # P1 ボード傾き
        self.p1_pivot.rotation_z = self.p1_tilt.x
        self.p1_pivot.rotation_x = self.p1_tilt.y

        # P2 ボード傾き
        self.p2_pivot.rotation_z = self.p2_tilt.x
        self.p2_pivot.rotation_x = self.p2_tilt.y

        # P1 ボール更新
        p1_all_goaled = self._update_player_balls(
            self.p1_balls, self.p1_ball_physics,
            self.p1_ball_states, self.p1_ball_fall_speeds,
            self.p1_ball_starts, self.p1_tilt, dt,
        )

        # P2 ボール更新
        p2_all_goaled = self._update_player_balls(
            self.p2_balls, self.p2_ball_physics,
            self.p2_ball_states, self.p2_ball_fall_speeds,
            self.p2_ball_starts, self.p2_tilt, dt,
        )

        # 先に全ゴールした方が勝ち
        if p1_all_goaled and not self.round_over:
            if not getattr(self.manager, 'bgm_muted', False):
                self._fall_goal_se.stop()
                self._fall_goal_se.play()
            try:
                self.result_session.on_stage_cleared()
            except ResultApiError as e:
                print(f'[result-api] stage-clear failed: {e}')
            self.p1_score += 1
            self._update_score_display()
            self.win_text.text = 'P1 Win!'
            self.round_over = True
            self.round_timer = 0
        elif p2_all_goaled and not self.round_over:
            if not getattr(self.manager, 'bgm_muted', False):
                self._fall_goal_se.stop()
                self._fall_goal_se.play()
            try:
                self.result_session.on_stage_cleared()
            except ResultApiError as e:
                print(f'[result-api] stage-clear failed: {e}')
            self.p2_score += 1
            self._update_score_display()
            self.win_text.text = 'P2 Win!'
            self.round_over = True
            self.round_timer = 0

    def input(self, key):
        if key == 'r':
            self._reset_round()
        elif key == 'escape':
            self.result_session.on_game_abort()
            self.manager.switch('start')
