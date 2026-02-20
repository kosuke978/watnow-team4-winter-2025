"""
ゲーム画面ベースクラス — ソロ/協力/対戦の共通ロジック
"""

from ursina import (
    Entity, Text, DirectionalLight, AmbientLight,
    Vec2, Vec3, color, camera, window, time, Audio,
)

from screens.base import Screen
from stage_builder import load_stage, build_stage, clear_stage, list_stages
from physics import BallPhysics


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
        self.board_pivot = Entity(position=(0, 0, 0))
        self.ball = Entity(
            parent=self.board_pivot,
            model='sphere',
            color=color.white,
            scale=1,
        )
        self.dir_light = DirectionalLight(
            y=2, z=3, shadows=True, rotation=(45, -45, 45),
        )
        self.amb_light = AmbientLight(color=color.rgba(100, 100, 100, 0.1))
        self._scene = [self.board_pivot, self.dir_light, self.amb_light]

        # UI --- TVフレームオーバーレイ（スクリーン部分は透明→3Dステージが透ける）
        self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='assets/fonts/TVFrameGame',
            scale=(window.aspect_ratio, 1),
            z=0,
        ))

        self.stage_text = self._add(Text(
            text='',
            position=(0, 0.45),
            origin=(0, 0),
            scale=1.5,
            color=color.white,
        ))
        self.instruction_text = self._add(Text(
            text='R: Reset / ESC: Back',
            position=(0, 0.38),
            origin=(0, 0),
            scale=0.8,
            color=color.light_gray,
        ))
        self.status_text = self._add(Text(
            text='',
            position=(-0.85, -0.45),
            origin=(-0.5, 0),
            scale=0.8,
            color=color.light_gray,
        ))
        self.win_text = self._add(Text(
            text='',
            position=(0, 0),
            origin=(0, 0),
            scale=3,
            color=color.yellow,
        ))

        # ゲーム状態
        self.stage_data = None
        self.stage_entities = {}
        self.physics = None
        self.game_mode = 'solo'
        self.stage_index = 0
        self.stage_path = None
        self.game_won = False
        self.game_over = False
        self.fall_speed = 0
        self.elapsed_time = 0
        self.win_timer = 0

        # BGM
        self._bgm = Audio('assets/bgm/game-bgm.mp3', loop=True, autoplay=False)

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
        camera.position = (0, 14, -12)
        camera.rotation_x = 50

    def _on_reset(self):
        """モード固有のリセット処理。サブクラスでオーバーライド可。"""
        pass

    def _update_status(self):
        """ステータス表示の更新。サブクラスでオーバーライド可。"""
        pass

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

        if stage_path:
            self.stage_path = stage_path
            self._load_stage(stage_path)

    def on_hide(self):
        super().on_hide()
        for e in self._scene:
            e.enabled = False
        self._bgm.stop()

    # ------------------------------------------------------------------
    # ステージ管理
    # ------------------------------------------------------------------

    def _load_stage(self, path):
        if self.stage_entities:
            clear_stage(self.stage_entities)

        self.stage_data = load_stage(path)
        self.ball.scale = self.stage_data.ball_radius * 2
        self.ball.texture = self.stage_data.ball_texture
        self.stage_entities = build_stage(self.stage_data, self.board_pivot)
        self.physics = BallPhysics(self.stage_data)

        self.stage_text.text = self.stage_data.name

        self._reset_game()

    def _reset_game(self):
        sx, sz = self.stage_data.ball_start
        self.ball.position = Vec3(
            sx,
            self.stage_data.board_thickness / 2 + self.stage_data.ball_radius,
            sz,
        )
        self.ball.rotation = Vec3(0, 0, 0)
        self.physics.reset()
        self.board_pivot.rotation = Vec3(0, 0, 0)
        self.game_won = False
        self.game_over = False
        self.fall_speed = 0
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
        if not self.physics:
            return
        dt = time.dt

        # クリア後 — ボールが穴に落ちる演出 → 結果画面へ
        if self.game_won:
            self.fall_speed += 15 * dt
            self.ball.y -= self.fall_speed * dt
            self.win_timer += dt
            if self.win_timer > 1.5:
                self._go_to_result()
            return

        # 落下中 — 一定距離落ちたらリセット
        if self.game_over:
            self.fall_speed += 15 * dt
            self.ball.y -= self.fall_speed * dt
            if self.ball.y < -5:
                self._reset_game()
            return

        self.elapsed_time += dt

        # 入力
        board_tilt = self._get_board_tilt(dt)
        self._update_status()

        # 板の回転
        self.board_pivot.rotation_z = board_tilt.x
        self.board_pivot.rotation_x = board_tilt.y

        # 物理演算
        result = self.physics.update(self.ball, board_tilt, dt)

        if result == "goal":
            self.game_won = True
            self.fall_speed = 0
            self.win_timer = 0
            self.win_text.text = 'Clear!'
        elif result == "fell":
            self.game_over = True
            self.fall_speed = 0

    def input(self, key):
        if key == 'r':
            self._reset_game()
        elif key == 'escape':
            self.manager.switch('start')
