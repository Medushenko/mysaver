"""
Cache Cleaner for MySaver
Handles cleanup of preview cache, temp files, and old reports
"""
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

from app.core.cache.config import (
    CACHE_TTL,
    MAX_CACHE_SIZE,
    PREVIEW_CACHE_DIR,
    RCLONE_TEMP_DIR,
    REPORTS_RETENTION_DAYS,
    ensure_cache_dirs,
)
from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


class CacheCleaner:
    """
    Clean up various caches in MySaver
    """
    
    def __init__(self):
        # Ensure directories exist
        ensure_cache_dirs()
    
    def clean_preview_cache(self, task_id: Optional[str] = None) -> int:
        """
        Clean preview cache files
        
        Args:
            task_id: If provided, only clean cache for this specific task.
                    If None, clean all expired preview cache.
        
        Returns:
            Number of files/directories deleted
        """
        deleted_count = 0
        current_time = time.time()
        
        if not PREVIEW_CACHE_DIR.exists():
            return 0
        
        if task_id:
            # Clean specific task cache
            task_cache_path = PREVIEW_CACHE_DIR / task_id
            if task_cache_path.exists():
                try:
                    if task_cache_path.is_dir():
                        shutil.rmtree(task_cache_path)
                    else:
                        task_cache_path.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted preview cache for task {task_id}")
                except Exception as e:
                    logger.error(f"Failed to delete preview cache for {task_id}: {e}")
        else:
            # Clean all expired cache (older than CACHE_TTL)
            for item in PREVIEW_CACHE_DIR.iterdir():
                try:
                    mtime = item.stat().st_mtime
                    age = current_time - mtime
                    
                    if age > CACHE_TTL:
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                        deleted_count += 1
                        logger.debug(f"Deleted expired cache: {item.name}")
                except Exception as e:
                    logger.error(f"Failed to delete cache item {item}: {e}")
        
        return deleted_count
    
    def clean_rclone_temp(self) -> int:
        """
        Clean rclone temporary files
        
        Returns:
            Number of files/directories deleted
        """
        deleted_count = 0
        
        if not RCLONE_TEMP_DIR.exists():
            return 0
        
        try:
            # Delete all contents of temp directory
            for item in RCLONE_TEMP_DIR.iterdir():
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete temp item {item}: {e}")
            
            logger.info(f"Cleaned {deleted_count} rclone temp files")
        except Exception as e:
            logger.error(f"Failed to clean rclone temp directory: {e}")
        
        return deleted_count
    
    def clean_old_reports(self, days: int = None) -> int:
        """
        Clean old report files
        
        Args:
            days: Retention period in days. Uses REPORTS_RETENTION_DAYS if not specified.
        
        Returns:
            Number of files deleted
        """
        if days is None:
            days = REPORTS_RETENTION_DAYS
        
        deleted_count = 0
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Assuming reports are stored in a reports directory
        reports_dir = Path("/tmp/mysaver/reports")
        
        if not reports_dir.exists():
            return 0
        
        for report_file in reports_dir.iterdir():
            if not report_file.is_file():
                continue
            
            try:
                mtime = datetime.fromtimestamp(report_file.stat().st_mtime)
                
                if mtime < cutoff_date:
                    report_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old report: {report_file.name}")
            except Exception as e:
                logger.error(f"Failed to delete old report {report_file}: {e}")
        
        logger.info(f"Deleted {deleted_count} reports older than {days} days")
        return deleted_count
    
    def get_cache_stats(self) -> dict:
        """
        Get statistics about current cache usage
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {
            "preview_cache": {"size_bytes": 0, "file_count": 0},
            "rclone_temp": {"size_bytes": 0, "file_count": 0},
            "total_size_bytes": 0,
        }
        
        # Calculate preview cache stats
        if PREVIEW_CACHE_DIR.exists():
            size, count = self._calculate_dir_stats(PREVIEW_CACHE_DIR)
            stats["preview_cache"]["size_bytes"] = size
            stats["preview_cache"]["file_count"] = count
            stats["total_size_bytes"] += size
        
        # Calculate rclone temp stats
        if RCLONE_TEMP_DIR.exists():
            size, count = self._calculate_dir_stats(RCLONE_TEMP_DIR)
            stats["rclone_temp"]["size_bytes"] = size
            stats["rclone_temp"]["file_count"] = count
            stats["total_size_bytes"] += size
        
        # Add human-readable sizes
        stats["preview_cache"]["size_human"] = self._format_size(
            stats["preview_cache"]["size_bytes"]
        )
        stats["rclone_temp"]["size_human"] = self._format_size(
            stats["rclone_temp"]["size_bytes"]
        )
        stats["total_size_human"] = self._format_size(stats["total_size_bytes"])
        stats["max_size_human"] = self._format_size(MAX_CACHE_SIZE)
        stats["exceeds_max"] = stats["total_size_bytes"] > MAX_CACHE_SIZE
        
        return stats
    
    def _calculate_dir_stats(self, path: Path) -> tuple:
        """Calculate total size and file count for a directory"""
        total_size = 0
        file_count = 0
        
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                        file_count += 1
                    except (OSError, IOError):
                        pass
        except Exception as e:
            logger.error(f"Failed to calculate stats for {path}: {e}")
        
        return total_size, file_count
    
    def _format_size(self, bytes_value: int) -> str:
        """Format bytes to human-readable size"""
        if bytes_value is None or bytes_value == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024
        return f"{bytes_value:.2f} PB"
    
    def full_cleanup(self) -> dict:
        """
        Perform full cleanup of all cache types
        
        Returns:
            Dictionary with cleanup results
        """
        results = {
            "preview_cleaned": self.clean_preview_cache(),
            "rclone_temp_cleaned": self.clean_rclone_temp(),
            "old_reports_cleaned": self.clean_old_reports(),
        }
        results["total_cleaned"] = (
            results["preview_cleaned"] +
            results["rclone_temp_cleaned"] +
            results["old_reports_cleaned"]
        )
        
        logger.info(f"Full cleanup completed: {results['total_cleaned']} items deleted")
        return results


# Celery task for scheduled cleanup
@celery_app.task(bind=True, name="mysaver.clean_cache")
def scheduled_cleanup(self) -> dict:
    """
    Celery task for scheduled cache cleanup
    
    Can be called periodically via Celery beat
    """
    try:
        cleaner = CacheCleaner()
        results = cleaner.full_cleanup()
        
        logger.info(f"Scheduled cleanup completed: {results}")
        return results
    except Exception as e:
        logger.error(f"Scheduled cleanup failed: {e}")
        raise
