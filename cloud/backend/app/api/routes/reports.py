from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import get_current_user
from app.models.models import Report, User
from app.schemas.schemas import ReportOut, ReportRequest

router = APIRouter(tags=["reports"])


@router.get("/reports", response_model=list[ReportOut])
async def list_reports(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    rows = (await db.execute(
        select(Report).where(Report.company_id == user.company_id).order_by(Report.created_at.desc()).limit(50)
    )).scalars().all()
    return rows


@router.post("/reports", response_model=ReportOut, status_code=201)
async def generate_report(
    payload: ReportRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Queues a report export. The MVP writes the row synchronously; a production
    deployment would push this onto a background worker (Celery/RQ) and render the
    CSV/Excel/PDF file asynchronously, updating file_url when ready."""
    report = Report(
        company_id=user.company_id, type=payload.type, format=payload.format,
        period_start=payload.period_start, period_end=payload.period_end,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report
