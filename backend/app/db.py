"""
Database configuration and session management
Async SQLAlchemy 2.0 with PostgreSQL
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine
from sqlalchemy.pool import NullPool
from app.config import settings
from app.models.base import Base


# Async engine for application runtime
async_engine: AsyncEngine | None = None
async_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_database_url() -> str:
    """Get database URL from settings"""
    return settings.DATABASE_URL


def init_db_engine(database_url: str | None = None) -> None:
    """Initialize async engine and session maker"""
    global async_engine, async_session_maker
    
    if database_url is None:
        database_url = get_database_url()
    
    # Convert postgresql:// to postgresql+asyncpg:// if needed
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    async_engine = create_async_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False,
    )
    
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def init_db() -> None:
    """Create all tables (for testing only, not for production)"""
    if async_engine is None:
        init_db_engine()
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections"""
    if async_engine:
        await async_engine.dispose()


async def get_db() -> AsyncSession:
    """Dependency for FastAPI - yields async session"""
    if async_session_maker is None:
        init_db_engine()
    
    async with async_session_maker() as session:  # type: ignore[arg-type]
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()