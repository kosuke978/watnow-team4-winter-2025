"""
ステージビルダー — JSONファイルからUrsinaエンティティを構築する
"""

import json
import math
import os
from dataclasses import dataclass, field

from ursina import Entity, Mesh, Vec3, color, destroy

_WALL_OBSTACLE_TEXTURE = "assets/ui/tree.png"


@dataclass
class BallStartData:
    start: list[float]    # [x, z]
    radius: float = 0.2


@dataclass
class HoleData:
    position: list[float]
    radius: float
    type: str = "goal"


@dataclass
class WallData:
    start: list[float]
    end: list[float]
    height: float = 0.4


@dataclass
class ObstacleData:
    type: str
    position: list[float]
    radius: float = 0.3


@dataclass
class TileData:
    position: list[float]   # [x, z] center
    size: list[float]        # [width_x, width_z]


@dataclass
class StageData:
    name: str = ""
    board_size: float = 6
    board_thickness: float = 0.5
    board_color: list[int] = field(default_factory=lambda: [139, 90, 43])
    tiles: list[TileData] = field(default_factory=list)
    ball_radius: float = 0.2
    ball_start: list[float] = field(default_factory=lambda: [0, 0])
    ball_texture: str = "assets/pinkE.png"
    ball_starts: list[BallStartData] = field(default_factory=list)
    holes: list[HoleData] = field(default_factory=list)
    walls: list[WallData] = field(default_factory=list)
    obstacles: list[ObstacleData] = field(default_factory=list)
    gravity: float = 20
    friction: float = 0.985
    max_speed: float = 8
    bounce: float = 0.6
    rim_width: float = 0.3
    rim_strength: float = 5
    background_color: list[int] = field(default_factory=lambda: [50, 50, 80])
    wall_color: list[int] = field(default_factory=lambda: [100, 70, 30])


_OBJECT_SCALE = 1.5   # 障害物・トラップ穴の拡大倍率（板はそのまま）
_BALL_SCALE = 2.0     # ボールの拡大倍率
_GOAL_SCALE = 1.3     # ゴール穴の拡大倍率


def load_stage(path: str) -> StageData:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    stage = StageData()
    stage.name = data.get("name", "")

    board = data.get("board", {})
    stage.board_size = board.get("size", 6)
    stage.board_thickness = board.get("thickness", 0.5)
    stage.board_color = board.get("color", [139, 90, 43])

    tiles_raw = board.get("tiles", None)
    if tiles_raw:
        for t in tiles_raw:
            stage.tiles.append(TileData(
                position=t["position"],
                size=t["size"],
            ))
    else:
        # 後方互換: 単一の正方形タイル
        stage.tiles.append(TileData(
            position=[0, 0],
            size=[stage.board_size, stage.board_size],
        ))

    ball = data.get("ball", {})
    stage.ball_radius = ball.get("radius", 0.2) * _BALL_SCALE
    stage.ball_start = ball.get("start", [0, 0])
    stage.ball_texture = ball.get("texture", "assets/pinkE.png")

    # 複数ボール対応
    balls_raw = data.get("balls", None)
    if balls_raw:
        for b in balls_raw:
            stage.ball_starts.append(BallStartData(
                start=b["start"],
                radius=b.get("radius", 0.2) * _BALL_SCALE,
            ))
    else:
        # 後方互換: 単一ballから1個のBallStartDataを生成
        stage.ball_starts.append(BallStartData(
            start=stage.ball_start,
            radius=stage.ball_radius,
        ))

    for h in data.get("holes", []):
        hole_type = h.get("type", "goal")
        scale = _GOAL_SCALE if hole_type == "goal" else _OBJECT_SCALE
        stage.holes.append(HoleData(
            position=h["position"],
            radius=h.get("radius", 0.25) * scale,
            type=hole_type,
        ))

    for w in data.get("walls", []):
        stage.walls.append(WallData(
            start=w["start"],
            end=w["end"],
            height=w.get("height", 0.4),
        ))

    for o in data.get("obstacles", []):
        stage.obstacles.append(ObstacleData(
            type=o.get("type", "bump"),
            position=o["position"],
            radius=o.get("radius", 0.3) * _OBJECT_SCALE,
        ))

    physics = data.get("physics", {})
    stage.gravity = physics.get("gravity", 20)
    stage.friction = physics.get("friction", 0.985)
    stage.max_speed = physics.get("max_speed", 8)
    stage.bounce = physics.get("bounce", 0.6)
    stage.rim_width = physics.get("rim_width", 0.5)
    stage.rim_strength = physics.get("rim_strength", 10)

    theme = data.get("theme", {})
    stage.background_color = theme.get("background", [50, 50, 80])
    stage.wall_color = theme.get("wall_color", [100, 70, 30])

    return stage


