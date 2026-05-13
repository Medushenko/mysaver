"""
Конфигурация тестов и фикстуры для MySaver.
Использует PostgreSQL для тестов (соответствует production окружению).
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
from app.config import settings

# Настройка pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

# Используем PostgreSQL для тестов (соответствие production)
# Переменная TEST_DATABASE_URL должна быть установлена в окружении
# Пример: postgresql+asyncpg://user:pass@localhost:5432/mysaver_test
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/mysaver_test"
)


@pytest.fixture(scope="session")
def event_loop_policy():
    """Используем стандартную политику event loop."""
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(scope="function")
async def db_session(event_loop_policy):
    """
    Фикстура для создания чистой БД перед каждым тестом.
    Использует PostgreSQL с транзакционным откатом для изоляции.
    """
    from app.models.base import Base
    
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True
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
        # Откатываем все изменения после теста (транзакционная изоляция)
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
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
