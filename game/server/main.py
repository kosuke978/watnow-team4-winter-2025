"""
シグナリングサーバー — WebRTC接続確立のためのSDP/ICE中継
起動: python main.py
"""

import json
import os
import socket
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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


@app.get("/health")
async def health():
    return {"status": "ok", "clients": len(clients)}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    print(f"[+] Client connected (total: {len(clients)})")
    try:
        while True:
            data = await ws.receive_text()
            # ログ出力（type だけ表示）
            try:
                msg = json.loads(data)
                msg_type = msg.get("type", "unknown")
                print(f"[relay] {msg_type}")
            except json.JSONDecodeError:
                print("[relay] (non-JSON)")

            # 他の全クライアントへ転送
            for client in clients.copy():
                if client != ws:
                    try:
                        await client.send_text(data)
                    except Exception:
                        clients.discard(client)
    except WebSocketDisconnect:
        pass
    finally:
        clients.discard(ws)
        print(f"[-] Client disconnected (total: {len(clients)})")


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
