"""
ボール転がしゲーム - 板を傾けてボールを穴に入れよう！
操作: 矢印キーで板を傾ける / R でリセット / ESC で終了
"""

from ursina import *
import math

app = Ursina()

# ウィンドウ設定
window.title = 'Ball Rolling Game'
window.borderless = False
window.fps_counter.enabled = True

# 板のサイズ
BOARD_SIZE = 6
BOARD_THICKNESS = 0.5
WALL_THICKNESS = 0.25
WALL_HEIGHT = 0.4
BALL_RADIUS = 0.2
HOLE_RADIUS = 0.25
HOLE_DEPTH = 0.8

# 板グループ（親エンティティ）
board_pivot = Entity(position=(0, 0, 0))

# 板（ステージ）
board = Entity(
    parent=board_pivot,
    model='cube',
    color=color.rgb(139, 90, 43),
    scale=(BOARD_SIZE, BOARD_THICKNESS, BOARD_SIZE),
    position=(0, 0, 0),
    texture='white_cube'
)

# 板の範囲（端）- ボールが半分くらい出たら落下
BOARD_EDGE = BOARD_SIZE / 2 + BALL_RADIUS * 0.5


# 穴（ゴール）の位置
HOLE_POS = Vec3(2, 0, 2)

# 穴の3D表現 - 複数のリングで深さを表現
hole_parts = []
num_rings = 8
for i in range(num_rings):
    depth = i * (HOLE_DEPTH / num_rings)
    brightness = max(10, 60 - i * 7)  # 深くなるほど暗く
    ring = Entity(
        parent=board_pivot,
        model='circle',
        color=color.rgb(brightness, brightness, brightness),
        scale=HOLE_RADIUS * 2,
        position=(HOLE_POS.x, BOARD_THICKNESS/2 - depth, HOLE_POS.z),
        rotation_x=90,
    )
    hole_parts.append(ring)

# 穴の底（黒）
hole_bottom = Entity(
    parent=board_pivot,
    model='circle',
    color=color.black,
    scale=HOLE_RADIUS * 2,
    position=(HOLE_POS.x, BOARD_THICKNESS/2 - HOLE_DEPTH, HOLE_POS.z),
    rotation_x=90,
)

# 穴の縁（白リング）
hole_ring = Entity(
    parent=board_pivot,
    model='circle',
    color=color.white,
    scale=HOLE_RADIUS * 2.5,
    position=(HOLE_POS.x, BOARD_THICKNESS/2 + 0.03, HOLE_POS.z),
    rotation_x=90,
)

# ボール（板の子要素として動く）
# テクスチャを使う場合は texture='ファイル名' を指定
# 例: texture='face.png' （同じフォルダに画像を置く）
ball = Entity(
    parent=board_pivot,
    model='sphere',
    color=color.white,
    scale=BALL_RADIUS * 2,
    texture='image.png',
)

# ボールの物理状態
ball_velocity = Vec3(0, 0, 0)
gravity = 20
friction = 0.985
bounce = 0.6

# 板の傾き
board_tilt = Vec2(0, 0)
max_tilt = 12
tilt_speed = 25

# ゲーム状態
game_won = False
game_over = False  # 落下中
fall_speed = 0

# ライト
DirectionalLight(y=2, z=3, shadows=True, rotation=(45, -45, 45))
AmbientLight(color=color.rgba(100, 100, 100, 0.1))

# カメラ設定
camera.position = (0, 14, -12)
camera.rotation_x = 50

# UI
title_text = Text(
    text='Ball Rolling Game',
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


def reset_game():
    """ゲームをリセット"""
    global ball_velocity, board_tilt, game_won, game_over, fall_speed
    ball.position = Vec3(0, BOARD_THICKNESS/2 + BALL_RADIUS, 0)
    ball_velocity = Vec3(0, 0, 0)
    board_tilt = Vec2(0, 0)
    board_pivot.rotation = Vec3(0, 0, 0)
    game_won = False
    game_over = False
    fall_speed = 0
    win_text.text = ''


def update():
    global ball_velocity, board_tilt, game_won, game_over, fall_speed

    # クリア後の処理
    if game_won:
        fall_speed += 15 * time.dt
        ball.y -= fall_speed * time.dt
        if held_keys['r']:
            reset_game()
        return

    # 落下中の処理
    if game_over:
        fall_speed += 15 * time.dt
        ball.y -= fall_speed * time.dt
        # 一定以下に落ちたらリセット
        if ball.y < -5:
            reset_game()
        if held_keys['r']:
            reset_game()
        return

    # 板の傾き操作
    if held_keys['left arrow']:
        board_tilt.x = max(board_tilt.x - tilt_speed * time.dt, -max_tilt)
    if held_keys['right arrow']:
        board_tilt.x = min(board_tilt.x + tilt_speed * time.dt, max_tilt)
    if held_keys['up arrow']:
        board_tilt.y = min(board_tilt.y + tilt_speed * time.dt, max_tilt)
    if held_keys['down arrow']:
        board_tilt.y = max(board_tilt.y - tilt_speed * time.dt, -max_tilt)

    # 傾きを戻す
    if not held_keys['left arrow'] and not held_keys['right arrow']:
        board_tilt.x *= 0.92
    if not held_keys['up arrow'] and not held_keys['down arrow']:
        board_tilt.y *= 0.92

    # 板の回転を適用
    board_pivot.rotation_z = board_tilt.x
    board_pivot.rotation_x = board_tilt.y

    # 傾きに基づく加速度（ローカル座標系）
    # 板が傾いた方向にボールが転がる
    accel_x = math.sin(math.radians(board_tilt.x)) * gravity
    accel_z = math.sin(math.radians(board_tilt.y)) * gravity

    # 速度更新
    ball_velocity.x += accel_x * time.dt
    ball_velocity.z += accel_z * time.dt

    # 摩擦
    ball_velocity.x *= friction
    ball_velocity.z *= friction

    # 速度上限
    max_speed = 8
    speed = math.sqrt(ball_velocity.x ** 2 + ball_velocity.z ** 2)
    if speed > max_speed:
        ball_velocity.x = ball_velocity.x / speed * max_speed
        ball_velocity.z = ball_velocity.z / speed * max_speed

    # 位置更新（ローカル座標系で直接更新）
    new_x = ball.x + ball_velocity.x * time.dt
    new_z = ball.z + ball_velocity.z * time.dt

    # 板の端から落ちたら落下開始
    if abs(new_x) > BOARD_EDGE or abs(new_z) > BOARD_EDGE:
        game_over = True
        fall_speed = 0
        return

    # ボールの位置を更新（Y座標は板の上に固定）
    ball.x = new_x
    ball.z = new_z
    ball.y = BOARD_THICKNESS / 2 + BALL_RADIUS

    # ボールの回転（転がり演出）
    # 左右移動(X) → Z軸周りに回転
    # 前後移動(Z) → X軸周りに回転
    ball.rotation_z += ball_velocity.x * 100 * time.dt
    ball.rotation_x += ball_velocity.z * 100 * time.dt

    # 穴との衝突判定
    distance_to_hole = math.sqrt(
        (ball.x - HOLE_POS.x) ** 2 +
        (ball.z - HOLE_POS.z) ** 2
    )

    if distance_to_hole < (HOLE_RADIUS - BALL_RADIUS * 0.3):
        speed = math.sqrt(ball_velocity.x ** 2 + ball_velocity.z ** 2)
        if speed < 4:
            game_won = True
            win_text.text = 'Clear!\nPress R to retry'
            fall_speed = 0

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
