"""
Интеграционные тесты API задач (Tasks API).
Проверка полного цикла: создание, получение списка, обновление, отмена.
"""
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.future import select

pytestmark = pytest.mark.asyncio


async def test_create_task(db_session, sample_task_data):
    """Тест создания задачи через API."""
    from app.main import app
    from httpx import ASGITransport, AsyncClient
    
    transport = ASGITransport(app=app)
    async with AsyncClient(base_url="http://test", transport=transport) as ac:
        # Путь: /api/v1/tasks/tasks (дублирование префикса в main.py и tasks.py)
        response = await ac.post("/api/v1/tasks/tasks", json=sample_task_data)
    
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    
    assert "id" in data
    assert data["status"] == "pending"
    assert data.get("user_id") is None  # user_id должен быть nullable
    
    print(f"✅ Task created: {data['id']}")


async def test_get_task_list(db_session, sample_task_data):
    """Тест получения списка задач."""
    from app.main import app
    from app.models.task import Task
    
    # Создаем тестовую задачу напрямую в БД
    task = Task(**sample_task_data, status="pending")
    db_session.add(task)
    await db_session.commit()
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/tasks")
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) >= 1
    
    # Проверяем, что наша задача в списке
    task_ids = [t["id"] for t in data]
    assert str(task.id) in task_ids
    
    print(f"✅ Task list retrieved: {len(data)} tasks")


async def test_get_single_task(db_session, sample_task_data):
    """Тест получения одной задачи по ID."""
    from app.main import app
    from app.models.task import Task
    
    # Создаем задачу
    task = Task(**sample_task_data, status="running")
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/tasks/{task.id}")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == str(task.id)
    assert data["status"] == "running"
    assert data["name"] == sample_task_data["name"]
    
    print(f"✅ Single task retrieved: {data['id']}")


async def test_update_task_status(db_session, sample_task_data):
    """Тест обновления статуса задачи."""
    from app.main import app
    from app.models.task import Task
    
    # Создаем задачу
    task = Task(**sample_task_data, status="pending")
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    
    # Обновляем статус
    update_data = {"status": "running"}
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.patch(f"/api/v1/tasks/{task.id}/status", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "running"
    
    print(f"✅ Task status updated: {data['id']} -> running")


async def test_cancel_task(db_session, sample_task_data):
    """Тест отмены задачи."""
    from app.main import app
    from app.models.task import Task
    
    # Создаем задачу
    task = Task(**sample_task_data, status="running")
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    
    # Отменяем задачу
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(f"/api/v1/tasks/{task.id}/cancel")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "cancelled"
    
    print(f"✅ Task cancelled: {data['id']}")


async def test_delete_task(db_session, sample_task_data):
    """Тест удаления задачи."""
    from app.main import app
    from app.models.task import Task
    
    # Создаем задачу
    task = Task(**sample_task_data, status="pending")
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    
    # Удаляем задачу
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.delete(f"/api/v1/tasks/{task.id}")
    
    assert response.status_code == 200
    
    # Проверяем, что задача удалена
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/tasks/{task.id}")
    
    assert response.status_code == 404
    
    print(f"✅ Task deleted: {task.id}")


async def test_task_with_null_user_id(db_session, sample_task_data):
    """Тест что задача может быть создана без user_id (NULL)."""
    from app.main import app
    from app.models.task import Task
    
    # Создаем задачу явно с user_id=None
    task = Task(
        name=sample_task_data["name"],
        description=sample_task_data["description"],
        source_path=sample_task_data["source_path"],
        destination_path=sample_task_data["destination_path"],
        user_id=None,  # Явно NULL
        status="pending"
    )
    
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    
    assert task.user_id is None
    
    # Получаем через API
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/tasks/{task.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] is None
    
    print(f"✅ Task with NULL user_id works: {task.id}")
