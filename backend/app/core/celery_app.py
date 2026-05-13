from celery import Celery
from app.config import settings

# Используем SQLite как бэкенд для тестов, если Redis недоступен
import os
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

if TEST_MODE:
    # Для тестов используем простой бэкенд в памяти
    celery_app = Celery(
        "mysaver_tasks",
        broker="memory://",
        backend="cache+memory://",
        include=["app.core.tasks"]
    )
else:
    celery_app = Celery(
        "mysaver_tasks",
        broker=settings.REDIS_URL,
        backend=settings.REDIS_URL,
        include=["app.core.tasks"]
    )

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    task_always_eager=TEST_MODE,  # Выполнять задачи синхронно в тестах
    task_eager_propagates=TEST_MODE,
)