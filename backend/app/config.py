"""
Application settings via pydantic-settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # === Приложение ===
    PROJECT_NAME: str = "MySaver"
    API_V1_STR: str = "/api/v1"
    
    # === База данных ===
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/mysaver"
    
    # === Redis / Celery ===
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # === rclone ===
    RCLONE_RC_ADDR: str = "http://127.0.0.1:5572"
    
    # === Безопасность ===
    SECRET_KEY: str = "dev-secret-key-change-in-prod"
    
    # === Логирование ===
    LOG_LEVEL: str = "INFO"
    
    # === Порты (опционально, для справки) ===
    API_PORT: int = 8000
    DB_PORT: int = 5432
    REDIS_PORT: int = 6379
    RCLONE_PORT: int = 5572
    
    # 🔥 КЛЮЧЕВОЕ: разрешаем игнорировать неизвестные поля из .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # ← это исправляет ошибку
    )


# Глобальный экземпляр
settings = Settings()