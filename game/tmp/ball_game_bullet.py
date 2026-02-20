"""
ボール転がしゲーム - 板を傾けてボールを穴に入れよう！
物理エンジン版: ursina + panda3d-bullet

操作: 矢印キーで板を傾ける / R でリセット / ESC で終了

必要なパッケージ:
    pip install ursina panda3d-bullet
"""

from ursina import *
from panda3d.bullet import (
    BulletWorld,
    BulletRigidBodyNode,
    BulletSphereShape,
    BulletBoxShape,
    BulletDebugNode,
)
from panda3d.core import Vec3 as PandaVec3, TransformState, Quat
import math

app = Ursina()

# ウィンドウ設定
window.title = 'Ball Rolling Game (Bullet Physics)'
window.borderless = False
window.fps_counter.enabled = True

# 板のサイズ
BOARD_SIZE = 6
BOARD_THICKNESS = 0.5
WALL_HEIGHT = 0.4
BALL_RADIUS = 0.2
HOLE_RADIUS = 0.25
HOLE_DEPTH = 0.8

# Bullet物理ワールド
physics_world = BulletWorld()
physics_world.setGravity(PandaVec3(0, -20, 0))

# デバッグ表示（Falseで非表示）
DEBUG_PHYSICS = False
if DEBUG_PHYSICS:
    debug_node = BulletDebugNode('Debug')
    debug_node.showWireframe(True)
    debug_np = render.attachNewNode(debug_node)
    debug_np.show()
    physics_world.setDebugNode(debug_node)

# 板グループ（親エンティティ）
board_pivot = Entity(position=(0, 0, 0))

# 板（ステージ）- ビジュアル
board = Entity(
    parent=board_pivot,
    model='cube',
    color=color.rgb(139, 90, 43),
    scale=(BOARD_SIZE, BOARD_THICKNESS, BOARD_SIZE),
    position=(0, 0, 0),
    texture='white_cube'
)

# 板の物理ボディ（キネマティック - スクリプトで制御）
board_shape = BulletBoxShape(PandaVec3(BOARD_SIZE / 2, BOARD_THICKNESS / 2, BOARD_SIZE / 2))
board_body = BulletRigidBodyNode('board')
board_body.addShape(board_shape)
board_body.setMass(0)  # 静的オブジェクト
board_body.setKinematic(True)
board_body.setFriction(0.8)
board_body.setRestitution(0.3)
board_np = render.attachNewNode(board_body)
physics_world.attachRigidBody(board_body)

# 壁の物理ボディを作成する関数
def create_wall_physics(pos, scale):
    """壁の物理ボディを作成"""
    shape = BulletBoxShape(PandaVec3(scale[0] / 2, scale[1] / 2, scale[2] / 2))
    body = BulletRigidBodyNode('wall')
    body.addShape(shape)
    body.setMass(0)
    body.setKinematic(True)
    body.setFriction(0.5)
    body.setRestitution(0.5)
    np = render.attachNewNode(body)
    np.setPos(pos[0], pos[1], pos[2])
    physics_world.attachRigidBody(body)
    return body, np

# 壁のビジュアルと物理
WALL_THICKNESS = 0.25
wall_configs = [
    # (position, scale)
    ((0, WALL_HEIGHT / 2, BOARD_SIZE / 2), (BOARD_SIZE + WALL_THICKNESS * 2, WALL_HEIGHT, WALL_THICKNESS)),  # 奥
    ((0, WALL_HEIGHT / 2, -BOARD_SIZE / 2), (BOARD_SIZE + WALL_THICKNESS * 2, WALL_HEIGHT, WALL_THICKNESS)),  # 手前
    ((BOARD_SIZE / 2, WALL_HEIGHT / 2, 0), (WALL_THICKNESS, WALL_HEIGHT, BOARD_SIZE)),  # 右
    ((-BOARD_SIZE / 2, WALL_HEIGHT / 2, 0), (WALL_THICKNESS, WALL_HEIGHT, BOARD_SIZE)),  # 左
]

wall_bodies = []
wall_nps = []
walls_visual = []

for pos, scale in wall_configs:
    # ビジュアル
    wall = Entity(
        parent=board_pivot,
        model='cube',
        color=color.rgb(100, 60, 30),
        scale=scale,
        position=pos,
    )
    walls_visual.append(wall)

    # 物理
    body, np = create_wall_physics(pos, scale)
    wall_bodies.append(body)
    wall_nps.append(np)

