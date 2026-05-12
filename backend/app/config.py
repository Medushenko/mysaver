# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # === Ядро приложения (обязательные, типизированные) ===
    PROJECT_NAME: str = "MySaver"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str
    REDIS_URL: str
    RCLONE_RC_ADDR: str
    SECRET_KEY: str = "dev-secret-key-change-in-prod"
    
    # === Опциональные с дефолтами ===
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    
    # 🔥 Ключевая настройка: игнорировать неизвестные поля из .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # === Удобный доступ к «свободным» переменным ===
    def get(self, key: str, default=None):
        return getattr(self, key, default) or __import__('os').environ.get(key, default)

settings = Settings()