from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError
from sqlalchemy import select

from app.core.security import decode_access_token
from app.db.session import AsyncSessionLocal
from app.models.models import Branch, Camera, User
from app.services.ws_manager import manager

router = APIRouter(tags=["websocket"])

POLICY_VIOLATION = 1008


async def _user_from_token(token: str | None) -> User | None:
    if not token:
        return None
    try:
        user_id = decode_access_token(token).get("sub")
    except JWTError:
        return None
    if not user_id:
        return None
    async with AsyncSessionLocal() as db:
        user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    return user if user and user.is_active else None


async def _serve(channel: str, ws: WebSocket) -> None:
    await manager.connect(channel, ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive / ping frames from client
    except WebSocketDisconnect:
        await manager.disconnect(channel, ws)


@router.websocket("/ws/dashboard")
async def ws_dashboard(ws: WebSocket, token: str | None = None):
    user = await _user_from_token(token)
    if not user:
        await ws.close(code=POLICY_VIOLATION)
        return
    await _serve(f"dashboard:{user.company_id}", ws)


@router.websocket("/ws/cameras/{camera_id}")
async def ws_camera(ws: WebSocket, camera_id: str, token: str | None = None):
    user = await _user_from_token(token)
    if not user:
        await ws.close(code=POLICY_VIOLATION)
        return
    async with AsyncSessionLocal() as db:
        company_id = (await db.execute(
            select(Branch.company_id).join(Camera, Camera.branch_id == Branch.id).where(Camera.id == camera_id)
        )).scalar_one_or_none()
    if company_id != user.company_id:  # чужая или несуществующая камера
        await ws.close(code=POLICY_VIOLATION)
        return
    await _serve(f"camera:{camera_id}", ws)
