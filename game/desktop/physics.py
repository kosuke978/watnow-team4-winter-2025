"""
ボール物理演算 — 加速度・摩擦・衝突判定・穴判定
"""

import math

from ursina import Vec3

from stage_builder import StageData


class BallPhysics:
    def __init__(self, stage_data: StageData):
        self.gravity = stage_data.gravity
        self.friction = stage_data.friction
        self.max_speed = stage_data.max_speed
        self.bounce = stage_data.bounce
        self.board_size = stage_data.board_size
        self.ball_radius = stage_data.ball_radius
        self.board_thickness = stage_data.board_thickness
        self.holes = stage_data.holes
        self.walls = stage_data.walls
        self.obstacles = stage_data.obstacles

        self.board_edge = self.board_size / 2 + self.ball_radius * 0.5
        self.velocity = Vec3(0, 0, 0)

    def reset(self):
        self.velocity = Vec3(0, 0, 0)

    def update(self, ball, board_tilt, dt) -> str:
        """物理演算して状態を返す: 'playing', 'goal', 'fell'"""

        # 傾きに基づく加速度
        accel_x = math.sin(math.radians(board_tilt.x)) * self.gravity
        accel_z = math.sin(math.radians(board_tilt.y)) * self.gravity

        # 速度更新
        self.velocity.x += accel_x * dt
        self.velocity.z += accel_z * dt

        # 摩擦
        self.velocity.x *= self.friction
        self.velocity.z *= self.friction

        # 速度上限
        speed = math.sqrt(self.velocity.x ** 2 + self.velocity.z ** 2)
        if speed > self.max_speed:
            self.velocity.x = self.velocity.x / speed * self.max_speed
            self.velocity.z = self.velocity.z / speed * self.max_speed

        # 位置更新
        new_x = ball.x + self.velocity.x * dt
        new_z = ball.z + self.velocity.z * dt

        # 壁衝突判定
        wall_thickness = 0.25
        for wall in self.walls:
            sx, sz = wall.start
            ex, ez = wall.end
            new_x, new_z = self._check_wall_collision(
                new_x, new_z, sx, sz, ex, ez, wall_thickness
            )

        # 障害物衝突判定
        for obs in self.obstacles:
            ox, oz = obs.position
            new_x, new_z = self._check_obstacle_collision(
                new_x, new_z, ox, oz, obs.radius
            )

        # 板の端から落下
        if abs(new_x) > self.board_edge or abs(new_z) > self.board_edge:
            return "fell"

        # ボール位置更新
        ball.x = new_x
        ball.z = new_z
        ball.y = self.board_thickness / 2 + self.ball_radius

        # 転がり演出
        ball.rotation_z += self.velocity.x * 100 * dt
        ball.rotation_x += self.velocity.z * 100 * dt

        # 穴との衝突判定
        for hole in self.holes:
            hx, hz = hole.position
            dist = math.sqrt((ball.x - hx) ** 2 + (ball.z - hz) ** 2)
            if dist < (hole.radius - self.ball_radius * 0.3):
                current_speed = math.sqrt(self.velocity.x ** 2 + self.velocity.z ** 2)
                if current_speed < 4:
                    if hole.type == "goal":
                        return "goal"

        return "playing"

    def _check_wall_collision(self, bx, bz, sx, sz, ex, ez, thickness):
        dx = ex - sx
        dz = ez - sz
        length = math.sqrt(dx * dx + dz * dz)
        if length == 0:
            return bx, bz

        # 壁の法線
        nx = -dz / length
        nz = dx / length

        # 壁の中心
        cx = (sx + ex) / 2
        cz = (sz + ez) / 2

        # ボールから壁中心への相対位置
        rel_x = bx - cx
        rel_z = bz - cz

        # 壁のローカル座標系に変換
        along = (rel_x * dx + rel_z * dz) / length  # 壁に沿った方向
        perp = rel_x * nx + rel_z * nz  # 壁に垂直な方向

        half_length = length / 2
        half_width = thickness / 2 + self.ball_radius

        # 壁の範囲内かチェック
        if abs(along) < half_length + self.ball_radius and abs(perp) < half_width:
            # 押し出し
            if perp >= 0:
                perp = half_width
            else:
                perp = -half_width

            bx = cx + along * (dx / length) + perp * nx
            bz = cz + along * (dz / length) + perp * nz

            # 速度の法線成分を反転
            v_perp = self.velocity.x * nx + self.velocity.z * nz
            self.velocity.x -= (1 + self.bounce) * v_perp * nx
            self.velocity.z -= (1 + self.bounce) * v_perp * nz

        return bx, bz

    def _check_obstacle_collision(self, bx, bz, ox, oz, obs_radius):
        dx = bx - ox
        dz = bz - oz
        dist = math.sqrt(dx * dx + dz * dz)
        min_dist = obs_radius + self.ball_radius

        if dist < min_dist and dist > 0:
            # 押し出し
            nx = dx / dist
            nz = dz / dist
            bx = ox + nx * min_dist
            bz = oz + nz * min_dist

            # 速度の法線成分を反転
            v_perp = self.velocity.x * nx + self.velocity.z * nz
            if v_perp < 0:
                self.velocity.x -= (1 + self.bounce) * v_perp * nx
                self.velocity.z -= (1 + self.bounce) * v_perp * nz

        return bx, bz
