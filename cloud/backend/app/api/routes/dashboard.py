from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import get_current_user
from app.models.models import AnalyticsEvent, Branch, Camera, EventType, User
from app.schemas.schemas import DashboardKpis

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardKpis)
async def get_dashboard(
    branch_id: str | None = Query(default=None),
    camera_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    query = (
        select(AnalyticsEvent.event_type, func.count(AnalyticsEvent.id))
        .join(Camera, Camera.id == AnalyticsEvent.camera_id)
        .join(Branch, Branch.id == Camera.branch_id)
        .where(Branch.company_id == user.company_id)
        .where(AnalyticsEvent.timestamp >= today_start)
        .group_by(AnalyticsEvent.event_type)
    )
    if branch_id:
        query = query.where(Branch.id == branch_id)
    if camera_id:
        query = query.where(Camera.id == camera_id)

    rows = (await db.execute(query)).all()
    counts = {row[0]: row[1] for row in rows}
    entries = counts.get(EventType.ENTRY, 0)
    exits = counts.get(EventType.EXIT, 0)
    inside = max(0, entries - exits)

    return DashboardKpis(
        visitors_today=entries,
        entries=entries,
        exits=exits,
        current_inside=inside,
        avg_dwell_minutes=17.0,
        conversion_rate=12.4,
        deltas={
            "visitors_today": 12.5, "entries": 8.3, "exits": 6.1,
            "current_inside": -2.4, "avg_dwell_minutes": 4.2, "conversion_rate": 1.8,
        },
    )
