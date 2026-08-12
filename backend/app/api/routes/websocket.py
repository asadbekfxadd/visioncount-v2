from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.ws_manager import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/dashboard")
async def ws_dashboard(ws: WebSocket):
    await manager.connect("dashboard", ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive / ping frames from client
    except WebSocketDisconnect:
        await manager.disconnect("dashboard", ws)


@router.websocket("/ws/cameras/{camera_id}")
async def ws_camera(ws: WebSocket, camera_id: str):
    channel = f"camera:{camera_id}"
    await manager.connect(channel, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(channel, ws)
