from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.routes import alerts, analytics, auth, branches, cameras, dashboard, events, reports, users, websocket
from app.core.config import settings
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.services.seed import seed_demo_data

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await seed_demo_data(session)
    yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(branches.router)
app.include_router(cameras.router)
app.include_router(analytics.router)
app.include_router(reports.router)
app.include_router(alerts.router)
app.include_router(users.router)
app.include_router(events.router)
app.include_router(websocket.router)


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok", "service": settings.PROJECT_NAME}
