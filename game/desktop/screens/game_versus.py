"""
対戦ゲーム画面 — 2ボード並列、P1/P2それぞれスマホ操作（キーボードはフォールバック）
"""

import math
import random

from ursina import (
    Entity, Text, DirectionalLight, AmbientLight,
    Vec2, Vec3, color, camera, window, time, held_keys, Audio,
)
from ursina.prefabs.sky import Sky
from panda3d.core import TransparencyAttrib

from screens.base import Screen
from stage_builder import load_stage, build_stage, clear_stage, list_stages
from physics import BallPhysics


class VersusGameScreen(Screen):

    def __init__(self, manager, webrtc_client, stages_dir):
        super().__init__(manager)
        self.stages_dir = stages_dir
        self.webrtc = webrtc_client

        # ボード間隔
        self.board_offset = 7

        # 背景Sky（シャドウパイプラインの影響を受けない背景）
        self.sky = Sky(texture='sky_gold')

        # P1 ボード（左）
        self.p1_pivot = Entity(position=(-self.board_offset, 0, 0))
        self.p1_ball = Entity(
            parent=self.p1_pivot,
            model='sphere',
            color=color.white,
            scale=1,
        )

        # P2 ボード（右）
        self.p2_pivot = Entity(position=(self.board_offset, 0, 0))
        self.p2_ball = Entity(
            parent=self.p2_pivot,
            model='sphere',
            color=color.white,
            scale=1,
        )

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

        # P1/P2 ラベル
        self.p1_label = self._add(Text(
            text='P1: Waiting...',
            position=(-0.45, -0.42),
            origin=(0, 0),
            scale=0.9,
            color=color.cyan,
        ))
        self.p2_label = self._add(Text(
            text='P2: Waiting...',
            position=(0.45, -0.42),
            origin=(0, 0),
            scale=0.9,
            color=color.orange,
        ))

        # スコア表示
        self.score_text = self._add(Text(
            text='0 - 0',
            position=(0, -0.42),
            origin=(0, 0),
            scale=1.2,
            color=color.white,
        ))

        # 勝利テキスト
        self.win_text = self._add(Text(
            text='',
            position=(0, 0),
            origin=(0, 0),
            scale=3,
            color=color.yellow,
        ))

        # ゲーム状態
        self.stage_data = None
        self.p1_stage_entities = {}
        self.p2_stage_entities = {}
        self.p1_physics = None
        self.p2_physics = None
        self.game_mode = 'versus'
        self.stage_index = 0
        self.stage_path = None

        self.p1_score = 0
        self.p2_score = 0

        # 各プレイヤーの状態: 'playing', 'won', 'fell'
        self.p1_state = 'playing'
        self.p2_state = 'playing'
        self.p1_fall_speed = 0
        self.p2_fall_speed = 0

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

        # BGM
        self._bgm = Audio('assets/bgm/game-bgm.mp3', loop=True, autoplay=False)
        self._fall_se = Audio('assets/bgm/fall.mp3', loop=False, autoplay=False)
        self._fall_goal_se = Audio('assets/bgm/fall_goal.mp3', loop=False, autoplay=False)

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

    def _load_stage(self, path):
        if self.p1_stage_entities:
            clear_stage(self.p1_stage_entities)
        if self.p2_stage_entities:
            clear_stage(self.p2_stage_entities)

        self.stage_data = load_stage(path)

        # P1 ボード
        self.p1_ball.scale = self.stage_data.ball_radius * 2
        self.p1_ball.texture = random.choice([
            'assets/pinkE.png', 'assets/purpleE.png', 'assets/yellowE.png',
            'assets/greenE.png', 'assets/grayE.png', 'assets/blueE.png',
        ])
        self.p1_stage_entities = build_stage(self.stage_data, self.p1_pivot)
        self.p1_physics = BallPhysics(self.stage_data)

        # P2 ボード
        self.p2_ball.scale = self.stage_data.ball_radius * 2
        self.p2_ball.texture = random.choice([
            'assets/pinkE.png', 'assets/purpleE.png', 'assets/yellowE.png',
            'assets/greenE.png', 'assets/grayE.png', 'assets/blueE.png',
        ])
        self.p2_stage_entities = build_stage(self.stage_data, self.p2_pivot)
        self.p2_physics = BallPhysics(self.stage_data)

        self.stage_text.text = self.stage_data.name

        self._reset_round()

    def _reset_round(self):
        sx, sz = self.stage_data.ball_start
        ball_y = self.stage_data.board_thickness / 2 + self.stage_data.ball_radius

        # P1
        self.p1_ball.position = Vec3(sx, ball_y, sz)
        self.p1_ball.rotation = Vec3(0, 0, 0)
        self.p1_physics.reset()
        self.p1_pivot.rotation = Vec3(0, 0, 0)
        self.p1_state = 'playing'
        self.p1_fall_speed = 0

        # P2
        self.p2_ball.position = Vec3(sx, ball_y, sz)
        self.p2_ball.rotation = Vec3(0, 0, 0)
        self.p2_physics.reset()
        self.p2_pivot.rotation = Vec3(0, 0, 0)
        self.p2_state = 'playing'
        self.p2_fall_speed = 0

        # 共通
        self.p1_tilt = Vec2(0, 0)
        self.p2_tilt = Vec2(0, 0)
        self.round_over = False
        self.round_timer = 0
        self.elapsed_time = 0
        self.win_text.text = ''
        self._update_score_display()

    def _reset_player(self, player):
        """落下したプレイヤーだけリセット"""
        sx, sz = self.stage_data.ball_start
        ball_y = self.stage_data.board_thickness / 2 + self.stage_data.ball_radius

        if player == 1:
            self.p1_ball.position = Vec3(sx, ball_y, sz)
            self.p1_ball.rotation = Vec3(0, 0, 0)
            self.p1_physics.reset()
            self.p1_pivot.rotation = Vec3(0, 0, 0)
            self.p1_state = 'playing'
            self.p1_fall_speed = 0
            self.p1_tilt = Vec2(0, 0)
        else:
            self.p2_ball.position = Vec3(sx, ball_y, sz)
            self.p2_ball.rotation = Vec3(0, 0, 0)
            self.p2_physics.reset()
            self.p2_pivot.rotation = Vec3(0, 0, 0)
            self.p2_state = 'playing'
            self.p2_fall_speed = 0
            self.p2_tilt = Vec2(0, 0)

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

    # ------------------------------------------------------------------
    # メインループ
    # ------------------------------------------------------------------

    def update(self):
        if not self.p1_physics:
            return
        dt = time.dt

        # ラウンド終了後 → リザルト画面へ
        if self.round_over:
            self.round_timer += dt
            # 落下演出
            if self.p1_state == 'won':
                self.p1_fall_speed += 15 * dt
                self.p1_ball.y -= self.p1_fall_speed * dt
            if self.p2_state == 'won':
                self.p2_fall_speed += 15 * dt
                self.p2_ball.y -= self.p2_fall_speed * dt
            if self.round_timer > 1.5:
                self._go_to_result()
            return

        self.elapsed_time += dt

        # 入力更新
        self._update_p1_input(dt)
        self._update_p2_input(dt)
        self._update_labels()

        # P1 更新
        if self.p1_state == 'playing':
            self.p1_pivot.rotation_z = self.p1_tilt.x
            self.p1_pivot.rotation_x = self.p1_tilt.y
            result1 = self.p1_physics.update(self.p1_ball, self.p1_tilt, dt)

            if result1 == 'goal':
                if not getattr(self.manager, 'bgm_muted', False):
                    self._fall_goal_se.stop()
                    self._fall_goal_se.play()
                self.p1_state = 'won'
                self.p1_score += 1
                self.p1_fall_speed = 0
                self._update_score_display()
                self.win_text.text = 'P1 Win!'
                self.round_over = True
                self.round_timer = 0
            elif result1 == 'fell':
                if not getattr(self.manager, 'bgm_muted', False):
                    self._fall_se.stop()
                    self._fall_se.play()
                self.p1_state = 'fell'
                self.p1_fall_speed = 0
        elif self.p1_state == 'fell':
            self.p1_fall_speed += 15 * dt
            self.p1_ball.y -= self.p1_fall_speed * dt
            if self.p1_ball.y < -5:
                self._reset_player(1)

        # P2 更新
        if self.p2_state == 'playing':
            self.p2_pivot.rotation_z = self.p2_tilt.x
            self.p2_pivot.rotation_x = self.p2_tilt.y
            result2 = self.p2_physics.update(self.p2_ball, self.p2_tilt, dt)

            if result2 == 'goal':
                if not getattr(self.manager, 'bgm_muted', False):
                    self._fall_goal_se.stop()
                    self._fall_goal_se.play()
                self.p2_state = 'won'
                self.p2_score += 1
                self.p2_fall_speed = 0
                self._update_score_display()
                self.win_text.text = 'P2 Win!'
                self.round_over = True
                self.round_timer = 0
            elif result2 == 'fell':
                if not getattr(self.manager, 'bgm_muted', False):
                    self._fall_se.stop()
                    self._fall_se.play()
                self.p2_state = 'fell'
                self.p2_fall_speed = 0
        elif self.p2_state == 'fell':
            self.p2_fall_speed += 15 * dt
            self.p2_ball.y -= self.p2_fall_speed * dt
            if self.p2_ball.y < -5:
                self._reset_player(2)

    def input(self, key):
        if key == 'r':
            self._reset_round()
        elif key == 'escape':
            self.manager.switch('start')
