"""
ステージビルダー — JSONファイルからUrsinaエンティティを構築する
"""

import json
import math
import os
from dataclasses import dataclass, field

from ursina import Entity, color, destroy


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
class StageData:
    name: str = ""
    board_size: float = 6
    board_thickness: float = 0.5
    board_color: list[int] = field(default_factory=lambda: [139, 90, 43])
    ball_radius: float = 0.2
    ball_start: list[float] = field(default_factory=lambda: [0, 0])
    ball_texture: str = "image.png"
    holes: list[HoleData] = field(default_factory=list)
    walls: list[WallData] = field(default_factory=list)
    obstacles: list[ObstacleData] = field(default_factory=list)
    gravity: float = 20
    friction: float = 0.985
    max_speed: float = 8
    bounce: float = 0.6
    background_color: list[int] = field(default_factory=lambda: [50, 50, 80])
    wall_color: list[int] = field(default_factory=lambda: [100, 70, 30])


def load_stage(path: str) -> StageData:
    with open(path, "r") as f:
        data = json.load(f)

    stage = StageData()
    stage.name = data.get("name", "")

    board = data.get("board", {})
    stage.board_size = board.get("size", 6)
    stage.board_thickness = board.get("thickness", 0.5)
    stage.board_color = board.get("color", [139, 90, 43])

    ball = data.get("ball", {})
    stage.ball_radius = ball.get("radius", 0.2)
    stage.ball_start = ball.get("start", [0, 0])
    stage.ball_texture = ball.get("texture", "image.png")

    for h in data.get("holes", []):
        stage.holes.append(HoleData(
            position=h["position"],
            radius=h.get("radius", 0.25),
            type=h.get("type", "goal"),
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
            radius=o.get("radius", 0.3),
        ))

    physics = data.get("physics", {})
    stage.gravity = physics.get("gravity", 20)
    stage.friction = physics.get("friction", 0.985)
    stage.max_speed = physics.get("max_speed", 8)
    stage.bounce = physics.get("bounce", 0.6)

    theme = data.get("theme", {})
    stage.background_color = theme.get("background", [50, 50, 80])
    stage.wall_color = theme.get("wall_color", [100, 70, 30])

    return stage


def build_stage(stage_data: StageData, board_pivot: Entity) -> dict:
    entities = {"board": None, "holes": [], "walls": [], "obstacles": []}

    # 板（ボード）
    board = Entity(
        parent=board_pivot,
        model='cube',
        color=color.rgb(*stage_data.board_color),
        scale=(stage_data.board_size, stage_data.board_thickness, stage_data.board_size),
        position=(0, 0, 0),
        texture='white_cube',
    )
    entities["board"] = board

    # 穴
    hole_depth = 0.8
    num_rings = 8
    for hole_data in stage_data.holes:
        hx, hz = hole_data.position
        hole_entities = []

        # 深さリング
        for i in range(num_rings):
            depth = i * (hole_depth / num_rings)
            brightness = max(10, 60 - i * 7)
            ring = Entity(
                parent=board_pivot,
                model='circle',
                color=color.rgb(brightness, brightness, brightness),
                scale=hole_data.radius * 2,
                position=(hx, stage_data.board_thickness / 2 - depth, hz),
                rotation_x=90,
            )
            hole_entities.append(ring)

        # 穴の底
        bottom = Entity(
            parent=board_pivot,
            model='circle',
            color=color.black,
            scale=hole_data.radius * 2,
            position=(hx, stage_data.board_thickness / 2 - hole_depth, hz),
            rotation_x=90,
        )
        hole_entities.append(bottom)

        # 穴の縁
        rim = Entity(
            parent=board_pivot,
            model='circle',
            color=color.white,
            scale=hole_data.radius * 2.5,
            position=(hx, stage_data.board_thickness / 2 + 0.03, hz),
            rotation_x=90,
        )
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
            color=color.rgb(*stage_data.wall_color),
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
                color=color.rgb(*stage_data.wall_color),
                scale=obs_data.radius * 2,
                position=(ox, stage_data.board_thickness / 2 + obs_data.radius * 0.5, oz),
            )
            entities["obstacles"].append(bump)

    return entities


def clear_stage(entities: dict):
    if entities.get("board"):
        destroy(entities["board"])
    for hole_group in entities.get("holes", []):
        for e in hole_group:
            destroy(e)
    for w in entities.get("walls", []):
        destroy(w)
    for o in entities.get("obstacles", []):
        destroy(o)


def list_stages(stages_dir: str) -> list[str]:
    files = sorted(f for f in os.listdir(stages_dir) if f.endswith(".json"))
    return [os.path.join(stages_dir, f) for f in files]
