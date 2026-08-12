from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.models import (
    Branch, Camera, CameraConfig, CameraStatus, Company, User, UserRole,
)

DEMO_BRANCHES = [
    {"name": "Atlas Chimgan", "visitor_limit": 300},
    {"name": "High Town", "visitor_limit": 220},
    {"name": "Eco Park", "visitor_limit": 350},
    {"name": "Алайский", "visitor_limit": 200},
]

DEMO_CAMERAS = {
    "Atlas Chimgan": ["Вход 1", "Торговый зал"],
    "High Town": ["Вход 2"],
    "Eco Park": ["Касса", "Торговый зал 2"],
    "Алайский": ["Выход"],
}


async def seed_demo_data(db: AsyncSession) -> None:
    existing = await db.execute(select(Company).where(Company.slug == "visioncount-demo"))
    if existing.scalar_one_or_none():
        return

    company = Company(name="VisionCount Retail", slug="visioncount-demo", timezone="Asia/Tashkent")
    db.add(company)
    await db.flush()

    owner = User(
        company_id=company.id,
        email="owner@visioncount.uz",
        full_name="Дмитрий Соколов",
        hashed_password=hash_password("demo1234"),
        role=UserRole.OWNER,
    )
    db.add(owner)

    for b in DEMO_BRANCHES:
        branch = Branch(company_id=company.id, name=b["name"], visitor_limit=b["visitor_limit"])
        db.add(branch)
        await db.flush()

        for cam_name in DEMO_CAMERAS.get(b["name"], []):
            camera = Camera(
                branch_id=branch.id,
                name=cam_name,
                rtsp_url=f"rtsp://demo.local/{cam_name.lower().replace(' ', '-')}",
                camera_type="RTSP",
                fps=25,
                status=CameraStatus.ONLINE,
            )
            db.add(camera)
            await db.flush()
            db.add(CameraConfig(
                camera_id=camera.id,
                entry_line=[{"x": 0.3, "y": 0.0}, {"x": 0.3, "y": 1.0}],
                exit_line=[{"x": 0.7, "y": 0.0}, {"x": 0.7, "y": 1.0}],
            ))

    await db.commit()
