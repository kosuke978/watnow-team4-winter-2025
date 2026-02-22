import sys
from pathlib import Path


def get_base_dir() -> Path:
    """assets/stages がある読み取り専用ベースディレクトリ"""
    if getattr(sys, '_MEIPASS', None):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def get_user_data_dir() -> Path:
    """local_scores.json 等の書き込み先 (バンドル時は ~/Library/Application Support/BallGame/)"""
    if getattr(sys, '_MEIPASS', None):
        d = Path.home() / "Library" / "Application Support" / "BallGame"
        d.mkdir(parents=True, exist_ok=True)
        return d
    return Path(__file__).parent
