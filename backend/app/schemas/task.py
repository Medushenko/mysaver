# app/schemas/task.py
from pydantic import BaseModel, Field, computed_field  # 🔥 FIX: Import computed_field
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any

class TaskCreate(BaseModel):
    """Схема для создания новой задачи копирования"""
    source_provider: str = Field(..., min_length=1, example="yandex")
    source_path: str = Field(..., min_length=1, example="/docs/project")
    dest_provider: str = Field(..., min_length=1, example="google")
    dest_path: str = Field(..., min_length=1, example="/backup/project")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_provider": "yandex",
                "source_path": "/docs",
                "dest_provider": "google", 
                "dest_path": "/backup",
                "options": {"conflict_policy": "skip_identical"}
            }
        }

class TaskResponse(BaseModel):
    """Схема ответа с информацией о задаче"""
    id: UUID
    status: str  # pending, running, success, partial, failed
    bytes_planned: Optional[int] = None
    bytes_done: Optional[int] = None
    error_reason: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    # 🔥 FIX: Добавлено вычисляемое поле progress_pct
    @computed_field
    @property
    def progress_pct(self) -> float:
        if not self.bytes_planned:
            return 0.0
        return round((self.bytes_done or 0) / self.bytes_planned * 100, 2)
    
    class Config:
        from_attributes = True  # Для работы с SQLAlchemy моделями