"""
Конфигурация и фикстуры для тестов Pytest.
Автоматически определяет среду (SQLite для локальной разработки, PostgreSQL для CI).
"""
import os
import sys
import pytest
import asyncio
from typing import AsyncGenerator, Generator

# Добавляем backend в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Пробуем импортировать компоненты БД, но не блокируем тесты если они недоступны
try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.database.base import Base
    DB_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    DB_AVAILABLE = False
    print(f"⚠️  База данных недоступна: {e}. Тесты БД будут пропущены.")

# Определение среды
IS_CI = os.getenv('CI', 'false').lower() == 'true'
IS_SANDBOX = os.getenv('AI_SANDBOX', 'false').lower() == 'true'

# Выбор базы данных
if IS_CI or IS_SANDBOX:
    # PostgreSQL для CI/CD или песочницы AI
    DB_URL = os.getenv(
        'TEST_DATABASE_URL',
        'postgresql+asyncpg://postgres:postgres@localhost:5432/mysaver_test'
    )
else:
    # SQLite для локальной разработки (macOS)
    DB_URL = 'sqlite+aiosqlite:///./test_mysaver.db'


@pytest.fixture(scope='session')
def event_loop() -> Generator:
    """Создание event loop для асинхронных тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def engine():
    """Создание движка БД для тестов."""
    connect_args = {}
    if DB_URL.startswith('sqlite'):
        connect_args['check_same_thread'] = False
    
    engine = create_async_engine(
        DB_URL,
        connect_args=connect_args,
        poolclass=StaticPool if DB_URL.startswith('sqlite') else None,
        echo=False  # Включить для отладки SQL запросов
    )
    
    # Создание таблиц
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Очистка после тестов
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()
    
    # Удаление файла SQLite если он существует
    if DB_URL.startswith('sqlite'):
        db_file = DB_URL.replace('sqlite+aiosqlite:///', '')
        if os.path.exists(db_file):
            os.remove(db_file)


@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Создание сессии БД для каждого теста."""
    session_maker = async_sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    session = session_maker()
    
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture
def override_get_db(db_session):
    """Фикстура для переопределения зависимости get_db в FastAPI."""
    async def _override_get_db():
        yield db_session
    
    return _override_get_db


@pytest.fixture(scope='session')
def api_base_url() -> str:
    """Базовый URL для API тестов."""
    port = os.getenv('TEST_API_PORT', '8000')
    return f'http://localhost:{port}'


@pytest.fixture
def test_task_data() -> dict:
    """Тестовые данные для создания задачи."""
    return {
        'name': 'Test Backup Task',
        'description': 'Test task for automated testing',
        'source_path': '/Users/test/source/docs',
        'destination_path': '/Volumes/Backup/docs',
        'config': {
            'exclude_patterns': ['*.tmp', '.DS_Store'],
            'verify_checksum': True
        }
    }


@pytest.fixture
def test_parse_data() -> dict:
    """Тестовые данные для парсинга ссылок."""
    return {
        'text': '''
        Проверка ссылок:
        1. Яндекс.Диск файл: https://yadi.sk/d/abc123file
        2. Яндекс.Диск папка: https://disk.yandex.ru/i/folder456
        3. Google Drive файл: https://drive.google.com/file/d/1xyz789/view
        4. Google Drive папка: https://drive.google.com/drive/folders/abc123
        5. Локальный путь Unix: /Users/name/Documents/report.pdf
        6. Локальный путь Windows: C:\\Users\\Documents\\file.txt
        '''
    }


@pytest.fixture
def sample_conflict_data() -> list:
    """Тестовые данные о конфликтах файлов."""
    return [
        {
            'source_path': '/source/file1.txt',
            'destination_path': '/dest/file1.txt',
            'size': 1024,
            'modified_time': '2023-10-27T10:00:00Z',
            'policy': 'skip'
        },
        {
            'source_path': '/source/file2.txt',
            'destination_path': '/dest/file2.txt',
            'size': 2048,
            'modified_time': '2023-10-27T11:00:00Z',
            'policy': 'overwrite'
        }
    ]
