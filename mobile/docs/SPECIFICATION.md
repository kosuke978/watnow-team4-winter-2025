# iOS モーションコントローラー アプリ仕様書

## 1. プロジェクト概要

### 1.1 目的
iOSデバイスをWiiリモコンのようなモーションコントローラーとして使用し、PC/Web上で動作するボール転がしゲームを操作する。

### 1.2 コンセプト
- iOSデバイスの加速度センサーと傾斜センサーを活用
- WebRTCによる超低レイテンシ通信
- Web移植を見据えた設計

---

## 2. 技術スタック

### 2.1 iOS側
- **開発言語**: Swift 5.9+
- **UIフレームワーク**: SwiftUI
- **最小対応OS**: iOS 15.0+
- **WebRTCライブラリ**: GoogleWebRTC.framework
- **センサー**: Core Motion Framework
- **通信**: URLSession WebSocket (シグナリング)

### 2.2 サーバー側（参考）
- **シグナリングサーバー**: Python FastAPI + WebSocket
- **WebRTC実装**: aiortc (Python) / 標準WebRTC API (Web)
- **STUNサーバー**: Google公開STUNサーバー

---

## 3. 機能要件

### 3.1 必須機能

#### F1. センサーデータ取得
- **加速度センサー**
  - 3軸（X, Y, Z）の加速度を取得
  - 更新頻度: 60Hz
  - 単位: m/s²

- **傾斜センサー（ジャイロスコープ）**
  - Pitch（前後傾斜）、Roll（左右傾斜）、Yaw（回転）
  - 更新頻度: 60Hz
  - 単位: ラジアン

#### F2. WebRTC通信
- **シグナリング**
  - WebSocket経由でSDP offer/answer交換
  - ICE候補の交換
  - 接続状態の管理

- **データチャンネル**
  - センサーデータのリアルタイム送信
  - 順序保証なし、再送なし（最低レイテンシ優先）
  - 送信頻度: 60Hz
  - データ形式: JSON

#### F3. 接続管理
- サーバーIPアドレス/URLの入力・保存
- 接続/切断機能
- 接続状態の可視化
- 自動再接続機能

#### F4. キャリブレーション
- センサーの初期位置を基準点として設定
- ゼロ点調整機能

### 3.2 オプション機能
- センサーデータの可視化（デバッグ用）
- 接続履歴の保存
- レイテンシ表示
- バッテリー最適化モード

---

## 4. システムアーキテクチャ

### 4.1 全体構成

```
┌─────────────────────────┐
│     iOS Application     │
│  ┌──────────────────┐  │
│  │  SwiftUI Views   │  │
│  └────────┬─────────┘  │
│           │             │
│  ┌────────▼─────────┐  │
│  │   View Models    │  │
│  └────────┬─────────┘  │
│           │             │
│  ┌────────▼─────────┐  │
│  │  Services Layer  │  │
│  │  ┌────────────┐  │  │
│  │  │  Motion    │  │  │
│  │  │  Service   │  │  │
│  │  └────────────┘  │  │
│  │  ┌────────────┐  │  │
│  │  │  WebRTC    │  │  │
│  │  │  Service   │  │  │
│  │  └────────────┘  │  │
│  │  ┌────────────┐  │  │
│  │  │ Signaling  │  │  │
│  │  │  Service   │  │  │
│  │  └────────────┘  │  │
│  └─────────────────┘  │
└─────────────────────────┘
         │
         │ WebSocket (Signaling)
         ▼
┌─────────────────────────┐
│   Signaling Server      │
│   (Python FastAPI)      │
└─────────────────────────┘
         │
         │ SDP/ICE Exchange
         ▼
┌─────────────────────────┐
│    Game Application     │
│  (Python / Web)         │
│                         │
│  ◄─── WebRTC Data ────  │
│       Channel (P2P)     │
└─────────────────────────┘
```

### 4.2 iOS アプリ構成

```
MotionController/
├── App/
│   └── MotionControllerApp.swift
├── Views/
│   ├── ContentView.swift           # メインビュー
│   ├── ConnectionView.swift        # 接続設定ビュー
│   ├── ControllerView.swift        # コントローラービュー
│   └── DebugView.swift             # デバッグビュー
├── ViewModels/
│   ├── ConnectionViewModel.swift   # 接続管理VM
│   └── ControllerViewModel.swift   # コントローラーVM
├── Services/
│   ├── MotionService.swift         # センサーデータ取得
│   ├── WebRTCService.swift         # WebRTC管理
│   └── SignalingService.swift      # シグナリング管理
├── Models/
│   ├── SensorData.swift            # センサーデータモデル
│   ├── ConnectionState.swift       # 接続状態モデル
│   └── SignalingMessage.swift      # シグナリングメッセージ
└── Utils/
    ├── Constants.swift             # 定数定義
    └── Extensions.swift            # 拡張機能
```

