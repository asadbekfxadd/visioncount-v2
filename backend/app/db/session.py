from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# в тестах у каждого запроса своё соединение (у TestClient свой event loop)
_pool = {"poolclass": NullPool} if settings.APP_ENV == "test" else {}
engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True, **_pool)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
