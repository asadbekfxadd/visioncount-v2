from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import get_current_user, require_role
from app.models.models import (
    AnalyticsEvent, Branch, Camera, CameraStatus, EventType, User, UserRole,
)
from app.schemas.schemas import BranchCreate, BranchOut, CompanyOut

router = APIRouter(tags=["branches"])


@router.get("/companies", response_model=list[CompanyOut])
async def list_companies(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    from app.models.models import Company
    result = await db.execute(select(Company).where(Company.id == user.company_id))
    return result.scalars().all()


@router.get("/branches", response_model=list[BranchOut])
async def list_branches(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    branches = (await db.execute(select(Branch).where(Branch.company_id == user.company_id))).scalars().all()
    out: list[BranchOut] = []

    for branch in branches:
        cameras = (await db.execute(select(Camera).where(Camera.branch_id == branch.id))).scalars().all()
        camera_ids = [c.id for c in cameras]
        online = sum(1 for c in cameras if c.status == CameraStatus.ONLINE)

        entries = exits = 0
        if camera_ids:
            rows = (await db.execute(
                select(AnalyticsEvent.event_type, func.count(AnalyticsEvent.id))
                .where(AnalyticsEvent.camera_id.in_(camera_ids))
                .where(AnalyticsEvent.timestamp >= today_start)
                .group_by(AnalyticsEvent.event_type)
            )).all()
            counts = {r[0]: r[1] for r in rows}
            entries, exits = counts.get(EventType.ENTRY, 0), counts.get(EventType.EXIT, 0)

        out.append(BranchOut(
            id=branch.id, name=branch.name, address=branch.address, visitor_limit=branch.visitor_limit,
            camera_count=len(cameras), cameras_online=online,
            visitors_today=entries, entries_today=entries, exits_today=exits,
            current_occupancy=max(0, entries - exits), avg_dwell_minutes=17.0,
        ))
    return out


@router.post("/branches", response_model=BranchOut, status_code=201)
async def create_branch(
    payload: BranchCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.ADMIN)),
):
    branch = Branch(company_id=user.company_id, name=payload.name, address=payload.address,
                     visitor_limit=payload.visitor_limit)
    db.add(branch)
    await db.commit()
    await db.refresh(branch)
    return BranchOut(id=branch.id, name=branch.name, address=branch.address, visitor_limit=branch.visitor_limit)
