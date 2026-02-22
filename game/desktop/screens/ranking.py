"""
ランキング画面

タブ切り替え:
- スコアランキング: オンライン API から取得
- マイスコア: ローカル端末の JSON ファイルから取得
"""

import json
import os
from datetime import datetime
from urllib import request
from urllib.error import URLError, HTTPError

from ursina import Audio, Entity, Text, camera, color, window, invoke

from screens.base import Screen
from local_scores import load_scores as _load_local_scores


class RankingScreen(Screen):
    def __init__(self, manager):
        super().__init__(manager)
        base_url = "https://ball-game-api-1081248663051.asia-northeast1.run.app"
        self.api_url = os.getenv('RANKING_API_URL', f'{base_url}/results?limit=20')
        self.ranking_data = []
        self._rows = []
        self._no_data_text = None
        self._fetch_failed = False
        # 現在のタブ: 'online' or 'local'
        self._current_tab = 'online'
        self._click_switch_delay = 0.06
        self._select_se = Audio('assets/bgm/selrct.mp3', loop=False, autoplay=False)
        self._modoru_se = Audio('assets/bgm/modoru.mp3', loop=False, autoplay=False)

        self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='assets/スコア背景.png',
            scale=(window.aspect_ratio, 1),
            z=1,
        ))

        # スコアランキングタブ（左上）  221x30 → scale=(0.18, 0.025)
        self._online_tab = self._add(Entity(
            model='quad',
            texture='assets/スコアランキング_red.png',
            parent=camera.ui,
            position=(-0.18, 0.22),
            scale=(0.18, 0.025),
            collider='box',
        ))
        self._online_tab.on_click = lambda: self._switch_tab('online')

        # マイスコアタブ（右上）  126x27 → scale=(0.12, 0.025)
        self._local_tab = self._add(Entity(
            model='quad',
            texture='assets/マイスコア_black.png',
            parent=camera.ui,
            position=(0.18, 0.22),
            scale=(0.12, 0.025),
            collider='box',
        ))
        self._local_tab.on_click = lambda: self._switch_tab('local')

        # ▷もどる（下部）  98x27 → scale=(0.09, 0.025)
        self._back_btn = self._add(Entity(
            model='quad',
            texture='assets/▷もどる.png',
            parent=camera.ui,
            position=(0, -0.22),
            scale=(0.09, 0.025),
            collider='box',
        ))
        self._back_btn.on_click = self._go_start_with_modoru_se

        start_y = 0.15
        row_gap = 0.063
        self._stage_rows = []
        for idx in range(5):
            y = start_y - (idx * row_gap)
            # 名前（左揃え）
            name_text = self._add(Text(
                text='',
                parent=camera.ui,
                position=(-0.2, y),
                origin=(-0.5, 0),
                scale=1.05,
                color=color.black,
                font='assets/fonts/DotGothic16-Regular.ttf',
            ))
            self._rows.append(name_text)
            # ステージ数（右揃え）
            stage_text = self._add(Text(
                text='',
                parent=camera.ui,
                position=(0.25, y),
                origin=(0.5, 0),
                scale=1.05,
                color=color.black,
                font='assets/fonts/DotGothic16-Regular.ttf',
            ))
            self._stage_rows.append(stage_text)

        self._no_data_text = self._add(Text(
            text='ランキングデータがありません',
            parent=camera.ui,
            position=(0, start_y),
            origin=(0, 0),
            scale=1.1,
            color=color.black,
            font='assets/fonts/DotGothic16-Regular.ttf',
        ))
        self._no_data_text.enabled = False

    def on_show(self, **kwargs):
        super().on_show(**kwargs)
        window.color = color.rgb(132, 16, 16)
        self._current_tab = 'online'
        self._refresh_data()

    def _switch_tab(self, tab):
        if self._current_tab == tab:
            return
        if self._select_se.playing:
            self._select_se.stop()
        self._select_se.play()
        self._current_tab = tab
        self._refresh_data()

    def _refresh_data(self):
        self._update_tab_style()
        if self._current_tab == 'online':
            self.ranking_data = self._fetch_online_data()
        else:
            self.ranking_data = self._fetch_local_data()
        self.render_ranking_rows()

    def _update_tab_style(self):
        if self._current_tab == 'online':
            self._online_tab.texture = 'assets/スコアランキング_red.png'
            self._local_tab.texture = 'assets/マイスコア_black.png'
        else:
            self._online_tab.texture = 'assets/スコアランキング_black.png'
            self._local_tab.texture = 'assets/マイスコア_red.png'

    def _fetch_online_data(self):
        self._fetch_failed = False
        try:
            with request.urlopen(self.api_url, timeout=3) as response:
                payload = response.read().decode('utf-8')
                data = json.loads(payload)
                if isinstance(data, list):
                    normalized = []
                    for row in data:
                        normalized.append({
                            'name': str(row.get('name', 'unknown')),
                            'cleared_stages': int(row.get('cleared_stages', 0)),
                            'clear_seconds': float(row.get('clear_seconds', 0.0)),
                            'played_date': self._format_date(
                                row.get('played_at_jst') or row.get('played_at') or row.get('created_at_jst')
                            ),
                        })

                    normalized.sort(
                        key=lambda value: (-value['cleared_stages'], value['clear_seconds'], value['name'])
                    )
                    return normalized
        except (URLError, HTTPError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError, ValueError, TypeError):
            self._fetch_failed = True
            return []
        return []

    def _fetch_local_data(self):
        self._fetch_failed = False
        try:
            scores = _load_local_scores(limit=20)
            normalized = []
            for row in scores:
                normalized.append({
                    'name': str(row.get('name', 'unknown')),
                    'cleared_stages': int(row.get('cleared_stages', 0)),
                    'clear_seconds': float(row.get('clear_seconds', 0.0)),
                    'played_date': self._format_date(row.get('played_at')),
                })
            return normalized
        except Exception:
            self._fetch_failed = True
            return []

    def _format_date(self, raw_value):
        if not raw_value:
            return '--/--'
        try:
            dt = datetime.fromisoformat(str(raw_value).replace('Z', '+00:00'))
            return f'{dt.month}/{dt.day}'
        except ValueError:
            return '--/--'

    def render_ranking_rows(self):
        for row_text in self._rows:
            row_text.text = ''
            row_text.enabled = False
        for stage_text in self._stage_rows:
            stage_text.text = ''
            stage_text.enabled = False

        top_rows = self.ranking_data[:5]
        if not top_rows:
            if self._fetch_failed:
                if self._current_tab == 'online':
                    self._no_data_text.text = 'ランキングを取得できませんでした'
                else:
                    self._no_data_text.text = 'スコアの読み込みに失敗しました'
            else:
                if self._current_tab == 'online':
                    self._no_data_text.text = 'ランキングデータがありません'
                else:
                    self._no_data_text.text = 'まだスコアがありません'
            self._no_data_text.enabled = True
            return

        self._no_data_text.enabled = False
        for idx, row in enumerate(top_rows):
            self._rows[idx].text = row['name']
            self._rows[idx].enabled = True
            self._stage_rows[idx].text = f'ステージ{row["cleared_stages"]}'
            self._stage_rows[idx].enabled = True

    def _go_start_with_modoru_se(self):
        if not getattr(self.manager, 'bgm_muted', False):
            if self._modoru_se.playing:
                self._modoru_se.stop()
            self._modoru_se.play()
            invoke(self.manager.switch, 'start', delay=self._click_switch_delay)
            return
        self.manager.switch('start')

    def input(self, key):
        if key == 'escape':
            self._go_start_with_modoru_se()
