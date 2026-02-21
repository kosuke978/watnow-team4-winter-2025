"""
仮想カーソル — iOSの傾きで画面上のカーソルを動かし、ボタンクリックを発火する
"""

from ursina import Entity, camera, color


# 傾き→画面位置のマッピング範囲（±rad）
_TILT_RANGE = 0.6


class CursorHandler:
    """iOSセンサーデータからUI上の仮想カーソルを制御する。"""

    def __init__(self, webrtc_client, player_id=1, cursor_color=None):
        self._webrtc = webrtc_client
        self._player_id = player_id

        self.cursor = Entity(
            parent=camera.ui,
            model='quad',
            color=cursor_color or color.red,
            scale=(0.02, 0.02),
            z=-0.1,
            enabled=False,
        )

    def show(self):
        self.cursor.enabled = True

    def hide(self):
        self.cursor.enabled = False

    def update(self):
        """sensor_dataのroll/pitchをカーソル位置にマッピングする。"""
        if not self.cursor.enabled:
            return

        data = self._webrtc.get_latest_sensor_data(self._player_id)
        if data is None:
            return

        # roll → X, -pitch → Y  (±_TILT_RANGE rad で画面端)
        x = max(-0.5, min(0.5, data.roll / _TILT_RANGE * 0.5))
        y = max(-0.5, min(0.5, -data.pitch / _TILT_RANGE * 0.5))
        self.cursor.x = x
        self.cursor.y = y

    def check_click(self, entities):
        """カーソル位置とentitiesのAABB判定を行い、ヒットしたon_click()を発火する。"""
        cx = self.cursor.x
        cy = self.cursor.y

        for e in entities:
            if not getattr(e, 'enabled', False):
                continue
            if not hasattr(e, 'on_click') or e.on_click is None:
                continue
            if not getattr(e, 'collider', None):
                continue

            # UI座標系でのAABB判定
            ex, ey = e.x, e.y
            sx = e.scale_x / 2
            sy = e.scale_y / 2

            if (ex - sx) <= cx <= (ex + sx) and (ey - sy) <= cy <= (ey + sy):
                e.on_click()
                return
