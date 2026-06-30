from collections.abc import AsyncIterator
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Celery workers call asyncio.run() per task, creating a new event loop each time.
# A shared connection pool would hold connections bound to the previous loop, causing
# "Future attached to a different loop" errors. Workers set CELERY_WORKER=1 to opt in
# to NullPool (no pooling), so each task gets a fresh connection and closes it cleanly.
_is_worker = os.environ.get("CELERY_WORKER") == "1"

if _is_worker:
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
else:
    engine = create_async_engine(settings.database_url, pool_pre_ping=True, pool_size=10, max_overflow=20)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session

