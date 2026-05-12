# app/api/v1/tasks.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from app.db import get_async_db
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskResponse
from app.core.tasks import copy_task  # Наша Celery-задача

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_async_db),
    background_tasks: BackgroundTasks = None
):
    """
    Создать новую задачу копирования файлов.
    Возвращает задачу в статусе 'pending'.
    """
    # 1. Создаём запись в БД
    new_task = Task(
        source_provider=task_data.source_provider,
        source_path=task_data.source_path,
        dest_provider=task_data.dest_provider,
        dest_path=task_data.dest_path,
        options=task_data.options or {},
        status=TaskStatus.PENDING,
        bytes_planned=None,  # Будет рассчитано при сканировании
        bytes_done=0
    )
    
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    
    # 2. Отправляем задачу в Celery (в фоне)
    # Важно: передаём только сериализуемые данные
    background_tasks.add_task(
        copy_task.delay,
        task_id=str(new_task.id),
        source={
            "provider": task_data.source_provider,
            "path": task_data.source_path
        },
        destination={
            "provider": task_data.dest_provider,
            "path": task_data.dest_path
        },
        options=task_data.options or {}
    )
    
    logger.info(f"Task created: {new_task.id} → {task_data.source_path} -> {task_data.dest_path}")
    
    return new_task

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Получить текущий статус задачи по ID.
    """
    from sqlalchemy import select
    
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    return task