"""
Cache configuration for MySaver
Defines TTL, max size, and cleanup settings
"""
import os
from pathlib import Path
from app.config import settings

# Cache Time-To-Live in seconds (1 hour default)
CACHE_TTL = int(settings.get("CACHE_TTL", 3600))

# Maximum cache size in bytes (1GB default)
MAX_CACHE_SIZE = int(settings.get("MAX_CACHE_SIZE", 1024 * 1024 * 1024))

# Preview cache directory
PREVIEW_CACHE_DIR = Path(settings.get("PREVIEW_CACHE_DIR", "/tmp/mysaver/preview"))

# Rclone temporary files directory
RCLONE_TEMP_DIR = Path(settings.get("RCLONE_TEMP_DIR", "/tmp/rclone"))

# Reports retention period in days
REPORTS_RETENTION_DAYS = int(settings.get("REPORTS_RETENTION_DAYS", 30))

# Auto-cleanup schedule interval in hours
AUTO_CLEANUP_INTERVAL = int(settings.get("AUTO_CLEANUP_INTERVAL", 6))

# Complete cache configuration dictionary
CACHE_CONFIG = {
    "ttl": CACHE_TTL,
    "max_size": MAX_CACHE_SIZE,
    "preview_cache_dir": str(PREVIEW_CACHE_DIR),
    "rclone_temp_dir": str(RCLONE_TEMP_DIR),
    "reports_retention_days": REPORTS_RETENTION_DAYS,
    "auto_cleanup_interval": AUTO_CLEANUP_INTERVAL,
}


def ensure_cache_dirs():
    """Ensure cache directories exist"""
    PREVIEW_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    RCLONE_TEMP_DIR.mkdir(parents=True, exist_ok=True)
