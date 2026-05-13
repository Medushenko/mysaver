# app/db.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# === 1. Force Async Driver ===
DATABASE_URL = settings.DATABASE_URL
if not DATABASE_URL.startswith("postgresql+asyncpg"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# === 2. Async Engine ===
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.DEBUG
)

# === 3. Async Session Factory ===
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# === 4. Sync Session Factory (для Celery) ===
SyncSessionLocal = sessionmaker(
    engine.sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# === 5. Base ===
from app.models.base import Base

# === 6. Helpers ===

def get_db_session():
    """Синхронная сессия для Celery/скриптов"""
    return SyncSessionLocal()

# 🔥 FIX: Простой async generator для FastAPI (БЕЗ @asynccontextmanager!)
async def get_async_db():
    """Асинхронная сессия для FastAPI endpoints"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# === 7. Init/Close ===
async def init_db():
    import asyncio
    from sqlalchemy import text
    try:
        async with asyncio.timeout(5):
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
                import app.models.user, app.models.task, app.models.usage_log, app.models.feature_flag
                await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database initialized")
    except Exception as e:
        if settings.DEBUG:
            logger.warning(f"⚠️ DB init skipped (dev): {e}")
        else:
            raise

async def close_db():
    await engine.dispose()
    logger.info("🔌 Database connections closed")