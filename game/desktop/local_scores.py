"""
ローカルスコア保存・読み込み

端末ローカルの JSON ファイルにスコアを保存する。
マイスコア（ランキング画面）で使用。
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")
_SCORES_PATH = os.path.join(os.path.dirname(__file__), "local_scores.json")


def _load_raw() -> list[dict]:
    if not os.path.exists(_SCORES_PATH):
        return []
    try:
        with open(_SCORES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _save_raw(data: list[dict]) -> None:
    with open(_SCORES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_score(
    name: str,
    cleared_stages: int,
    clear_seconds: float,
) -> None:
    """ローカルにスコアを1件追加する。"""
    now = datetime.now(JST)
    entry = {
        "name": name,
        "cleared_stages": cleared_stages,
        "clear_seconds": round(clear_seconds, 2),
        "played_at": now.isoformat(),
    }
    scores = _load_raw()
    scores.append(entry)
    _save_raw(scores)


def load_scores(limit: int = 20) -> list[dict]:
    """ローカルスコアをランキング順で返す。

    ソート: cleared_stages 降順 → clear_seconds 昇順 → name 昇順
    """
    scores = _load_raw()
    scores.sort(key=lambda r: (-r.get("cleared_stages", 0), r.get("clear_seconds", 0), r.get("name", "")))
    return scores[:limit]