def _make_wedge_mesh(width, height, depth):
    """くさび形メッシュ — 板の端をせりあげるスロープ。
    原点=内側の底辺中央。+x方向に幅(width)進むと高さ(height)にせりあがる。
    頂点を面ごとに複製し、法線とUVを付与。板と同じテクスチャで描画可能。
    """
    hw = depth / 2
    p0 = Vec3(0, 0, -hw)
    p1 = Vec3(0, 0, hw)
    p2 = Vec3(width, 0, -hw)
    p3 = Vec3(width, 0, hw)
    p4 = Vec3(width, height, -hw)
    p5 = Vec3(width, height, hw)

    slope_len = math.sqrt(width * width + height * height)
    slope_n = Vec3(-height / slope_len, width / slope_len, 0)

    verts = []
    norms = []
    uvs = []
    tris = []

    def _add_tri(a, b, c, n, uv0, uv1, uv2):
        idx = len(verts)
        verts.extend([a, b, c])
        norms.extend([n, n, n])
        uvs.extend([uv0, uv1, uv2])
        tris.extend([idx, idx + 1, idx + 2])

    def _add_quad(a, b, c, d, n):
        idx = len(verts)
        verts.extend([a, b, c, d])
        norms.extend([n, n, n, n])
        uvs.extend([(0, 0), (1, 0), (1, 1), (0, 1)])
        tris.extend([idx, idx + 1, idx + 2, idx, idx + 2, idx + 3])

    _add_quad(p0, p2, p3, p1, Vec3(0, -1, 0))
    _add_quad(p0, p1, p5, p4, slope_n)
    _add_quad(p2, p4, p5, p3, Vec3(1, 0, 0))
    _add_tri(p0, p4, p2, Vec3(0, 0, -1), (0, 0), (1, 1), (1, 0))
    _add_tri(p1, p3, p5, Vec3(0, 0, 1), (0, 0), (1, 0), (1, 1))

    return Mesh(vertices=verts, triangles=tris, normals=norms, uvs=uvs)


def _is_on_any_tile(x, z, tiles):
    """指定座標がいずれかのタイル上にあるか"""
    for tile in tiles:
        tx, tz_c = tile.position
        tw, td = tile.size
        if abs(x - tx) <= tw / 2 and abs(z - tz_c) <= td / 2:
            return True
    return False


