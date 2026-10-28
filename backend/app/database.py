# app/database.py
# SQLAlchemy async engine + session factory wired to MySQL via PyMySQL driver.
# FastAPI routes obtain a session through the `get_db` dependency.

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.models import Base  # ensure all tables are registered

# ---------------------------------------------------------------------------
# Engine — pool_pre_ping keeps stale connections from silently failing
# ---------------------------------------------------------------------------
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,          # set False in production
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,         # avoid lazy-load issues after commit
    autoflush=False,
    autocommit=False,
)


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async DB session and guarantee it is closed after the request,
    rolling back automatically if an unhandled exception propagates.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# Table creation helper (used in tests / initial bootstrap only)
# ---------------------------------------------------------------------------
async def create_all_tables() -> None:
    """Create all tables if they do not already exist.  Production should use Alembic."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
