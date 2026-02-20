# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

iOSをWiiリモコンのようなモーションコントローラーとして使い、WebRTC経由でPythonデスクトップゲーム（ボール転がし）を操作するプロジェクト。

## プロジェクト構成

| ディレクトリ | 言語 | プラットフォーム | 主要ライブラリ / ツール |
|---|---|---|---|
| `mobile/MotionController/` | Swift (SwiftUI) | iOS 15.0+ | WebRTC, XcodeGen (`project.yml`) |
| `game/desktop/` | Python 3.11 | macOS / Windows / Linux | ursina, pymunk |
| `game/server/` | Python | サーバー（未実装） | FastAPI, WebSocket |

## ビルド・実行コマンド

### iOS モバイルアプリ

```bash
cd mobile/MotionController
xcodegen generate                # project.yml から .xcodeproj を生成
open MotionController.xcodeproj  # Xcode で開いてビルド・実行
```

### Python デスクトップゲーム

```bash
cd game/desktop
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python ball_game.py
```

## アーキテクチャ

### iOS アプリ (MVVM + Services)

```
Views ← ViewModels ← Services ← Models

ConnectionView  ← ConnectionViewModel ← SignalingService, WebRTCService
ControllerView  ← ControllerViewModel ← MotionService, WebRTCService
DebugView       (接続・センサーの詳細表示)
ContentView     (TabView によるルーティング)
```

**Services**:
- **MotionService**: Core Motion で加速度・ジャイロを60Hzで取得。キャリブレーション(オフセット減算)対応
- **SignalingService**: URLSessionWebSocketTask でシグナリングサーバーに接続。自動再接続(3秒間隔、最大5回)
- **WebRTCService**: RTCPeerConnection + RTCDataChannel(unordered, retransmit=0)で低遅延P2P通信

**接続状態遷移**: `disconnected → connectingSignaling → signalingConnected → creatingOffer → waitingForAnswer → settingRemoteDescription → exchangingICE → connected`

### データフロー

```
Core Motion (60Hz) → MotionService → ControllerViewModel → JSON encode
→ WebRTCService.sendData() → DataChannel → Python ゲーム
```

送信JSON形式:
```json
{
  "type": "sensor_data",
  "timestamp": 1675234567.123,
  "acceleration": {"x": 0.15, "y": -0.23, "z": 9.81},
  "rotation": {"pitch": 0.12, "roll": -0.05, "yaw": 0.03},
  "calibrated": true
}
```

### デスクトップゲーム

`ball_game.py` がメインのゲーム。WebRTCでiOSアプリの入力を受け取りボール転がしゲームの盤面を動かす。`ball_game_physics.py`(pymunk版)と `ball_game_bullet.py`(Bullet版)は実験的な物理エンジン差し替え版。

### モバイルモーションコントローラー

ball_game.py に対してゲームコントローラーの役割を果たす。入力はiOSデバイスの加速度センサー・ジャイロスコープから取得し、WebRTC DataChannelで送信する。

### シグナリングサーバー

`game/server/` は仕様のみ(README.md)で未実装。WebRTC接続確立時のSDP/ICE候補の中継を担当する。P2P確立後は不要。

## 仕様書

詳細な技術仕様は `mobile/docs/SPECIFICATION.md` を参照。
