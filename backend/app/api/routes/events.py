import hmac
from datetime import datetime, timezone

from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.models import AnalyticsEvent, Branch, Camera, CameraStatus, EventType
from app.schemas.schemas import EventIngest
from app.services.ws_manager import manager

router = APIRouter(prefix="/internal", tags=["internal"])

_fernet = Fernet(settings.FERNET_KEY.encode())


def _check_service_key(key: str | None) -> None:
    if not key or not hmac.compare_digest(key.encode(), settings.service_key.encode()):
        raise HTTPException(status_code=401, detail="Invalid service key")


def _decrypt(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return _fernet.decrypt(value.encode()).decode()
    except InvalidToken:
        return None


@router.get("/cameras")
async def internal_list_cameras(
    db: AsyncSession = Depends(get_db),
    x_service_key: str | None = Header(default=None),
):
    """Trusted service-to-service endpoint the ai-service polls on startup (and
    periodically) to learn which cameras exist and should get a pipeline worker."""
    _check_service_key(x_service_key)

    rows = (await db.execute(select(Camera))).scalars().all()
    return [
        {
            "id": cam.id, "name": cam.name, "rtsp_url": cam.rtsp_url,
            "rtsp_login": cam.rtsp_login,
            "rtsp_password": _decrypt(cam.rtsp_password_encrypted),
            "fps": cam.fps,
        }
        for cam in rows
    ]


@router.post("/events", status_code=201)
async def ingest_event(
    payload: EventIngest,
    db: AsyncSession = Depends(get_db),
    x_service_key: str | None = Header(default=None),
):
    """Called by the ai-service pipeline for every ENTRY/EXIT crossing it detects
    (or synthesizes in Demo Mode). Not exposed to end users."""
    _check_service_key(x_service_key)

    camera = (await db.execute(select(Camera).where(Camera.id == payload.camera_id))).scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Unknown camera_id")

    event = AnalyticsEvent(
        camera_id=camera.id,
        track_id=payload.track_id,
        event_type=EventType(payload.event_type),
        direction=payload.direction,
        confidence=payload.confidence,
        timestamp=payload.timestamp or datetime.now(timezone.utc),
    )
    db.add(event)
    camera.status = CameraStatus.ONLINE
    camera.last_seen_at = datetime.now(timezone.utc)
    await db.commit()

    message = {
        "type": payload.event_type,
        "camera_id": camera.id,
        "camera_name": camera.name,
        "branch_id": camera.branch_id,
        "track_id": payload.track_id,
        "timestamp": event.timestamp.isoformat(),
    }
    company_id = (await db.execute(select(Branch.company_id).where(Branch.id == camera.branch_id))).scalar_one()
    await manager.broadcast(f"dashboard:{company_id}", message)
    await manager.broadcast(f"camera:{camera.id}", message)

    return {"ok": True}
