"""
Schemas for cache API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional


class CacheCleanupRequest(BaseModel):
    """Request schema for cache cleanup endpoint"""
    preview: bool = True
    temp: bool = True
    reports: bool = False
    days: int = Field(default=30, ge=1, le=365)
    
    class Config:
        json_schema_extra = {
            "example": {
                "preview": True,
                "temp": True,
                "reports": False,
                "days": 30
            }
        }


class CacheStatsSchema(BaseModel):
    """Cache statistics schema"""
    preview_cache: dict
    rclone_temp: dict
    total_size_bytes: int
    total_size_human: str
    max_size_human: str
    exceeds_max: bool


class CacheCleanupResponse(BaseModel):
    """Response schema for cache cleanup endpoint"""
    preview_cleaned: int
    rclone_temp_cleaned: int
    old_reports_cleaned: int
    total_cleaned: int
    stats: Optional[CacheStatsSchema] = None