# 板の範囲（穴に落ちる判定用）
BOARD_EDGE = BOARD_SIZE / 2 - WALL_THICKNESS

# 穴（ゴール）の位置
HOLE_POS = Vec3(2, 0, 2)

# 穴の3D表現 - 複数のリングで深さを表現
hole_parts = []
num_rings = 8
for i in range(num_rings):
    depth = i * (HOLE_DEPTH / num_rings)
    brightness = max(10, 60 - i * 7)
    ring = Entity(
        parent=board_pivot,
        model='circle',
        color=color.rgb(brightness, brightness, brightness),
        scale=HOLE_RADIUS * 2,
        position=(HOLE_POS.x, BOARD_THICKNESS / 2 - depth, HOLE_POS.z),
        rotation_x=90,
    )
    hole_parts.append(ring)

# 穴の底（黒）
hole_bottom = Entity(
    parent=board_pivot,
    model='circle',
    color=color.black,
    scale=HOLE_RADIUS * 2,
    position=(HOLE_POS.x, BOARD_THICKNESS / 2 - HOLE_DEPTH, HOLE_POS.z),
    rotation_x=90,
)

# 穴の縁（白リング）
hole_ring = Entity(
    parent=board_pivot,
    model='circle',
    color=color.white,
    scale=HOLE_RADIUS * 2.5,
    position=(HOLE_POS.x, BOARD_THICKNESS / 2 + 0.03, HOLE_POS.z),
    rotation_x=90,
)

# ボール - ビジュアル
ball = Entity(
    model='sphere',
    color=color.white,
    scale=BALL_RADIUS * 2,
    texture='image.png',
)

# ボールの物理ボディ
ball_shape = BulletSphereShape(BALL_RADIUS)
ball_body = BulletRigidBodyNode('ball')
ball_body.addShape(ball_shape)
ball_body.setMass(1.0)
ball_body.setFriction(0.8)
ball_body.setRestitution(0.4)
ball_body.setLinearDamping(0.3)  # 空気抵抗的な減衰
ball_body.setAngularDamping(0.3)
ball_np = render.attachNewNode(ball_body)
physics_world.attachRigidBody(ball_body)

# 板の傾き
board_tilt = Vec2(0, 0)
max_tilt = 12
tilt_speed = 25

# ゲーム状態
game_won = False
game_over = False
fall_timer = 0

# ライト
DirectionalLight(y=2, z=3, shadows=True, rotation=(45, -45, 45))
AmbientLight(color=color.rgba(100, 100, 100, 0.1))

# カメラ設定
camera.position = (0, 14, -12)
camera.rotation_x = 50

# UI
title_text = Text(
    text='Ball Rolling Game (Bullet Physics)',
    position=(0, 0.45),
    origin=(0, 0),
    scale=2,
    color=color.white
)
instruction_text = Text(
    text='Arrow keys to tilt, R to reset, ESC to quit',
    position=(0, 0.38),
    origin=(0, 0),
    scale=1,
    color=color.light_gray
)
win_text = Text(
    text='',
    position=(0, 0),
    origin=(0, 0),
    scale=3,
    color=color.yellow
)


def sync_physics_to_board():
    """板の傾きを物理ボディに同期"""
    # 板のワールド変換を取得して物理ボディに適用
    # board_pivotの回転を使用（度数のまま使用）
    # 符号反転でUrsinaビジュアルとBullet物理の座標系を補正
    rot_x = -board_pivot.rotation_x
    rot_z = -board_pivot.rotation_z

    # Quaternionで回転を表現（setFromAxisAngleは度数を受け取る）
    quat = Quat()
    quat.setFromAxisAngle(rot_z, PandaVec3(0, 0, 1))
    quat2 = Quat()
    quat2.setFromAxisAngle(rot_x, PandaVec3(1, 0, 0))
    final_quat = quat * quat2

    # 板の物理ボディを更新
    board_np.setQuat(final_quat)
    board_np.setPos(0, 0, 0)

    # 壁の物理ボディも更新
    for i, (body, np) in enumerate(zip(wall_bodies, wall_nps)):
        pos, scale = wall_configs[i]
        # ローカル座標をワールド座標に変換
        local_pos = PandaVec3(pos[0], pos[1], pos[2])
        rotated_pos = final_quat.xform(local_pos)
        np.setPos(rotated_pos)
        np.setQuat(final_quat)


