# app/main.py
"""
MySaver API — Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.db import init_db, close_db

# === Импорты роутеров ===
from app.api.v1 import tasks as tasks_router
from app.api.v1 import status as status_router
from app.api.v1 import parse as parse_router
from app.api.v1 import preview as preview_router


# === Lifecycle manager для БД ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация и закрытие ресурсов приложения"""
    # При старте: инициализируем БД (для тестов/разработки)
    # В продакшене используем только миграции Alembic
    if settings.DEBUG:
        await init_db()
    yield
    # При завершении: закрываем соединения
    await close_db()


# === Создание приложения ===
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Cloud file orchestrator — copy, sync, manage across storages",
    version="0.2.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# === CORS middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Настрой в продакшене!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Регистрация роутеров ===
app.include_router(tasks_router.router, prefix=f"{settings.API_V1_STR}/tasks", tags=["tasks"])
app.include_router(status_router.router, prefix=f"{settings.API_V1_STR}", tags=["status"])
app.include_router(parse_router.router, prefix=f"{settings.API_V1_STR}", tags=["parse"])
app.include_router(preview_router.router, prefix=f"{settings.API_V1_STR}", tags=["preview"])


# === Health check ===
@app.get("/health", tags=["health"])
async def health_check():
    """Проверка работоспособности API"""
    return {
        "status": "ok",
        "service": "mysaver-api",
        "version": "0.2.0"
    }


# === Root endpoint ===
@app.get("/", tags=["root"])
async def root():
    """Корневой эндпоинт с информацией об API"""
    return {
        "message": "MySaver API is running",
        "version": "0.2.0",
        "docs": "/docs",
        "health": "/health",
        "tasks_api": f"{settings.API_V1_STR}/tasks",
        "build_status": "/build-status"
    }


# === Для отладки: запуск через python app/main.py ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=settings.API_PORT,
        reload=True
    )