"""
ボール転がしゲーム - 板を傾けてボールを穴に入れよう！
エントリーポイント: Ursinaアプリ起動＋画面管理
"""

import os

from ursina import Ursina, Text, color, window

from screens import (
    ScreenManager,
    StartScreen,
    HowToPlayScreen,
    SoloGameScreen,
    CoopGameScreen,
    VersusGameScreen,
    ResultScreen,
)
from webrtc_client import WebRTCClient

app = Ursina()

window.title = 'Ball Rolling Game'
window.borderless = False
window.fps_counter.enabled = False
window.entity_counter.enabled = False
window.collider_counter.enabled = False
window.exit_button.enabled = False
window.color = color.rgb(30, 30, 50)
Text.default_font = 'assets/fonts/NotoSansJP.ttf'

STAGES_DIR = os.path.join(os.path.dirname(__file__), 'stages')

webrtc = WebRTCClient("ws://localhost:8080/ws")
webrtc.start()

manager = ScreenManager()
manager.add('start', StartScreen(manager))
manager.add('how_to_play', HowToPlayScreen(manager))
manager.add('game_solo', SoloGameScreen(manager, webrtc, STAGES_DIR))
manager.add('game_coop', CoopGameScreen(manager, webrtc, STAGES_DIR))
manager.add('game_versus', VersusGameScreen(manager, webrtc, STAGES_DIR))
manager.add('result', ResultScreen(manager))
manager.switch('start')


def update():
    manager.update()


def input(key):
    manager.input(key)


app.run()
