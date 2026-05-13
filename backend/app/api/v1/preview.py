# app/api/v1/preview.py
"""
API endpoints для предпросмотра дерева файлов перед копированием.
Итерация 1.1: Парсер ссылок + Превью-дерево + Конфликты
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import logging

from app.db import get_async_db
from app.models.task import Task
from app.schemas.preview import PreviewResponse, PreviewNode, StatsSchema

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/preview", tags=["preview"])


@router.get("/{task_id}", response_model=PreviewResponse)
async def get_preview(
    task_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Получить превью-дерево файлов для задачи копирования.
    """
    try:
        # 1. Находим задачу в БД
        result = await db.execute(
            select(Task).where(Task.id == task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )
        
        # 2. Если нет распарсенных ссылок — возвращаем пустое дерево
        if not task.parsed_links:
            return PreviewResponse(
                task_id=task_id,
                tree=PreviewNode(
                    id="root",
                    name="No links parsed",
                    type="folder",
                    size=0,
                    children=[],
                    checked=True
                ),
                stats={"total_files": 0, "total_size": 0, "total_folders": 0}
            )
        
        # 3. Заглушка: возвращаем простое дерево (реальная логика — в TreeBuilder)
        # Для теста: берём первую ссылку и создаём фейковое дерево
        link = task.parsed_links[0] if isinstance(task.parsed_links, list) else task.parsed_links
        link_name = link.get("url", "unknown").split("/")[-1] if isinstance(link, dict) else "unknown"
        
        tree = PreviewNode(
            id=str(task_id),
            name=link_name,
            type="folder",
            size=0,
            children=[
                PreviewNode(
                    id=f"{task_id}-file1",
                    name="example.txt",
                    type="file",
                    size=1024,
                    children=[],
                    checked=True
                )
            ],
            checked=True
        )
        
        return PreviewResponse(
            task_id=task_id,
            tree=tree,
            stats={"total_files": 1, "total_size": 1024, "total_folders": 1}
        )
        
    except HTTPException:
        # Пробрасываем преднамеренные ошибки (404 и т.д.)
        raise
    except Exception as e:
        # Логируем и возвращаем 500 с деталями (только в DEBUG!)
        logger.error(f"Preview error for task {task_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview generation failed: {str(e)}"
        )