def reset_game():
    """ゲームをリセット"""
    global board_tilt, game_won, game_over, fall_timer

    # 板の傾きをリセット
    board_tilt = Vec2(0, 0)
    board_pivot.rotation = Vec3(0, 0, 0)

    # ボールの位置と速度をリセット
    ball_body.setLinearVelocity(PandaVec3(0, 0, 0))
    ball_body.setAngularVelocity(PandaVec3(0, 0, 0))
    ball_np.setPos(0, BOARD_THICKNESS / 2 + BALL_RADIUS + 0.1, 0)
    ball_np.setQuat(Quat.identQuat())

    # ボールを強制的にアクティブ化（スリープ状態を解除）
    ball_body.setActive(True)

    # 物理ボディを同期
    sync_physics_to_board()

    # ゲーム状態リセット
    game_won = False
    game_over = False
    fall_timer = 0
    win_text.text = ''


def update():
    global board_tilt, game_won, game_over, fall_timer

    dt = time.dt

    # クリア後の処理
    if game_won:
        fall_timer += dt
        # ボールを穴に落とす演出
        pos = ball_np.getPos()
        ball_np.setPos(pos.x, pos.y - 2 * dt, pos.z)
        ball.position = Vec3(pos.x, pos.y - 2 * dt, pos.z)
        if held_keys['r']:
            reset_game()
        return

    # 落下後の処理
    if game_over:
        fall_timer += dt
        if fall_timer > 1.5:
            reset_game()
        if held_keys['r']:
            reset_game()
        return

    # 板の傾き操作
    if held_keys['left arrow']:
        board_tilt.x = max(board_tilt.x - tilt_speed * dt, -max_tilt)
    if held_keys['right arrow']:
        board_tilt.x = min(board_tilt.x + tilt_speed * dt, max_tilt)
    if held_keys['up arrow']:
        board_tilt.y = max(board_tilt.y - tilt_speed * dt, -max_tilt)
    if held_keys['down arrow']:
        board_tilt.y = min(board_tilt.y + tilt_speed * dt, max_tilt)

    # 傾きを戻す
    if not held_keys['left arrow'] and not held_keys['right arrow']:
        board_tilt.x *= 0.92
    if not held_keys['up arrow'] and not held_keys['down arrow']:
        board_tilt.y *= 0.92

    # 板の回転を適用（ビジュアル）
    board_pivot.rotation_z = board_tilt.x
    board_pivot.rotation_x = -board_tilt.y

    # 物理ボディを板の傾きに同期
    sync_physics_to_board()

    # 物理シミュレーションを進める
    physics_world.doPhysics(dt)

    # ボールのビジュアルを物理ボディに同期
    pos = ball_np.getPos()
    quat = ball_np.getQuat()
    ball.position = Vec3(pos.x, pos.y, pos.z)
    # Quaternionから回転を設定
    ball.rotation = Vec3(
        math.degrees(quat.getHpr().x),
        math.degrees(quat.getHpr().y),
        math.degrees(quat.getHpr().z)
    )

    # 落下判定（Y座標が低すぎる場合）
    if pos.y < -2:
        game_over = True
        fall_timer = 0
        win_text.text = 'Fell off!\nResetting...'
        return

    # 穴との衝突判定（板のローカル座標系で計算）
    # 板の回転の逆変換を適用してローカル座標を取得
    rot_x = math.radians(-board_pivot.rotation_x)
    rot_z = math.radians(-board_pivot.rotation_z)

    # 簡易的なローカル座標変換
    local_x = pos.x
    local_z = pos.z

    distance_to_hole = math.sqrt(
        (local_x - HOLE_POS.x) ** 2 +
        (local_z - HOLE_POS.z) ** 2
    )

    if distance_to_hole < (HOLE_RADIUS - BALL_RADIUS * 0.3):
        vel = ball_body.getLinearVelocity()
        speed = math.sqrt(vel.x ** 2 + vel.z ** 2)
        if speed < 4:
            game_won = True
            win_text.text = 'Clear!\nPress R to retry'
            fall_timer = 0

    # リセット
    if held_keys['r']:
        reset_game()


def input(key):
    if key == 'escape':
        application.quit()


# 背景色
window.color = color.rgb(50, 50, 80)

# 初期位置設定
reset_game()

# ゲーム実行
app.run()
