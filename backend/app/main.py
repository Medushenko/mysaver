"""
MySaver API Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Создаём экземпляр приложения — именно его ищет uvicorn: app.main:app
app = FastAPI(
    title="MySaver API",
    description="Cloud file orchestrator",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware (настрой в продакшене)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Проверка работоспособности API"""
    return {
        "status": "ok",
        "service": "mysaver-api",
        "version": "0.1.0"
    }

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "MySaver API is running",
        "docs": "/docs",
        "health": "/health"
    }