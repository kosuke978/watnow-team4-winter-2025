"""
シグナリングサーバー — WebRTC接続確立のためのSDP/ICE中継
起動: python main.py
"""

import json
import os
import socket
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
import uvicorn

PORT = int(os.environ.get("PORT", 8080))
ENABLE_MDNS = os.environ.get("ENABLE_MDNS", "true").lower() == "true"

# --- mDNS (Bonjour) ---

if ENABLE_MDNS:
    from zeroconf import ServiceInfo
    from zeroconf.asyncio import AsyncZeroconf

    SERVICE_TYPE = "_ballgame._tcp.local."
    SERVICE_NAME = "BallGame Signaling._ballgame._tcp.local."

    async_zeroconf: AsyncZeroconf | None = None

    async def register_mdns(port: int) -> None:
        """Bonjour サービスを非同期で登録する"""
        global async_zeroconf
        local_ip = get_local_ip()
        info = ServiceInfo(
            SERVICE_TYPE,
            SERVICE_NAME,
            addresses=[socket.inet_aton(local_ip)],
            port=port,
            properties={"path": "/ws"},
        )
        async_zeroconf = AsyncZeroconf()
        await async_zeroconf.async_register_service(info)
        print(f"[mDNS] Service registered: {SERVICE_TYPE} at {local_ip}:{port}")

    async def unregister_mdns() -> None:
        """Bonjour サービスを非同期で解除する"""
        global async_zeroconf
        if async_zeroconf is not None:
            await async_zeroconf.async_unregister_all_services()
            await async_zeroconf.async_close()
            async_zeroconf = None
            print("[mDNS] Service unregistered")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if ENABLE_MDNS:
        await register_mdns(PORT)
    else:
        print("[mDNS] Disabled (ENABLE_MDNS=false)")
    yield
    if ENABLE_MDNS:
        await unregister_mdns()

app = FastAPI(lifespan=lifespan)

# 接続中のクライアント
clients: set[WebSocket] = set()
game_clients: set[WebSocket] = set()   # role=game のクライアント

# Player ID 管理 (最大2人)
MAX_PLAYERS = 2
player_ids: dict[int, int] = {}  # id(ws) → player_id


def _find_available_player_id() -> int | None:
    """空いている最小のplayer_id(1 or 2)を返す。満員ならNone"""
    used = set(player_ids.values())
    for pid in range(1, MAX_PLAYERS + 1):
        if pid not in used:
            return pid
    return None


@app.get("/health")
async def health():
    return {"status": "ok", "clients": len(clients)}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, role: str = Query(default="player")):
    await ws.accept()

    is_game = (role == "game")

    if is_game:
        # ゲームクライアントはプレイヤー枠を使わない
        clients.add(ws)
        game_clients.add(ws)
        print(f"[+] Game client connected (total: {len(clients)}, players: {dict(player_ids.values()).__len__()})")
    else:
        # プレイヤークライアント — 空きスロットを探す
        assigned_id = _find_available_player_id()
        if assigned_id is None:
            await ws.send_text(json.dumps({
                "type": "error",
                "message": "満員です（最大2人）",
            }))
            await ws.close()
            print(f"[!] Player rejected (full). current ids: {list(player_ids.values())}")
            return

        clients.add(ws)
        player_ids[id(ws)] = assigned_id
        print(f"[+] Player P{assigned_id} connected (total: {len(clients)}, ids: {list(player_ids.values())})")

    try:
        # プレイヤーには player_id を通知
        if not is_game and id(ws) in player_ids:
            await ws.send_text(json.dumps({
                "type": "player_id_assigned",
                "player_id": player_ids[id(ws)],
            }))

        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type", "unknown")
            except json.JSONDecodeError:
                msg = None
                msg_type = None

            # sensor_data 以外のメッセージだけログ出力
            if msg_type and msg_type != "sensor_data":
                sender_label = f"P{player_ids.get(id(ws))}" if id(ws) in player_ids else "game"
                print(f"[relay] {sender_label} → {msg_type}")

            # sensor_data / button / player_name にはサーバーが管理する player_id を上書き
            sender_pid = player_ids.get(id(ws))
            msg_type = msg.get("type") if msg else None
            if msg and sender_pid is not None and msg_type in ("sensor_data", "button", "player_name"):
                msg["player_id"] = sender_pid
                data = json.dumps(msg)

            # プレイヤー → ゲームクライアントのみ転送
            # ゲームクライアント → プレイヤーのみ転送
            # iOS デバイス同士のメッセージ転送を防止する
            if is_game:
                targets = clients - game_clients
            else:
                targets = game_clients.copy()
            targets.discard(ws)

            for client in targets:
                try:
                    await client.send_text(data)
                except Exception:
                    clients.discard(client)
                    game_clients.discard(client)
                    player_ids.pop(id(client), None)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[!] Unexpected error: {e}")
    finally:
        pid = player_ids.pop(id(ws), None)
        clients.discard(ws)
        game_clients.discard(ws)
        label = f"P{pid}" if pid else "Game"
        print(f"[-] {label} disconnected (total: {len(clients)}, ids: {list(player_ids.values())})")

        # プレイヤー切断をゲームクライアントに通知
        if pid is not None:
            notify = json.dumps({"type": "player_disconnected", "player_id": pid})
            for gc in game_clients.copy():
                try:
                    await gc.send_text(notify)
                except Exception:
                    pass


def get_local_ip() -> str:
    """ローカルIPアドレスを取得"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    local_ip = get_local_ip()
    print(f"Signaling server starting...")
    print(f"  ws://localhost:{PORT}/ws")
    print(f"  ws://{local_ip}:{PORT}/ws  (use this on iPhone)")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
