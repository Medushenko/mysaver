"""
Конфигурация тестов и фикстуры для MySaver.
Автоматически определяет окружение (SQLite для тестов, PostgreSQL для прода).
"""
import pytest
import asyncio
import os
import sys
from pathlib import Path

# Добавляем backend в path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

# Используем SQLite для изолированных тестов
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Настройка pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop_policy():
    """Используем стандартную политику event loop."""
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(scope="function")
async def db_session(event_loop_policy):
    """
    Фикстура для создания чистой БД перед каждым тестом.
    Использует SQLite в памяти для скорости.
    """
    from app.models.base import Base
    
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Создаем все таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Создаем сессию
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    session = async_session()
    
    try:
        yield session
    finally:
        await session.close()
        await engine.dispose()

@pytest.fixture
def sample_task_data():
    """Пример данных для создания задачи (соответствует реальной схеме TaskCreate)."""
    return {
        "source_provider": "yandex",
        "source_path": "/home/user/docs",
        "dest_provider": "google",
        "dest_path": "/backup/docs",
        "options": {"mode": "sync"}
    }
