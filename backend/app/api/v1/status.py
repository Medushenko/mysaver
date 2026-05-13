# app/api/v1/status.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

router = APIRouter(tags=["status"])

# 🔥 FIX: Абсолютный путь к templates относительно этого файла
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@router.get("/build-status", response_class=HTMLResponse)
async def build_status(request: Request):
    """
    Временная страница для отслеживания прогресса разработки.
    """
    version = "0.2.0"
    try:
        version_file = BASE_DIR / "VERSION.txt"
        if version_file.exists():
            version = version_file.read_text().strip()
    except Exception as e:
        print(f"⚠️ Could not read VERSION.txt: {e}")
    
    # 🔥 Обновлённый чек-лист с итерациями 1.1 и 1.2
    iterations = [
        {"id": "0.1", "name": "БД + модели + миграции", "status": "done"},
        {"id": "0.2", "name": "StorageAdapter + rclone + Celery", "status": "done"},
        {"id": "1.1", "name": "Парсер ссылок + превью-дерево", "status": "done"},
        {"id": "1.2", "name": "Telegram-бот + отчёты + очистка кеша", "status": "current"},
        {"id": "2.1", "name": "Frontend (React/Vue) + интерактивное дерево", "status": "pending"},
    ]
    
    return templates.TemplateResponse(
        request,
        "build_status.html",
        {
            "version": version,
            "iterations": iterations,
            "meta_refresh": 30
        }
    )