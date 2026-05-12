from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # === Ядро приложения ===
    PROJECT_NAME: str = "MySaver"
    API_V1_STR: str = "/api/v1"
    
    # === База данных ===
    DATABASE_URL: str
    
    # === Redis / Celery ===
    REDIS_URL: str
    
    # === rclone ===
    RCLONE_RC_ADDR: str
    
    # === Безопасность ===
    SECRET_KEY: str = "dev-secret-key-change-in-prod"
    
    # === Порты (объявлены для доступа через settings.get()) ===
    API_PORT: int = 8000
    DB_PORT: int = 5432
    REDIS_PORT: int = 6379
    RCLONE_PORT: int = 5572
    
    # === Опциональные ===
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    def get(self, key: str, default=None):
        """Безопасное получение любой переменной"""
        # Сначала пробуем получить как объявленное поле
        value = getattr(self, key, None)
        if value is not None:
            return value
        # Потом — из os.environ (если экспортировано в оболочку)
        import os
        return os.getenv(key, default)

settings = Settings()