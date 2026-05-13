"""
Cache API endpoints for MySaver
DELETE /api/v1/cache - Clean up cache files
GET /api/v1/cache/stats - Get cache statistics
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.schemas.cache import (
    CacheCleanupRequest,
    CacheCleanupResponse,
    CacheStatsSchema
)
from app.core.cache.cleaner import CacheCleaner

router = APIRouter()


@router.delete("/cache", response_model=CacheCleanupResponse)
async def cleanup_cache(
    preview: bool = Query(default=True, description="Clean preview cache"),
    temp: bool = Query(default=True, description="Clean rclone temp files"),
    reports: bool = Query(default=False, description="Clean old reports"),
    days: int = Query(default=30, ge=1, le=365, description="Reports retention days"),
):
    """
    Clean up cache files
    
    Parameters:
    - **preview**: Clean preview cache (default: True)
    - **temp**: Clean rclone temporary files (default: True)
    - **reports**: Clean old reports (default: False)
    - **days**: Retention period for reports in days (default: 30)
    
    Returns number of items cleaned for each category.
    """
    try:
        cleaner = CacheCleaner()
        
        results = {
            "preview_cleaned": 0,
            "rclone_temp_cleaned": 0,
            "old_reports_cleaned": 0,
            "total_cleaned": 0,
        }
        
        if preview:
            results["preview_cleaned"] = cleaner.clean_preview_cache()
        
        if temp:
            results["rclone_temp_cleaned"] = cleaner.clean_rclone_temp()
        
        if reports:
            results["old_reports_cleaned"] = cleaner.clean_old_reports(days=days)
        
        results["total_cleaned"] = (
            results["preview_cleaned"] +
            results["rclone_temp_cleaned"] +
            results["old_reports_cleaned"]
        )
        
        # Get updated stats
        stats_data = cleaner.get_cache_stats()
        stats = CacheStatsSchema(**stats_data)
        
        return CacheCleanupResponse(
            **results,
            stats=stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache cleanup failed: {str(e)}")


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get current cache statistics
    
    Returns information about cache usage including:
    - Preview cache size and file count
    - Rclone temp files size and count
    - Total cache size
    - Whether cache exceeds maximum allowed size
    """
    try:
        cleaner = CacheCleaner()
        stats_data = cleaner.get_cache_stats()
        
        return CacheStatsSchema(**stats_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@router.post("/cache/cleanup")
async def cleanup_cache_with_body(request: CacheCleanupRequest):
    """
    Clean up cache with request body parameters
    
    Alternative endpoint that accepts JSON body instead of query parameters.
    """
    try:
        cleaner = CacheCleaner()
        
        results = {
            "preview_cleaned": 0,
            "rclone_temp_cleaned": 0,
            "old_reports_cleaned": 0,
            "total_cleaned": 0,
        }
        
        if request.preview:
            results["preview_cleaned"] = cleaner.clean_preview_cache()
        
        if request.temp:
            results["rclone_temp_cleaned"] = cleaner.clean_rclone_temp()
        
        if request.reports:
            results["old_reports_cleaned"] = cleaner.clean_old_reports(days=request.days)
        
        results["total_cleaned"] = (
            results["preview_cleaned"] +
            results["rclone_temp_cleaned"] +
            results["old_reports_cleaned"]
        )
        
        # Get updated stats
        stats_data = cleaner.get_cache_stats()
        stats = CacheStatsSchema(**stats_data)
        
        return CacheCleanupResponse(
            **results,
            stats=stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache cleanup failed: {str(e)}")