---

## 5. データ仕様

### 5.1 センサーデータ形式

```json
{
  "type": "sensor_data",
  "timestamp": 1675234567.123,
  "acceleration": {
    "x": 0.15,
    "y": -0.23,
    "z": 9.81
  },
  "rotation": {
    "pitch": 0.12,
    "roll": -0.05,
    "yaw": 0.03
  },
  "calibrated": true
}
```

### 5.2 シグナリングメッセージ形式

#### Offer
```json
{
  "type": "offer",
  "sdp": "v=0\r\no=- ...",
  "client_id": "ios_device_uuid"
}
```

#### Answer
```json
{
  "type": "answer",
  "sdp": "v=0\r\no=- ...",
  "client_id": "ios_device_uuid"
}
```

#### ICE Candidate
```json
{
  "type": "ice",
  "candidate": "candidate:...",
  "sdpMid": "0",
  "sdpMLineIndex": 0,
  "client_id": "ios_device_uuid"
}
```

---

## 6. WebRTC通信フロー

### 6.1 接続確立フロー

```
iOS App                Signaling Server           Game App
   │                          │                       │
   │──(1) Connect WS─────────►│                       │
   │                          │                       │
   │◄─(2) Connected───────────│                       │
   │                          │                       │
   │──(3) Create Offer───────►│──(4) Forward Offer──►│
   │                          │                       │
   │                          │◄─(5) Create Answer────│
   │                          │                       │
   │◄─(6) Receive Answer──────│                       │
   │                          │                       │
   │──(7) Send ICE───────────►│──(8) Forward ICE────►│
   │                          │                       │
   │◄─(9) Receive ICE─────────│◄─(10) Send ICE───────│
   │                          │                       │
   │◄────────(11) P2P Data Channel Established───────►│
   │                          │                       │
   │──────────(12) Stream Sensor Data───────────────►│
   │                          │                       │
```

### 6.2 データ送信フロー

```
Core Motion (60Hz)
    │
    ▼
MotionService
    │
    ▼
センサーデータ加工
    │
    ▼
JSON Encode
    │
    ▼
WebRTC Data Channel
    │
    ▼
Game Application
```

---

## 7. UI設計

### 7.1 画面構成

#### 接続画面（ConnectionView）
```
┌─────────────────────────┐
│   Motion Controller     │
├─────────────────────────┤
│                         │
│  Server URL:            │
│  ┌─────────────────┐   │
│  │ ws://192.168... │   │
│  └─────────────────┘   │
│                         │
│  Status: ⚫ Disconnected│
│                         │
│  ┌─────────────────┐   │
│  │    Connect      │   │
│  └─────────────────┘   │
│                         │
│  Recent Connections:    │
│  • ws://192.168.1.100  │
│  • ws://localhost:8000 │
│                         │
└─────────────────────────┘
```

#### コントローラー画面（ControllerView）
```
┌─────────────────────────┐
│   🟢 Connected          │
├─────────────────────────┤
│                         │
│  ┌───────────────────┐ │
│  │   Calibrate       │ │
│  └───────────────────┘ │
│                         │
│  Tilt:                  │
│  ┌─────────────────┐   │
│  │    📱 Device    │   │
│  │   ↗️  Tilted     │   │
│  └─────────────────┘   │
│                         │
│  Acceleration:          │
│  X: +0.15 m/s²         │
│  Y: -0.23 m/s²         │
│  Z: +9.81 m/s²         │
│                         │
│  Rotation:              │
│  Pitch: +0.12 rad      │
│  Roll:  -0.05 rad      │
│  Yaw:   +0.03 rad      │
│                         │
│  ┌───────────────────┐ │
│  │   Disconnect      │ │
│  └───────────────────┘ │
│                         │
└─────────────────────────┘
```

### 7.2 画面遷移

```
ContentView (Tab View)
├── ConnectionView
│   └── → ControllerView (接続成功時)
└── DebugView (開発時のみ)
```

---

## 8. Core Motion設定

### 8.1 センサー設定

```swift
// 更新頻度
motionManager.accelerometerUpdateInterval = 1.0 / 60.0  // 60Hz
motionManager.gyroUpdateInterval = 1.0 / 60.0           // 60Hz
motionManager.deviceMotionUpdateInterval = 1.0 / 60.0   // 60Hz

// リファレンスフレーム
motionManager.startDeviceMotionUpdates(using: .xArbitraryZVertical)
```