def build_stage(stage_data: StageData, board_pivot: Entity) -> dict:
    entities = {"board": [], "holes": [], "walls": [], "obstacles": [], "rims": []}

    # 板（タイル）
    for tile in stage_data.tiles:
        board = Entity(
            parent=board_pivot,
            model='cube',
            color=color.white,
            scale=(tile.size[0], stage_data.board_thickness, tile.size[1]),
            position=(tile.position[0], 0, tile.position[1]),
            texture='assets/gray_sokumen.png',
        )
        entities["board"].append(board)

    # 穴
    hole_depth = 0.8
    num_rings = 8
    for hole_data in stage_data.holes:
        hx, hz = hole_data.position
        hole_entities = []

        is_trap = hole_data.type == "trap"
        hole_model = 'quad' if is_trap else 'circle'
        hole_texture = 'assets/ui/dokuro.png' if is_trap else 'assets/ui/orenge.png'

        # 深さリング
        for i in range(num_rings):
            depth = i * (hole_depth / num_rings)
            brightness = max(10, 60 - i * 7)
            ring = Entity(
                parent=board_pivot,
                model=hole_model,
                color=color.rgb(brightness, brightness, brightness),
                scale=hole_data.radius * 2,
                position=(hx, stage_data.board_thickness / 2 - depth, hz),
                rotation_x=90,
            )
            hole_entities.append(ring)

        # 穴の底
        bottom = Entity(
            parent=board_pivot,
            model=hole_model,
            color=color.black,
            scale=hole_data.radius * 2,
            position=(hx, stage_data.board_thickness / 2 - hole_depth, hz),
            rotation_x=90,
        )
        hole_entities.append(bottom)

        # 穴の縁（四角穴=dokuro、丸穴=star）
        rim = Entity(
            parent=board_pivot,
            model=hole_model,
            color=color.white,
            texture=hole_texture,
            scale=hole_data.radius * 2.5,
            position=(hx, stage_data.board_thickness / 2 + 0.03, hz),
            rotation_x=90,
        )
        if rim.texture:
            rim.texture.filtering = False
        hole_entities.append(rim)

        entities["holes"].append(hole_entities)

    # 壁
    wall_thickness = 0.25
    for wall_data in stage_data.walls:
        sx, sz = wall_data.start
        ex, ez = wall_data.end
        cx = (sx + ex) / 2
        cz = (sz + ez) / 2
        length = math.sqrt((ex - sx) ** 2 + (ez - sz) ** 2)
        angle = math.degrees(math.atan2(ex - sx, ez - sz))

        wall = Entity(
            parent=board_pivot,
            model='cube',
            color=color.white,
            texture=_WALL_OBSTACLE_TEXTURE,
            scale=(wall_thickness, wall_data.height, length),
            position=(cx, stage_data.board_thickness / 2 + wall_data.height / 2, cz),
            rotation_y=angle,
        )
        entities["walls"].append(wall)

    # 障害物
    for obs_data in stage_data.obstacles:
        ox, oz = obs_data.position
        if obs_data.type == "bump":
            bump = Entity(
                parent=board_pivot,
                model='sphere',
                color=color.white,
                texture=_WALL_OBSTACLE_TEXTURE,
                scale=obs_data.radius * 2,
                position=(ox, stage_data.board_thickness / 2 + obs_data.radius * 0.5, oz),
            )
            entities["obstacles"].append(bump)
        elif obs_data.type in ("square", "cube", "block", "box"):
            side = obs_data.radius * 2
            square = Entity(
                parent=board_pivot,
                model='cube',
                color=color.white,
                texture=_WALL_OBSTACLE_TEXTURE,
                scale=(side, side, side),
                position=(ox, stage_data.board_thickness / 2 + side * 0.5, oz),
            )
            entities["obstacles"].append(square)

    # 皿の縁 — ボード端を内側からせりあげるくさび形スロープ
    rim_w = 0.35       # 縁の幅（板の端からどれだけ内側まで傾斜するか）
    rim_h = 0.10       # 縁の高さ（端のせりあがり量）
    seg_len = 0.7      # 辺の分割長さ
    probe = 0.15       # 外縁判定の探索距離
    bt = stage_data.board_thickness
    y_base = bt / 2    # ボード表面のY座標

    for tile in stage_data.tiles:
        tx, tz = tile.position
        tw, td = tile.size

        # ±x 縁 (z方向に分割)
        nz = max(1, round(td / seg_len))
        sz = td / nz
        for i in range(nz):
            z_mid = (tz - td / 2) + (i + 0.5) * sz
            # +x 端せりあげ（内側から端に向かって高くなる）
            if not _is_on_any_tile(tx + tw / 2 + probe, z_mid, stage_data.tiles):
                wedge = _make_wedge_mesh(rim_w, rim_h, sz)
                entities["rims"].append(Entity(
                    parent=board_pivot, model=wedge,
                    color=color.white, texture='assets/gray_sokumen.png',
                    position=(tx + tw / 2 - rim_w, y_base, z_mid),
                ))
            # -x 端せりあげ
            if not _is_on_any_tile(tx - tw / 2 - probe, z_mid, stage_data.tiles):
                wedge = _make_wedge_mesh(rim_w, rim_h, sz)
                entities["rims"].append(Entity(
                    parent=board_pivot, model=wedge,
                    color=color.white, texture='assets/gray_sokumen.png',
                    position=(tx - tw / 2 + rim_w, y_base, z_mid),
                    rotation_y=180,
                ))

        # ±z 縁 (x方向に分割)
        nx = max(1, round(tw / seg_len))
        sx_seg = tw / nx
        for i in range(nx):
            x_mid = (tx - tw / 2) + (i + 0.5) * sx_seg
            # +z 端せりあげ
            if not _is_on_any_tile(x_mid, tz + td / 2 + probe, stage_data.tiles):
                wedge = _make_wedge_mesh(rim_w, rim_h, sx_seg)
                entities["rims"].append(Entity(
                    parent=board_pivot, model=wedge,
                    color=color.white, texture='assets/gray_sokumen.png',
                    position=(x_mid, y_base, tz + td / 2 - rim_w),
                    rotation_y=-90,
                ))
            # -z 端せりあげ
            if not _is_on_any_tile(x_mid, tz - td / 2 - probe, stage_data.tiles):
                wedge = _make_wedge_mesh(rim_w, rim_h, sx_seg)
                entities["rims"].append(Entity(
                    parent=board_pivot, model=wedge,
                    color=color.white, texture='assets/gray_sokumen.png',
                    position=(x_mid, y_base, tz - td / 2 + rim_w),
                    rotation_y=90,
                ))

    return entities


def clear_stage(entities: dict):
    for b in entities.get("board", []):
        destroy(b)
    for hole_group in entities.get("holes", []):
        for e in hole_group:
            destroy(e)
    for w in entities.get("walls", []):
        destroy(w)
    for o in entities.get("obstacles", []):
        destroy(o)
    for r in entities.get("rims", []):
        destroy(r)


def list_stages(stages_dir: str) -> list[str]:
    files = sorted(f for f in os.listdir(stages_dir) if f.endswith(".json"))
    return [os.path.join(stages_dir, f) for f in files]
