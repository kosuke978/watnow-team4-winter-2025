"""
ゲーム画面ベースクラス — ソロ/協力/対戦の共通ロジック
"""

import math
import random

from ursina import (
    Entity, Text, DirectionalLight, AmbientLight,
    Vec2, Vec3, color, camera, window, time, Audio,
)

_BALL_TEXTURES = [
    'assets/pinkE.png',
    'assets/purpleE.png',
    'assets/yellowE.png',
    'assets/greenE.png',
    'assets/grayE.png',
    'assets/blueE.png',
]
from ursina.prefabs.sky import Sky
from panda3d.core import TransparencyAttrib

from screens.base import Screen
from stage_builder import load_stage, build_stage, clear_stage, list_stages
from physics import BallPhysics
from results import ResultSessionManager, ResultApiError


class GameScreenBase(Screen):
    """単一ボードのゲーム画面ベースクラス。

    サブクラスは以下をオーバーライドする:
    - _create_input()    : 入力の初期化
    - _get_board_tilt(dt) : 入力から Vec2 tilt を返す
    - _setup_camera()    : カメラ配置
    - _on_reset()        : モード固有のリセット処理
    """

    def __init__(self, manager, webrtc_client, stages_dir):
        super().__init__(manager)
        self.stages_dir = stages_dir
        self.webrtc = webrtc_client

        # 3Dシーン
        self.sky = Sky(texture='sky_gold')
        self.board_pivot = Entity(position=(0, 0, 0))
        self.dir_light = DirectionalLight(
            y=2, z=3, shadows=True, rotation=(45, -45, 45),
        )
        self.amb_light = AmbientLight(color=color.rgba(100, 100, 100, 0.1))
        self._scene = [self.sky, self.board_pivot, self.dir_light, self.amb_light]

        # 複数ボール
        self.balls = []
        self.ball_physics = []
        self.ball_states = []       # 'playing' / 'goaled' / 'falling'
        self.ball_fall_speeds = []
        self.ball_starts = []

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

        # ゲーム状態
        self.stage_data = None
        self.stage_entities = {}
        self.game_mode = 'solo'
        self.stage_index = 0
        self.stage_path = None
        self.game_won = False
        self.elapsed_time = 0
        self.win_timer = 0
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

        # サブクラスで入力を初期化
        self._create_input()

    # ------------------------------------------------------------------
    # サブクラスがオーバーライドするメソッド
    # ------------------------------------------------------------------

    def _create_input(self):
        """入力ハンドラーの初期化。サブクラスで実装する。"""
        pass

    def _get_board_tilt(self, dt) -> Vec2:
        """フレームごとのボード傾きを返す。サブクラスで実装する。"""
        return Vec2(0, 0)

    def _setup_camera(self):
        """カメラ配置。サブクラスでオーバーライド可。"""
        camera.position = (0, 22, -19)
        camera.rotation_x = 50

    def _on_reset(self):
        """モード固有のリセット処理。サブクラスでオーバーライド可。"""
        pass

    def _update_status(self):
        """ステータス表示の更新。サブクラスでオーバーライド可。"""
        pass

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

        # "GO!" 表示中
        if self._countdown_go_timer > 0:
            self._countdown_go_timer -= dt
            if self._countdown_go_timer <= 0:
                self.countdown_text.enabled = False
                self._countdown_active = False
            return True

        # 3,2,1 表示
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
    # 画面ライフサイクル
    # ------------------------------------------------------------------

    def on_show(self, stage_path=None, stage_index=0, game_mode='solo', **kwargs):
        super().on_show()
        for e in self._scene:
            e.enabled = True
        if hasattr(self.manager, 'start_bgm'):
            self.manager.start_bgm.stop()
        if not getattr(self.manager, 'bgm_muted', False):
            self._bgm.play()

        self._setup_camera()

        self.game_mode = game_mode
        self.stage_index = stage_index
        self.player_name = kwargs.get('player_name', 'guest')

        # セッション未開始なら開始
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

    # ------------------------------------------------------------------
    # ステージ管理
    # ------------------------------------------------------------------

    def _load_stage(self, path):
        if self.stage_entities:
            clear_stage(self.stage_entities)

        # 既存ボールを破棄
        from ursina import destroy
        for b in self.balls:
            destroy(b)
        self.balls.clear()
        self.ball_physics.clear()
        self.ball_states.clear()
        self.ball_fall_speeds.clear()
        self.ball_starts.clear()

        self.stage_data = load_stage(path)
        self.stage_entities = build_stage(self.stage_data, self.board_pivot)

        # 複数ボール生成
        textures = random.sample(
            _BALL_TEXTURES,
            min(len(self.stage_data.ball_starts), len(_BALL_TEXTURES)),
        )
        for i, bs in enumerate(self.stage_data.ball_starts):
            ball = Entity(
                parent=self.board_pivot,
                model='sphere',
                color=color.white,
                scale=bs.radius * 2,
                texture=textures[i % len(textures)],
            )
            self.balls.append(ball)
            self.ball_physics.append(BallPhysics(self.stage_data))
            self.ball_states.append('playing')
            self.ball_fall_speeds.append(0)
            self.ball_starts.append(bs.start)

        self._reset_game()
        self._start_countdown()

    def _reset_game(self):
        for i, ball in enumerate(self.balls):
            sx, sz = self.ball_starts[i]
            ball.position = Vec3(
                sx,
                self.stage_data.board_thickness / 2 + self.stage_data.ball_starts[i].radius,
                sz,
            )
            ball.rotation = Vec3(0, 0, 0)
            ball.visible = True
            self.ball_physics[i].reset()
            self.ball_states[i] = 'playing'
            self.ball_fall_speeds[i] = 0
        self.board_pivot.rotation = Vec3(0, 0, 0)
        self.game_won = False
        self.elapsed_time = 0
        self.win_timer = 0
        self.win_text.text = ''
        self._on_reset()

    # ------------------------------------------------------------------
    # リザルト遷移
    # ------------------------------------------------------------------

    def _go_to_result(self):
        stage_paths = list_stages(self.stages_dir)
        next_index = self.stage_index + 1
        has_next = next_index < len(stage_paths)

        # 次のステージがあれば自動で進む
        if has_next:
            next_path = stage_paths[next_index]
            self.stage_index = next_index
            self.stage_path = next_path
            self._load_stage(next_path)
            return

        # 最終ステージクリア → リザルト画面へ
        try:
            self.result_session.on_game_finish()
        except ResultApiError as e:
            print(f'[result-api] finish failed: {e}')

        self.manager.switch(
            'result',
            game_mode=self.game_mode,
            cleared=True,
            stage_index=self.stage_index,
            stage_path=self.stage_path,
            next_stage_path=None,
            elapsed_time=self.elapsed_time,
        )

    # ------------------------------------------------------------------
    # メインループ
    # ------------------------------------------------------------------

    def update(self):
        if not self.balls:
            return
        dt = time.dt
        if self._update_countdown(dt):
            return

        # クリア後 — 全goaledボールの沈下演出 → 結果画面へ
        if self.game_won:
            for i, ball in enumerate(self.balls):
                if self.ball_states[i] == 'goaled':
                    self.ball_fall_speeds[i] += 15 * dt
                    ball.y -= self.ball_fall_speeds[i] * dt
            self.win_timer += dt
            if self.win_timer > 1.5:
                self._go_to_result()
            return

        self.elapsed_time += dt

        # カウントダウンタイマー（60秒で全ステージ挑戦）
        self.timer -= dt
        if self.timer <= 0:
            self.timer = 0
            self.timer_text.text = '0'
            if not getattr(self.manager, 'bgm_muted', False):
                self._timeup_se.stop()
                self._timeup_se.play()
            self.manager.switch(
                'result',
                game_mode=self.game_mode,
                cleared=False,
                stage_index=self.stage_index,
                stage_path=self.stage_path,
                next_stage_path=None,
                elapsed_time=self.elapsed_time,
            )
            return
        self.timer_text.text = str(int(self.timer) + 1)

        # 入力
        board_tilt = self._get_board_tilt(dt)
        self._update_status()

        # 板の回転
        self.board_pivot.rotation_z = board_tilt.x
        self.board_pivot.rotation_x = board_tilt.y

        # 各ボール個別処理
        for i, ball in enumerate(self.balls):
            state = self.ball_states[i]

            if state == 'playing':
                result = self.ball_physics[i].update(ball, board_tilt, dt)
                if result == 'goal':
                    if not getattr(self.manager, 'bgm_muted', False):
                        self._fall_goal_se.stop()
                        self._fall_goal_se.play()
                    self.ball_states[i] = 'goaled'
                    self.ball_fall_speeds[i] = 0
                elif result == 'fell':
                    if not getattr(self.manager, 'bgm_muted', False):
                        self._fall_se.stop()
                        self._fall_se.play()
                    self.ball_states[i] = 'falling'
                    self.ball_fall_speeds[i] = 0

            elif state == 'falling':
                self.ball_fall_speeds[i] += 15 * dt
                ball.y -= self.ball_fall_speeds[i] * dt
                if ball.y < -5:
                    # 初期位置にリセット（ゲーム継続）
                    sx, sz = self.ball_starts[i]
                    ball.position = Vec3(
                        sx,
                        self.stage_data.board_thickness / 2 + self.stage_data.ball_starts[i].radius,
                        sz,
                    )
                    ball.rotation = Vec3(0, 0, 0)
                    self.ball_physics[i].reset()
                    self.ball_states[i] = 'playing'
                    self.ball_fall_speeds[i] = 0

            elif state == 'goaled':
                self.ball_fall_speeds[i] += 5 * dt
                ball.y -= self.ball_fall_speeds[i] * dt

        # playingボール同士の衝突判定
        playing_indices = [i for i, s in enumerate(self.ball_states) if s == 'playing']
        for a_idx in range(len(playing_indices)):
            for b_idx in range(a_idx + 1, len(playing_indices)):
                ia = playing_indices[a_idx]
                ib = playing_indices[b_idx]
                BallPhysics.collide_balls(
                    self.balls[ia], self.balls[ib],
                    self.ball_physics[ia], self.ball_physics[ib],
                )

        # 全ボールgoaled かつ 全ボールが穴に沈んでから → クリア
        if (all(s == 'goaled' for s in self.ball_states)
                and all(b.y < 0 for b in self.balls)):
            try:
                self.result_session.on_stage_cleared()
            except ResultApiError as e:
                print(f'[result-api] stage-clear failed: {e}')
            self.game_won = True
            self.win_timer = 0
            self.win_text.text = 'Clear!'

    def input(self, key):
        if key == 'r':
            self._reset_game()
        elif key == 'escape':
            self.result_session.on_game_abort()
            self.manager.switch('start')