### 8.2 キャリブレーション

- ユーザーがキャリブレーションボタンを押した時点の値を基準値として保存
- 以降のセンサーデータから基準値を差し引いて送信

```swift
calibrationOffset = currentSensorData
transmittedData = currentSensorData - calibrationOffset
```

---

## 9. WebRTC設定

### 9.1 RTCConfiguration

```swift
let config = RTCConfiguration()
config.iceServers = [
    RTCIceServer(urlStrings: ["stun:stun.l.google.com:19302"]),
    RTCIceServer(urlStrings: ["stun:stun1.l.google.com:19302"])
]
config.sdpSemantics = .unifiedPlan
config.continualGatheringPolicy = .gatherContinually
```

### 9.2 Data Channel設定

```swift
let dataChannelConfig = RTCDataChannelConfiguration()
dataChannelConfig.isOrdered = false           // 順序保証なし
dataChannelConfig.maxRetransmits = 0          // 再送なし
dataChannelConfig.isNegotiated = false
```

---

## 10. エラーハンドリング

### 10.1 エラー種別

| エラーコード | 説明 | 対応 |
|-------------|------|------|
| E001 | センサー初期化失敗 | アプリ再起動を促す |
| E002 | WebSocket接続失敗 | URL確認、再接続 |
| E003 | WebRTC接続失敗 | ネットワーク確認、再接続 |
| E004 | Data Channel切断 | 自動再接続 |
| E005 | センサーデータ取得失敗 | センサー再初期化 |

### 10.2 自動再接続

- WebSocket切断時: 3秒後に自動再接続（最大5回）
- Data Channel切断時: 即座に再接続試行
- 失敗が続く場合: ユーザーに手動再接続を促す

---

## 11. パフォーマンス要件

### 11.1 レイテンシ
- センサー取得からWebRTC送信まで: < 16ms (60fps相当)
- エンドツーエンド: < 50ms (目標値)

### 11.2 バッテリー消費
- 1時間の連続使用で < 20%消費（目標値）
- バックグラウンド時は自動停止

### 11.3 ネットワーク帯域
- 送信データ: 約 10-20 KB/s
- JSON圧縮を検討（必要に応じて）

---

## 12. セキュリティ要件

### 12.1 通信
- シグナリング: WSS (WebSocket Secure) 推奨
- WebRTC: DTLS-SRTP（WebRTCデフォルト）

### 12.2 認証
- 開発フェーズ: 認証なし
- 本番環境: トークンベース認証を検討

---

## 13. 開発フェーズ

### Phase 1: 基本実装
- [ ] Xcodeプロジェクトセットアップ
- [ ] Core Motion統合
- [ ] 基本UI実装
- [ ] センサーデータ可視化

### Phase 2: WebRTC統合
- [ ] WebRTC.framework導入
- [ ] シグナリング実装
- [ ] WebRTC接続確立
- [ ] Data Channel実装

### Phase 3: 統合・テスト
- [ ] エンドツーエンド接続テスト
- [ ] レイテンシ測定
- [ ] エラーハンドリング実装
- [ ] UI/UX改善

### Phase 4: 最適化
- [ ] パフォーマンス最適化
- [ ] バッテリー最適化
- [ ] 自動再接続実装
- [ ] デバッグ機能追加

---

## 14. テスト要件

### 14.1 単体テスト
- MotionService: センサーデータ取得・加工
- WebRTCService: 接続管理
- SignalingService: メッセージ送受信

### 14.2 統合テスト
- センサー → WebRTC → ゲーム間のデータフロー
- 接続・切断・再接続シナリオ
- エラーハンドリング

### 14.3 デバイステスト
- iPhone 12以降
- iPad Pro
- 様々なネットワーク環境（Wi-Fi、異なるネットワーク）

---

## 15. 参考資料

### 15.1 ドキュメント
- [Apple Core Motion](https://developer.apple.com/documentation/coremotion)
- [WebRTC iOS SDK](https://webrtc.github.io/webrtc-org/native-code/ios/)
- [WebRTC Data Channels](https://developer.mozilla.org/en-US/docs/Web/API/RTCDataChannel)

### 15.2 ライブラリ
- [GoogleWebRTC](https://cocoapods.org/pods/GoogleWebRTC)
- [Starscream](https://github.com/daltoniam/Starscream) (WebSocket)

---

## 16. 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2026-02-03 | 1.0.0 | 初版作成 |

---

**作成者**: Claude Code
**最終更新**: 2026-02-03
