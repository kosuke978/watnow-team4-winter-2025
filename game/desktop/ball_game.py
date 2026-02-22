"""
ボール転がしゲーム - 板を傾けてボールを穴に入れよう！
エントリーポイント: Ursinaアプリ起動＋画面管理
"""

import os
import sys

from pathutil import get_base_dir

from ursina import Ursina, Text, color, window

from screens import (
    ScreenManager,
    StartScreen,
    HowToPlayScreen,
    RankingScreen,
    SoloGameScreen,
    CoopGameScreen,
    VersusGameScreen,
    ResultScreen,
)
from webrtc_client import WebRTCClient
from cursor_handler import CursorHandler

app = Ursina()

if getattr(sys, '_MEIPASS', None) or getattr(sys, 'frozen', False):
    import ursina.application as _uapp
    from ursina import texture_importer as _teximp
    from panda3d.core import getModelPath
    _base = get_base_dir()
    # .app バンドルでは assets/ がシンボリックリンクのため
    # Path.glob('**') が再帰的にたどらない → 直接追加する
    _assets = _base / 'assets'
    _uapp.asset_folder = _base
    _uapp.compressed_textures_folder = _base / 'textures_compressed'
    _teximp.folders = [
        _uapp.compressed_textures_folder,
        _assets,                         # assets/ を直接検索対象に
        _assets / 'ui',
        _base,
        _uapp.internal_textures_folder,
    ]
    getModelPath().appendDirectory(str(_base))
    getModelPath().appendDirectory(str(_assets))

window.title = 'Ball Rolling Game'
window.borderless = False
window.fps_counter.enabled = False
window.entity_counter.enabled = False
window.collider_counter.enabled = False
window.exit_button.enabled = False
window.color = color.rgb(30, 30, 50)
Text.default_font = 'assets/fonts/NotoSansJP.ttf'

STAGES_DIR = str(get_base_dir() / 'stages')

# iOSコントローラー接続を有効にするには True に変更
ENABLE_MOBILE_INPUT = True

webrtc = WebRTCClient("wss://signaling-server-1081248663051.asia-northeast1.run.app/ws")
if ENABLE_MOBILE_INPUT:
    webrtc.start()

cursors = []
if ENABLE_MOBILE_INPUT:
    cursors.append(CursorHandler(webrtc, player_id=1, cursor_color=color.red))
    cursors.append(CursorHandler(webrtc, player_id=2, cursor_color=color.cyan))

manager = ScreenManager()
manager.add('start', StartScreen(manager, webrtc))
manager.add('how_to_play', HowToPlayScreen(manager))
manager.add('ranking', RankingScreen(manager))
manager.add('game_solo', SoloGameScreen(manager, webrtc, STAGES_DIR))
manager.add('game_coop', CoopGameScreen(manager, webrtc, STAGES_DIR))
manager.add('game_versus', VersusGameScreen(manager, webrtc, STAGES_DIR))
manager.add('result', ResultScreen(manager))
if cursors:
    manager.set_cursors(cursors, webrtc, cursor_screens={'start', 'how_to_play', 'ranking', 'result'})
manager.switch('start')


def update():
    manager.update()


def input(key):
    manager.input(key)


app.run()
