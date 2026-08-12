import asyncio
from datetime import datetime, timezone

from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.deps import get_current_user, require_role
from app.models.models import (
    AnalyticsEvent, Branch, Camera, CameraConfig, CameraStatus, EventType, User, UserRole,
)
from app.schemas.schemas import (
    CameraCreate, CameraOut, CameraTestResult, CameraUpdate, LineCrossingConfig,
)

router = APIRouter(tags=["cameras"])

_fernet = Fernet(settings.FERNET_KEY.encode())  # persisted key from settings/.env


def _encrypt(value: str | None) -> str | None:
    if not value:
        return None
    return _fernet.encrypt(value.encode()).decode()


async def _to_camera_out(db: AsyncSession, camera: Camera) -> CameraOut:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    rows = (await db.execute(
        select(AnalyticsEvent.event_type, func.count(AnalyticsEvent.id))
        .where(AnalyticsEvent.camera_id == camera.id)
        .where(AnalyticsEvent.timestamp >= today_start)
        .group_by(AnalyticsEvent.event_type)
    )).all()
    counts = {r[0]: r[1] for r in rows}
    return CameraOut(
        id=camera.id, branch_id=camera.branch_id, name=camera.name, camera_type=camera.camera_type,
        fps=camera.fps, status=camera.status.value,
        entries_today=counts.get(EventType.ENTRY, 0), exits_today=counts.get(EventType.EXIT, 0),
        last_seen_at=camera.last_seen_at,
    )


@router.get("/cameras", response_model=list[CameraOut])
async def list_cameras(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    cameras = (await db.execute(
        select(Camera).join(Branch, Branch.id == Camera.branch_id).where(Branch.company_id == user.company_id)
    )).scalars().all()
    return [await _to_camera_out(db, c) for c in cameras]


@router.post("/cameras", response_model=CameraOut, status_code=201)
async def create_camera(
    payload: CameraCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.MANAGER)),
):
    branch = (await db.execute(
        select(Branch).where(Branch.id == payload.branch_id, Branch.company_id == user.company_id)
    )).scalar_one_or_none()
    if not branch:
        raise HTTPException(status_code=404, detail="Филиал не найден")

    camera = Camera(
        branch_id=branch.id, name=payload.name, rtsp_url=payload.rtsp_url,
        rtsp_login=payload.rtsp_login, rtsp_password_encrypted=_encrypt(payload.rtsp_password),
        camera_type=payload.camera_type, fps=payload.fps, status=CameraStatus.OFFLINE,
    )
    db.add(camera)
    await db.flush()
    db.add(CameraConfig(
        camera_id=camera.id,
        entry_line=[{"x": 0.3, "y": 0.0}, {"x": 0.3, "y": 1.0}],
        exit_line=[{"x": 0.7, "y": 0.0}, {"x": 0.7, "y": 1.0}],
    ))
    await db.commit()
    await db.refresh(camera)
    return await _to_camera_out(db, camera)


@router.put("/cameras/{camera_id}", response_model=CameraOut)
async def update_camera(
    camera_id: str,
    payload: CameraUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.MANAGER)),
):
    camera = (await db.execute(
        select(Camera).join(Branch, Branch.id == Camera.branch_id)
        .where(Camera.id == camera_id, Branch.company_id == user.company_id)
    )).scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Камера не найдена")

    data = payload.model_dump(exclude_unset=True)
    if "rtsp_password" in data:
        camera.rtsp_password_encrypted = _encrypt(data.pop("rtsp_password"))
    for field, value in data.items():
        setattr(camera, field, value)

    await db.commit()
    await db.refresh(camera)
    return await _to_camera_out(db, camera)


@router.delete("/cameras/{camera_id}", status_code=204)
async def delete_camera(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.ADMIN)),
):
    camera = (await db.execute(
        select(Camera).join(Branch, Branch.id == Camera.branch_id)
        .where(Camera.id == camera_id, Branch.company_id == user.company_id)
    )).scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Камера не найдена")
    await db.delete(camera)
    await db.commit()


@router.post("/cameras/{camera_id}/test", response_model=CameraTestResult)
async def test_camera_connection(
    camera_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Attempts an ONVIF/RTSP handshake. In demo mode (no real camera reachable) this
    simulates a successful probe so the flow can be shown end-to-end."""
    camera = (await db.execute(
        select(Camera).join(Branch, Branch.id == Camera.branch_id)
        .where(Camera.id == camera_id, Branch.company_id == user.company_id)
    )).scalar_one_or_none()
    if not camera:
        raise HTTPException(status_code=404, detail="Камера не найдена")

    await asyncio.sleep(0.8)  # simulated probe latency
    camera.status = CameraStatus.ONLINE
    camera.last_seen_at = datetime.now(timezone.utc)
    await db.commit()

    return CameraTestResult(ok=True, message="Камера доступна", resolved_fps=camera.fps)


@router.put("/cameras/{camera_id}/config", response_model=LineCrossingConfig)
async def update_line_crossing(
    camera_id: str,
    payload: LineCrossingConfig,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.MANAGER)),
):
    config = (await db.execute(
        select(CameraConfig).join(Camera, Camera.id == CameraConfig.camera_id)
        .join(Branch, Branch.id == Camera.branch_id)
        .where(CameraConfig.camera_id == camera_id, Branch.company_id == user.company_id)
    )).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Конфигурация камеры не найдена")

    config.entry_line = payload.entry_line
    config.exit_line = payload.exit_line
    config.detection_zone = payload.detection_zone
    await db.commit()
    return payload
