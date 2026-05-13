"""
Schemas for report API responses
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class LogEntrySchema(BaseModel):
    """Single log entry in the report"""
    timestamp: str
    action: str
    source_path: str
    dest_path: str
    size: int
    message: Optional[str] = None


class StatsSchema(BaseModel):
    """Statistics for the report"""
    total_files: int = 0
    total_folders: int = 0
    total_size: int = 0
    copied_files: int = 0
    copied_size: int = 0
    skipped_files: int = 0
    failed_files: int = 0
    renamed_files: int = 0
    duration_seconds: float = 0.0
    speed_mb_per_sec: float = 0.0


class ReportSchema(BaseModel):
    """Complete report schema"""
    task_id: str
    status: str
    stats: StatsSchema
    logs: List[LogEntrySchema] = []
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    source_provider: str
    source_path: str
    dest_provider: str
    dest_path: str
    error_reason: Optional[str] = None
    conflict_policy: Optional[str] = None
    
    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    """API response for report endpoint"""
    task_id: str
    report: ReportSchema
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
