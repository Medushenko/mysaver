"""
Application settings via pydantic-settings
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "MySaver"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/mysaver"
    
    # Redis/Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # rclone RC API
    RCLONE_RC_ADDR: str = "http://127.0.0.1:5572"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-prod"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Глобальный экземпляр
settings = Settings()