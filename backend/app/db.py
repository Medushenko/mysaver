# app/db.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from contextlib import asynccontextmanager

# === 1. Force Async Driver (Критично для SQLAlchemy 2.0 Async) ===
# SQLAlchemy требует 'postgresql+asyncpg' для async движков.
# Мы автоматически преобразуем URL, если он начинается просто с 'postgresql://'.
DATABASE_URL = settings.DATABASE_URL
if not DATABASE_URL.startswith("postgresql+asyncpg"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# === 2. Async Engine ===
engine = create_async_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False  # Поставь True, чтобы видеть SQL-запросы в логах
)

# === 3. Async Session Factory ===
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# === 4. Sync Session Factory (для Celery/Скриптов) ===
# Используем синхронный движок, привязанный к async engine
SyncSessionLocal = sessionmaker(
    engine.sync_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

# === 5. Import Base from Models ===
# Критично: Мы должны использовать тот же Base, что и модели,
# чтобы init_db мог найти все зарегистрированные таблицы.
from app.models.base import Base

# === 6. Helper Functions ===

def get_db_session():
    """Возвращает синхронную сессию БД (для Celery/Скриптов)"""
    return SyncSessionLocal()

@asynccontextmanager
async def get_async_db():
    """Асинхронная сессия (для FastAPI)"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# === 7. Database Initialization ===
async def init_db():
    """Создаёт все таблицы на основе зарегистрированных моделей"""
    async with engine.begin() as conn:
        # Импортируем модели, чтобы они зарегистрировались в Base
        import app.models.user
        import app.models.task
        import app.models.usage_log
        import app.models.feature_flag
        await conn.run_sync(Base.metadata.create_all)