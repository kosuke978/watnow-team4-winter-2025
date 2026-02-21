"""
ランキング画面
"""

import json
import os
from datetime import datetime
from urllib import request
from urllib.error import URLError, HTTPError

from ursina import Entity, Text, camera, color, window

from screens.base import Screen


class RankingScreen(Screen):
    def __init__(self, manager):
        super().__init__(manager)
        base_url = os.getenv('RESULT_API_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
        self.api_url = os.getenv('RANKING_API_URL', f'{base_url}/results?limit=20')
        self.ranking_data = []
        self._rows = []
        self._no_data_text = None
        self._fetch_failed = False

        self._add(Entity(
            parent=camera.ui,
            model='quad',
            texture='assets/ui/ranking.png',
            scale=(window.aspect_ratio, 1),
            z=1,
        ))

        start_y = 0.18
        row_gap = 0.055
        for idx in range(10):
            row_text = self._add(Text(
                text='',
                parent=camera.ui,
                position=(0, start_y - (idx * row_gap)),
                origin=(0, 0),
                scale=1.05,
                color=color.black,
                font='assets/fonts/DotGothic16-Regular.ttf',
            ))
            self._rows.append(row_text)

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
        self.ranking_data = self.fetch_ranking_data()
        self.render_ranking_rows()

    def fetch_ranking_data(self):
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

        top_rows = self.ranking_data[:10]
        if not top_rows:
            if self._fetch_failed:
                self._no_data_text.text = 'ランキングを取得できませんでした'
            else:
                self._no_data_text.text = 'ランキングデータがありません'
            self._no_data_text.enabled = True
            return

        self._no_data_text.enabled = False
        for idx, row in enumerate(top_rows, start=1):
            self._rows[idx - 1].text = (
                f'{idx:>2}  {row["name"]:<12}  ステージ{row["cleared_stages"]:<2}  {row["played_date"]:>5}'
            )
            self._rows[idx - 1].enabled = True
