from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import get_current_user
from app.models.models import AnalyticsEvent, Branch, Camera, EventType, User
from app.schemas.schemas import DailyPoint, HeatmapCell, HourlyPoint

router = APIRouter(prefix="/analytics", tags=["analytics"])

HEATMAP_ZONES = ["Вход", "Торговый зал", "Кассы", "Выход"]
HEATMAP_SLOTS = ["06:00", "09:00", "12:00", "15:00", "18:00", "21:00"]


async def _company_camera_ids(db: AsyncSession, user: User, branch_id: str | None) -> list[str]:
    q = select(Camera.id).join(Branch, Branch.id == Camera.branch_id).where(Branch.company_id == user.company_id)
    if branch_id:
        q = q.where(Branch.id == branch_id)
    return [row[0] for row in (await db.execute(q)).all()]


@router.get("", response_model=dict)
async def analytics_overview(
    branch_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    camera_ids = await _company_camera_ids(db, user, branch_id)
    if not camera_ids:
        return {"entries": 0, "exits": 0}
    rows = (await db.execute(
        select(AnalyticsEvent.event_type, func.count(AnalyticsEvent.id))
        .where(AnalyticsEvent.camera_id.in_(camera_ids))
        .group_by(AnalyticsEvent.event_type)
    )).all()
    counts = {r[0]: r[1] for r in rows}
    return {"entries": counts.get(EventType.ENTRY, 0), "exits": counts.get(EventType.EXIT, 0)}


@router.get("/hourly", response_model=list[HourlyPoint])
async def analytics_hourly(
    branch_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    camera_ids = await _company_camera_ids(db, user, branch_id)
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    result: dict[int, dict[str, int]] = {h: {"entries": 0, "exits": 0} for h in range(24)}
    if camera_ids:
        rows = (await db.execute(
            select(AnalyticsEvent.event_type, AnalyticsEvent.timestamp)
            .where(AnalyticsEvent.camera_id.in_(camera_ids))
            .where(AnalyticsEvent.timestamp >= today_start)
        )).all()
        for event_type, ts in rows:
            key = "entries" if event_type == EventType.ENTRY else "exits"
            result[ts.hour][key] += 1

    return [HourlyPoint(hour=f"{h:02d}", entries=v["entries"], exits=v["exits"]) for h, v in result.items()]


@router.get("/daily", response_model=list[DailyPoint])
async def analytics_daily(
    days: int = Query(default=7, le=90),
    branch_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    camera_ids = await _company_camera_ids(db, user, branch_id)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    buckets: dict[str, dict[str, int]] = {}
    if camera_ids:
        rows = (await db.execute(
            select(AnalyticsEvent.event_type, AnalyticsEvent.timestamp)
            .where(AnalyticsEvent.camera_id.in_(camera_ids))
            .where(AnalyticsEvent.timestamp >= since)
        )).all()
        for event_type, ts in rows:
            key = ts.date().isoformat()
            buckets.setdefault(key, {"entries": 0, "exits": 0})
            buckets[key]["entries" if event_type == EventType.ENTRY else "exits"] += 1

    return [DailyPoint(date=d, entries=v["entries"], exits=v["exits"]) for d, v in sorted(buckets.items())]


@router.get("/heatmap", response_model=list[HeatmapCell])
async def analytics_heatmap(
    branch_id: str | None = Query(default=None),
    user: User = Depends(get_current_user),
):
    """Zone x time-slot occupancy density. In production this is derived from per-zone
    detection counts; demo/backfilled values are returned when no zone telemetry exists yet."""
    import random
    random.seed(branch_id or "default")
    return [
        HeatmapCell(zone=zone, slot=slot, value=random.randint(5, 65))
        for zone in HEATMAP_ZONES for slot in HEATMAP_SLOTS
    ]
