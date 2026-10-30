# app/database.py
import os
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine,
)
from app.models import Base

USE_SQLITE = os.getenv("USE_SQLITE", "False").lower() == "true"

if USE_SQLITE:
    DB_URL = "sqlite+aiosqlite:///./voting_demo.db"
    engine = create_async_engine(
        DB_URL, echo=False, connect_args={"check_same_thread": False}
    )
    print("[DEMO] Using SQLite — no MySQL setup needed")
else:
    from app.core.config import settings
    engine = create_async_engine(
        settings.DATABASE_URL, echo=False,
        pool_pre_ping=True, pool_size=10, max_overflow=20,
    )
    print("[PROD] Using MySQL")

AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession,
    expire_on_commit=False, autoflush=False, autocommit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def create_all_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] All database tables ready")
