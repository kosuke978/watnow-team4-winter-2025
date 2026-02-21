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
        self.ball_radius = stage_data.ball_radius
        self.board_thickness = stage_data.board_thickness
        self.holes = stage_data.holes
        self.walls = stage_data.walls
        self.obstacles = stage_data.obstacles
        self.tiles = stage_data.tiles
        self.rim_width = stage_data.rim_width
        self.rim_strength = stage_data.rim_strength

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

        # 皿の縁効果（ボード端に近いほど中央に戻す力）
        self._apply_rim_force(ball.x, ball.z, dt)

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

        # 板の端から落下（タイルベース判定）
        if not self._is_on_board(new_x, new_z):
            return "fell"

        # ボール位置更新
        ball.x = new_x
        ball.z = new_z
        ball.y = self.board_thickness / 2 + self.ball_radius + self._get_rim_height(new_x, new_z)

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
                    elif hole.type == "trap":
                        return "fell"

        return "playing"

    def _rim_safe_distances(self, x, z):
        """各方向のボード端までの最大安全距離を返す (+x, -x, +z, -z)"""
        margin = self.ball_radius * 0.5
        max_safe = [0.0, 0.0, 0.0, 0.0]
        for tile in self.tiles:
            tx, tz = tile.position
            tw, td = tile.size
            if abs(x - tx) > tw / 2 + margin or abs(z - tz) > td / 2 + margin:
                continue
            max_safe[0] = max(max_safe[0], (tx + tw / 2) - x)
            max_safe[1] = max(max_safe[1], x - (tx - tw / 2))
            max_safe[2] = max(max_safe[2], (tz + td / 2) - z)
            max_safe[3] = max(max_safe[3], z - (tz - td / 2))
        return max_safe

    def _apply_rim_force(self, x, z, dt):
        """皿の縁効果 — ボード外縁に近いほど中央方向へ戻す力を加える"""
        if self.rim_width <= 0:
            return
        max_safe = self._rim_safe_distances(x, z)
        rw = self.rim_width
        rs = self.rim_strength
        if 0 < max_safe[0] < rw:
            f = ((rw - max_safe[0]) / rw) ** 2
            self.velocity.x -= rs * f * dt
        if 0 < max_safe[1] < rw:
            f = ((rw - max_safe[1]) / rw) ** 2
            self.velocity.x += rs * f * dt
        if 0 < max_safe[2] < rw:
            f = ((rw - max_safe[2]) / rw) ** 2
            self.velocity.z -= rs * f * dt
        if 0 < max_safe[3] < rw:
            f = ((rw - max_safe[3]) / rw) ** 2
            self.velocity.z += rs * f * dt

    def _get_rim_height(self, x, z):
        """縁の高さを返す — ボード端に近いほど高くなる（坂道効果）"""
        if self.rim_width <= 0:
            return 0.0
        max_safe = self._rim_safe_distances(x, z)
        rw = self.rim_width
        rim_max_h = 0.12  # 縁の最大高さ
        height = 0.0
        for safe_dist in max_safe:
            if 0 < safe_dist < rw:
                t = (rw - safe_dist) / rw
                height = max(height, rim_max_h * t * t)
        return height

    def _is_on_board(self, x: float, z: float) -> bool:
        """ボールがいずれかのタイル上にあるか判定"""
        margin = self.ball_radius * 0.5
        for tile in self.tiles:
            tx, tz = tile.position
            tw, td = tile.size
            if abs(x - tx) <= tw / 2 + margin and abs(z - tz) <= td / 2 + margin:
                return True
        return False

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

    @staticmethod
    def collide_balls(ball_a, ball_b, physics_a, physics_b):
        """球-球の衝突判定＋押し出し＋速度交換"""
        dx = ball_a.x - ball_b.x
        dz = ball_a.z - ball_b.z
        dist = math.sqrt(dx * dx + dz * dz)
        min_dist = physics_a.ball_radius + physics_b.ball_radius

        if dist < min_dist and dist > 0:
            # 法線ベクトル
            nx = dx / dist
            nz = dz / dist

            # 押し出し（半分ずつ）
            overlap = min_dist - dist
            ball_a.x += nx * overlap * 0.5
            ball_a.z += nz * overlap * 0.5
            ball_b.x -= nx * overlap * 0.5
            ball_b.z -= nz * overlap * 0.5

            # 法線方向の相対速度
            rel_vn = ((physics_a.velocity.x - physics_b.velocity.x) * nx +
                       (physics_a.velocity.z - physics_b.velocity.z) * nz)

            # 近づいている場合のみ速度交換
            if rel_vn > 0:
                bounce = min(physics_a.bounce, physics_b.bounce)
                impulse = rel_vn * (1 + bounce) * 0.5
                physics_a.velocity.x -= impulse * nx
                physics_a.velocity.z -= impulse * nz
                physics_b.velocity.x += impulse * nx
                physics_b.velocity.z += impulse * nz
