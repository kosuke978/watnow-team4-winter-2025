"""
ボール転がしゲーム - pymunk物理演算版
操作: 矢印キーで板を傾ける / R でリセット / ESC で終了
"""

from ursina import *
import pymunk
import math

app = Ursina()

# ウィンドウ設定
window.title = 'Ball Rolling Game (Physics)'
window.borderless = False
window.fps_counter.enabled = True

# サイズ設定
BOARD_SIZE = 6
BOARD_THICKNESS = 0.5
BALL_RADIUS = 0.2
HOLE_RADIUS = 0.25
HOLE_DEPTH = 0.8

# pymunk物理空間（XZ平面を2Dとして扱う）
space = pymunk.Space()
space.gravity = (0, 0)  # 重力は傾きで制御

# pymunk: ボールを作成
ball_mass = 1
ball_moment = pymunk.moment_for_circle(ball_mass, 0, BALL_RADIUS)
ball_body = pymunk.Body(ball_mass, ball_moment)
ball_body.position = (0, 0)
ball_shape = pymunk.Circle(ball_body, BALL_RADIUS)
ball_shape.friction = 0.7
ball_shape.elasticity = 0.4
space.add(ball_body, ball_shape)

# Ursina: 板グループ（親エンティティ）
board_pivot = Entity(position=(0, 0, 0))

# Ursina: 板（ステージ）
board = Entity(
    parent=board_pivot,
    model='cube',
    color=color.rgb(139, 90, 43),
    scale=(BOARD_SIZE, BOARD_THICKNESS, BOARD_SIZE),
    position=(0, 0, 0),
    texture='white_cube'
)

# 穴（ゴール）の位置
HOLE_POS = Vec3(2, 0, 2)

# 穴の3D表現
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
        position=(HOLE_POS.x, BOARD_THICKNESS/2 - depth, HOLE_POS.z),
        rotation_x=90,
    )
    hole_parts.append(ring)

hole_bottom = Entity(
    parent=board_pivot,
    model='circle',
    color=color.black,
    scale=HOLE_RADIUS * 2,
    position=(HOLE_POS.x, BOARD_THICKNESS/2 - HOLE_DEPTH, HOLE_POS.z),
    rotation_x=90,
)

hole_ring = Entity(
    parent=board_pivot,
    model='circle',
    color=color.white,
    scale=HOLE_RADIUS * 2.5,
    position=(HOLE_POS.x, BOARD_THICKNESS/2 + 0.03, HOLE_POS.z),
    rotation_x=90,
)

# Ursina: ボール
ball = Entity(
    parent=board_pivot,
    model='sphere',
    color=color.white,
    scale=BALL_RADIUS * 2,
    texture='image.png',
)

# 板の傾き
board_tilt = Vec2(0, 0)
max_tilt = 15
tilt_speed = 30

# 物理パラメータ
GRAVITY_STRENGTH = 50
DAMPING = 0.98

# ゲーム状態
game_won = False
game_over = False
fall_speed = 0

# 板の範囲
BOARD_EDGE = BOARD_SIZE / 2 + BALL_RADIUS * 0.5

# ライト
DirectionalLight(y=2, z=3, shadows=True, rotation=(45, -45, 45))
AmbientLight(color=color.rgba(100, 100, 100, 0.1))

# カメラ設定
camera.position = (0, 14, -12)
camera.rotation_x = 50

# UI
title_text = Text(
    text='Ball Rolling Game (Physics)',
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
    global board_tilt, game_won, game_over, fall_speed

    # pymunk: ボールをリセット
    ball_body.position = (0, 0)
    ball_body.velocity = (0, 0)
    ball_body.angular_velocity = 0

    board_tilt = Vec2(0, 0)
    board_pivot.rotation = Vec3(0, 0, 0)
    game_won = False
    game_over = False
    fall_speed = 0
    win_text.text = ''


def update():
    global board_tilt, game_won, game_over, fall_speed

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

    # Ursina: 板の回転を適用
    board_pivot.rotation_z = board_tilt.x
    board_pivot.rotation_x = board_tilt.y

    # pymunk: 傾きに基づく重力を設定
    gx = math.sin(math.radians(board_tilt.x)) * GRAVITY_STRENGTH
    gy = math.sin(math.radians(board_tilt.y)) * GRAVITY_STRENGTH
    space.gravity = (gx, gy)

    # pymunk: 減衰（摩擦の代わり）
    ball_body.velocity = (
        ball_body.velocity.x * DAMPING,
        ball_body.velocity.y * DAMPING
    )

    # pymunk: シミュレーションステップ
    dt = 1/60
    for _ in range(3):  # サブステップ
        space.step(dt / 3)

    # pymunk → Ursina: 位置を同期（pymunkのXY → UrsinaのXZ）
    ball.x = ball_body.position.x
    ball.z = ball_body.position.y
    ball.y = BOARD_THICKNESS / 2 + BALL_RADIUS

    # ボールの回転（転がり演出）
    ball.rotation_z += ball_body.velocity.x * 5 * time.dt
    ball.rotation_x += ball_body.velocity.y * 5 * time.dt

    # 板の端から落ちたか判定
    if abs(ball.x) > BOARD_EDGE or abs(ball.z) > BOARD_EDGE:
        game_over = True
        fall_speed = 0
        return

    # 穴との衝突判定
    distance_to_hole = math.sqrt(
        (ball.x - HOLE_POS.x) ** 2 +
        (ball.z - HOLE_POS.z) ** 2
    )

    if distance_to_hole < (HOLE_RADIUS - BALL_RADIUS * 0.3):
        speed = ball_body.velocity.length
        if speed < 3:
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
