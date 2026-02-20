"""
ボール転がしゲーム - 板を傾けてボールを穴に入れよう！
エントリーポイント: Ursinaアプリ起動＋画面管理
"""

import os

from ursina import Ursina, Text, color, window

from screens import (
    ScreenManager,
    StartScreen,
    StageSelectScreen,
    HowToPlayScreen,
    GameScreen,
    ResultScreen,
)
from webrtc_client import WebRTCClient

app = Ursina()

window.title = 'Ball Rolling Game'
window.borderless = False
window.fps_counter.enabled = True
window.color = color.rgb(30, 30, 50)
Text.default_font = 'assets/fonts/NotoSansJP.ttf'

STAGES_DIR = os.path.join(os.path.dirname(__file__), 'stages')

webrtc = WebRTCClient("ws://localhost:8080/ws")
webrtc.start()

manager = ScreenManager()
manager.add('start', StartScreen(manager))
manager.add('stage_select', StageSelectScreen(manager, STAGES_DIR))
manager.add('how_to_play', HowToPlayScreen(manager))
manager.add('game', GameScreen(manager, webrtc, STAGES_DIR))
manager.add('result', ResultScreen(manager))
manager.switch('start')


def update():
    manager.update()


def input(key):
    manager.input(key)


app.run()
