# シグナリングサーバー

## なぜ必要か

WebRTCはP2P通信だが、接続を確立する前に2つのピア（iOSアプリとゲーム）がお互いの接続情報を交換する必要がある。この仲介役がシグナリングサーバー。

```
iOS ──WebSocket──> シグナリングサーバー ──WebSocket──> ゲーム
                    (SDP/ICE交換のみ)

iOS ◄══════════ WebRTC DataChannel (P2P) ══════════► ゲーム
                  (センサーデータはここを流れる)
```

シグナリングサーバーが中継するのは接続確立時の数秒間だけで、P2P接続が成立した後はセンサーデータが直接流れる。

## 役割

1. **SDP Offer/Answer の中継** — 各ピアのメディア/データ能力情報を交換
2. **ICE Candidate の中継** — 接続経路の候補（IPアドレス等）を交換

## 必要なもの

| コンポーネント | 役割 | 備考 |
|--------------|------|------|
| シグナリングサーバー | SDP/ICE交換の仲介 | **このディレクトリで実装する** |
| STUNサーバー | 各ピアのグローバルIPを通知 | Google公開サーバーを使用（実装不要） |

## 技術スタック（仕様書準拠）

- **言語**: Python
- **フレームワーク**: FastAPI + WebSocket
- **プロトコル**: WebSocket (`ws://`、本番では `wss://` 推奨)

## メッセージ形式

シグナリングサーバーが中継するJSONメッセージは3種類:

### Offer（iOS → ゲーム）
```json
{
  "type": "offer",
  "sdp": "v=0\r\no=- ...",
  "client_id": "ios_device_uuid"
}
```

### Answer（ゲーム → iOS）
```json
{
  "type": "answer",
  "sdp": "v=0\r\no=- ...",
  "client_id": "ios_device_uuid"
}
```

### ICE Candidate（双方向）
```json
{
  "type": "ice",
  "candidate": "candidate:...",
  "sdpMid": "0",
  "sdpMLineIndex": 0,
  "client_id": "ios_device_uuid"
}
```

## 接続フロー

1. iOS アプリが WebSocket でシグナリングサーバーに接続
2. ゲーム（デスクトップ/Web）も WebSocket でシグナリングサーバーに接続
3. iOS が SDP Offer を送信 → サーバーがゲームに転送
4. ゲームが SDP Answer を送信 → サーバーが iOS に転送
5. 双方が ICE Candidate を交換 → サーバーが相互に転送
6. WebRTC P2P 接続が確立 → 以降シグナリングサーバーは不要

## 参考

- iOS側の仕様: [`mobile/docs/SPECIFICATION.md`](../../mobile/docs/SPECIFICATION.md) §5.2, §6.1
