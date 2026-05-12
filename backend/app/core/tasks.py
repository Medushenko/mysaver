# app/core/tasks.py
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db_session
from app.models.task import Task, TaskStatus
from app.core.rclone_client import RcloneClient
from app.core.adapters.yandex import YandexDiskAdapter
from app.core.adapters.google import GoogleDriveAdapter
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, name="mysaver.copy_task", max_retries=3)
def copy_task(self, task_id: str, source: dict, destination: dict, options: dict):
    """
    Celery task для копирования файлов между хранилищами.
    
    :param task_id: UUID задачи в БД
    :param source: {provider: str, path: str}
    :param destination: {provider: str, path: str}
    :param options: {conflict_policy, verify_mode, tags, ...}
    """
    rclone = RcloneClient()
    
    try:
        # 1. Получаем сессию БД и задачу
        # (в реальном приложении здесь будет асинхронная сессия)
        # Для синхронного Celery worker используем blocking call
        import asyncio
        from app.db import engine
        from sqlalchemy.orm import sessionmaker
        
        SyncSession = sessionmaker(bind=engine.sync_engine)
        session = SyncSession()
        
        task = session.query(Task).filter(Task.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return {"error": "task_not_found"}
        
        # 2. Обновляем статус на "running"
        task.status = TaskStatus.RUNNING
        session.commit()
        
        # 3. Формируем строки для rclone: provider:path
        src_fs = f"{source['provider']}:{source['path']}"
        dst_fs = f"{destination['provider']}:{destination['path']}"
        
        # 4. Запускаем копирование через rclone RC API
        job_id = asyncio.run(rclone.start_copy(src_fs, dst_fs, options))
        logger.info(f"Started rclone job {job_id} for task {task_id}")
        
        # 5. Мониторим прогресс (упрощённо)
        # В продакшене здесь будет цикл с периодическим опросом job/status
        import time
        for _ in range(60):  # макс. 5 минут
            status = asyncio.run(rclone.get_job_status(job_id))
            if status.get("error"):
                raise Exception(f"rclone error: {status['error']}")
            
            # Обновляем прогресс в БД
            bytes_done = status.get("bytes", 0)
            task.bytes_done = bytes_done
            session.commit()
            
            if status.get("finished"):
                break
            time.sleep(5)
        
        # 6. Финализируем
        task.status = TaskStatus.SUCCESS
        task.completed_at = asyncio.get_event_loop().run_until_complete(
            asyncio.get_event_loop().create_task(asyncio.sleep(0))
        ) or __import__('datetime').datetime.utcnow()
        session.commit()
        
        return {"success": True, "job_id": job_id, "bytes_transferred": task.bytes_done}
        
    except Exception as exc:
        # Обработка ошибок и повторные попытки
        logger.error(f"Task {task_id} failed: {exc}")
        
        # Обновляем статус в БД
        try:
            SyncSession = sessionmaker(bind=engine.sync_engine)
            session = SyncSession()
            task = session.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = TaskStatus.FAILED
                task.error_reason = str(exc)
                session.commit()
        except:
            pass
        
        # Retry логика Celery
        raise self.retry(exc=exc, countdown=60, max_retries=3)
        
    finally:
        if 'session' in locals():
            session.close()