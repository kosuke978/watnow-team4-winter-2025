# CLAUDE.md

このファイルは Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイドラインを提供する。

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

`ball_game.py` がエントリーポイント。画面管理（ScreenManager）で各画面を切り替える構成。

```
game/desktop/
├── ball_game.py          # エントリーポイント（ScreenManager起動）
├── screens/
│   ├── base.py           # Screen基底クラス + ScreenManager
│   ├── start.py          # スタート画面
│   ├── stage_select.py   # ステージ選択（Solo/Co-op/Versus）
│   ├── how_to_play.py    # 使い方
│   ├── game.py           # ゲームプレイ（3Dボール転がし）
│   └── result.py         # 結果画面（対戦用 / 協力・一人で用）
├── stage_builder.py      # JSON→Ursinaエンティティ構築
├── physics.py            # ボール物理・衝突判定
├── input_handler.py      # キーボード＋WebSocket入力統合
├── ui.py                 # 共有UIユーティリティ
├── stages/*.json         # ステージ定義（JSONのみ、コード不要）
└── webrtc_client.py      # WebSocket経由センサー入力
```

**画面遷移**: `Start → Stage Select → Game → Result → Stage Select / Game`

**担当分割**:
| 担当 | 領域 | 触るファイル |
|---|---|---|
| Person A | ゲームロジック・物理 | `screens/game.py`, `physics.py` |
| Person B | ステージデザイン | `stages/*.json`（コード不要） |
| Person C | UI・画面・演出 | `screens/*.py`, `input_handler.py`, `assets/ui/` |

### UI方針

#### 基本ルール
- **Ursina組み込みUI（`Text`, `Button`, `ButtonList`, `Slider`, `Sprite` 等）** を基本として使う
- Ursina外部のUIライブラリは使わない（エコシステムに適合するものがないため）
- 日本語フォント（Noto Sans JP）を `assets/fonts/NotoSansJP.ttf` に配置済み。`ball_game.py` で `Text.default_font` に設定しているため**UIテキストに日本語を使用可能**

#### 画像アセット
- **画像アセット**で見た目をリッチにする（ボタン背景、画面背景、ロゴ等）
- 画像は `game/desktop/assets/ui/` に配置し、`texture=` / `Sprite` で読み込む
- 動的テキスト（タイム、ステータス等）は `Text` を使う
- 静的な装飾・ボタンは画像で作る（デザイン担当がFigma等で書き出し）

#### 画面（Screen）の作り方
- 全画面は `screens/base.py` の `Screen` 基底クラスを継承する
- 全UIエンティティは `self._add(entity)` で登録する（画面切替時の表示/非表示が自動化される）
- 画面遷移は `self.manager.switch('画面名', **kwargs)` で行う
- ESCキーは親画面に戻る動作にする
- `on_show()` で `window.color` を設定して背景色を変える
- 新規画面追加時は `screens/__init__.py` と `ball_game.py` にも登録する

### モバイルモーションコントローラー

ball_game.py に対してゲームコントローラーの役割を果たす。入力はiOSデバイスの加速度センサー・ジャイロスコープから取得し、WebRTC DataChannelで送信する。

### シグナリングサーバー

`game/server/` は仕様のみ(README.md)で未実装。WebRTC接続確立時のSDP/ICE候補の中継を担当する。P2P確立後は不要。

## 仕様書

詳細な技術仕様は `mobile/docs/SPECIFICATION.md` を参照。
