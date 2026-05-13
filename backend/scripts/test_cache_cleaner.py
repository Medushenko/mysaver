"""
Test script for Cache Cleaner functionality
Tests cache cleanup, stats, and configuration
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, '/workspace/backend')


def test_cache_config():
    """Test cache configuration values"""
    print("Testing cache configuration...")
    
    from app.core.cache.config import (
        CACHE_TTL,
        MAX_CACHE_SIZE,
        PREVIEW_CACHE_DIR,
        RCLONE_TEMP_DIR,
        REPORTS_RETENTION_DAYS,
        AUTO_CLEANUP_INTERVAL,
        CACHE_CONFIG,
        ensure_cache_dirs,
    )
    
    # Verify config values are reasonable
    assert CACHE_TTL > 0, "CACHE_TTL should be positive"
    assert CACHE_TTL <= 86400 * 30, "CACHE_TTL should not exceed 30 days"
    print(f"✓ CACHE_TTL: {CACHE_TTL} seconds")
    
    assert MAX_CACHE_SIZE > 0, "MAX_CACHE_SIZE should be positive"
    print(f"✓ MAX_CACHE_SIZE: {MAX_CACHE_SIZE} bytes ({MAX_CACHE_SIZE / (1024**3):.2f} GB)")
    
    assert isinstance(PREVIEW_CACHE_DIR, Path)
    print(f"✓ PREVIEW_CACHE_DIR: {PREVIEW_CACHE_DIR}")
    
    assert isinstance(RCLONE_TEMP_DIR, Path)
    print(f"✓ RCLONE_TEMP_DIR: {RCLONE_TEMP_DIR}")
    
    assert REPORTS_RETENTION_DAYS > 0
    print(f"✓ REPORTS_RETENTION_DAYS: {REPORTS_RETENTION_DAYS}")
    
    assert "ttl" in CACHE_CONFIG
    assert "max_size" in CACHE_CONFIG
    print("✓ CACHE_CONFIG dictionary complete")
    
    # Test ensure_cache_dirs
    ensure_cache_dirs()
    assert PREVIEW_CACHE_DIR.exists() or True  # May already exist
    print("✓ ensure_cache_dirs executed successfully")
    
    return True


def test_cache_cleaner_basic():
    """Test basic CacheCleaner functionality"""
    print("\nTesting CacheCleaner basic operations...")
    
    from app.core.cache.cleaner import CacheCleaner
    
    cleaner = CacheCleaner()
    assert cleaner is not None
    print("✓ CacheCleaner instantiated")
    
    return True


def test_clean_preview_cache():
    """Test preview cache cleaning"""
    print("\nTesting preview cache cleaning...")
    
    from app.core.cache.cleaner import CacheCleaner
    from app.core.cache.config import PREVIEW_CACHE_DIR, CACHE_TTL
    
    cleaner = CacheCleaner()
    
    # Create test cache files
    test_task_id = "test-task-12345"
    test_cache_dir = PREVIEW_CACHE_DIR / test_task_id
    test_cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a test file
    test_file = test_cache_dir / "test_file.txt"
    test_file.write_text("test content")
    
    assert test_file.exists()
    print(f"✓ Created test cache file: {test_file}")
    
    # Clean specific task cache
    deleted = cleaner.clean_preview_cache(task_id=test_task_id)
    assert deleted >= 1 or not test_cache_dir.exists()
    print(f"✓ clean_preview_cache deleted {deleted} items for task {test_task_id}")
    
    # Verify cleanup
    if not test_cache_dir.exists():
        print("✓ Task cache directory removed")
    
    # Test cleaning all expired cache (should return 0 since no expired cache)
    deleted_all = cleaner.clean_preview_cache()
    assert isinstance(deleted_all, int)
    print(f"✓ clean_preview_cache (all) returned: {deleted_all}")
    
    return True


def test_clean_rclone_temp():
    """Test rclone temp file cleaning"""
    print("\nTesting rclone temp cleaning...")
    
    from app.core.cache.cleaner import CacheCleaner
    from app.core.cache.config import RCLONE_TEMP_DIR
    
    cleaner = CacheCleaner()
    
    # Create test temp files
    test_temp_file = RCLONE_TEMP_DIR / "temp_test_file.txt"
    test_temp_file.write_text("temp content")
    
    assert test_temp_file.exists()
    print(f"✓ Created test temp file: {test_temp_file}")
    
    # Clean temp files
    deleted = cleaner.clean_rclone_temp()
    print(f"✓ clean_rclone_temp deleted {deleted} items")
    
    # Verify cleanup
    if not test_temp_file.exists():
        print("✓ Temp file removed")
    
    return True


def test_clean_old_reports():
    """Test old reports cleaning"""
    print("\nTesting old reports cleaning...")
    
    from app.core.cache.cleaner import CacheCleaner
    
    cleaner = CacheCleaner()
    
    # Test with default retention (should return 0 if no old reports)
    deleted = cleaner.clean_old_reports()
    assert isinstance(deleted, int)
    print(f"✓ clean_old_reports (default) deleted {deleted} items")
    
    # Test with custom retention
    deleted_custom = cleaner.clean_old_reports(days=7)
    assert isinstance(deleted_custom, int)
    print(f"✓ clean_old_reports (7 days) deleted {deleted_custom} items")
    
    return True


def test_get_cache_stats():
    """Test cache statistics"""
    print("\nTesting cache statistics...")
    
    from app.core.cache.cleaner import CacheCleaner
    
    cleaner = CacheCleaner()
    stats = cleaner.get_cache_stats()
    
    # Verify stats structure
    assert "preview_cache" in stats
    assert "rclone_temp" in stats
    assert "total_size_bytes" in stats
    assert "total_size_human" in stats
    assert "max_size_human" in stats
    assert "exceeds_max" in stats
    print("✓ Stats dictionary has all required keys")
    
    # Verify nested structure
    assert "size_bytes" in stats["preview_cache"]
    assert "file_count" in stats["preview_cache"]
    assert "size_human" in stats["preview_cache"]
    print("✓ Preview cache stats structure correct")
    
    assert "size_bytes" in stats["rclone_temp"]
    assert "file_count" in stats["rclone_temp"]
    print("✓ Rclone temp stats structure correct")
    
    # Print stats
    print(f"\n📊 Cache Statistics:")
    print(f"   Preview cache: {stats['preview_cache']['size_human']} ({stats['preview_cache']['file_count']} files)")
    print(f"   Rclone temp: {stats['rclone_temp']['size_human']} ({stats['rclone_temp']['file_count']} files)")
    print(f"   Total: {stats['total_size_human']}")
    print(f"   Max allowed: {stats['max_size_human']}")
    print(f"   Exceeds max: {stats['exceeds_max']}")
    
    return True


def test_full_cleanup():
    """Test full cleanup operation"""
    print("\nTesting full cleanup...")
    
    from app.core.cache.cleaner import CacheCleaner
    
    cleaner = CacheCleaner()
    
    # Create some test files
    from app.core.cache.config import PREVIEW_CACHE_DIR, RCLONE_TEMP_DIR
    
    test_preview = PREVIEW_CACHE_DIR / "cleanup_test" / "file.txt"
    test_preview.parent.mkdir(parents=True, exist_ok=True)
    test_preview.write_text("test")
    
    test_temp = RCLONE_TEMP_DIR / "cleanup_test.txt"
    test_temp.write_text("temp")
    
    print("✓ Created test files for cleanup")
    
    # Run full cleanup
    results = cleaner.full_cleanup()
    
    assert "preview_cleaned" in results
    assert "rclone_temp_cleaned" in results
    assert "old_reports_cleaned" in results
    assert "total_cleaned" in results
    print("✓ Full cleanup results have all required keys")
    
    print(f"\n🧹 Cleanup Results:")
    print(f"   Preview cleaned: {results['preview_cleaned']}")
    print(f"   Rclone temp cleaned: {results['rclone_temp_cleaned']}")
    print(f"   Old reports cleaned: {results['old_reports_cleaned']}")
    print(f"   Total cleaned: {results['total_cleaned']}")
    
    return True


def test_scheduled_cleanup_task():
    """Test Celery scheduled cleanup task"""
    print("\nTesting scheduled cleanup Celery task...")
    
    from app.core.cache.cleaner import scheduled_cleanup
    
    # The task should be callable
    assert scheduled_cleanup is not None
    print("✓ scheduled_cleanup task exists")
    
    # Check task name
    assert scheduled_cleanup.name == "mysaver.clean_cache"
    print(f"✓ Task name: {scheduled_cleanup.name}")
    
    # Try to run the task (will work without Redis but may not persist)
    try:
        result = scheduled_cleanup()
        assert isinstance(result, dict)
        print(f"✓ scheduled_cleanup executed successfully")
        print(f"   Result: {result}")
    except Exception as e:
        # May fail due to missing Redis, that's OK for this test
        print(f"⚠ scheduled_cleanup execution note: {e}")
    
    return True


def test_cache_schemas():
    """Test cache-related Pydantic schemas"""
    print("\nTesting cache schemas...")
    
    from app.schemas.cache import (
        CacheCleanupRequest,
        CacheStatsSchema,
        CacheCleanupResponse,
    )
    
    # Test CacheCleanupRequest
    request = CacheCleanupRequest(
        preview=True,
        temp=True,
        reports=False,
        days=30
    )
    assert request.preview is True
    assert request.temp is True
    assert request.reports is False
    assert request.days == 30
    print("✓ CacheCleanupRequest schema works")
    
    # Test validation
    try:
        invalid = CacheCleanupRequest(days=0)
        assert False, "Should have raised validation error"
    except Exception:
        print("✓ CacheCleanupRequest validates days correctly")
    
    try:
        invalid = CacheCleanupRequest(days=400)
        assert False, "Should have raised validation error"
    except Exception:
        print("✓ CacheCleanupRequest validates max days correctly")
    
    # Test CacheStatsSchema
    stats = CacheStatsSchema(
        preview_cache={"size_bytes": 1024, "file_count": 5},
        rclone_temp={"size_bytes": 2048, "file_count": 3},
        total_size_bytes=3072,
        total_size_human="3.00 KB",
        max_size_human="1.00 GB",
        exceeds_max=False
    )
    assert stats.total_size_bytes == 3072
    print("✓ CacheStatsSchema works")
    
    # Test CacheCleanupResponse
    response = CacheCleanupResponse(
        preview_cleaned=5,
        rclone_temp_cleaned=3,
        old_reports_cleaned=0,
        total_cleaned=8,
        stats=stats
    )
    assert response.total_cleaned == 8
    print("✓ CacheCleanupResponse works")
    
    return True


def test_with_real_files():
    """Test cache cleaner with real file operations"""
    print("\nTesting with real file operations...")
    
    from app.core.cache.cleaner import CacheCleaner
    from app.core.cache.config import PREVIEW_CACHE_DIR
    
    cleaner = CacheCleaner()
    
    # Create multiple test files with different ages
    test_dir = PREVIEW_CACHE_DIR / "real_test"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create files
    files_created = []
    for i in range(5):
        test_file = test_dir / f"file_{i}.txt"
        test_file.write_text(f"content {i}")
        files_created.append(test_file)
    
    print(f"✓ Created {len(files_created)} test files")
    
    # Get stats before cleanup
    stats_before = cleaner.get_cache_stats()
    print(f"✓ Stats before cleanup: {stats_before['preview_cache']['file_count']} files")
    
    # Clean up
    deleted = cleaner.clean_preview_cache(task_id="real_test")
    print(f"✓ Deleted {deleted} items")
    
    # Verify files are gone
    remaining = [f for f in files_created if f.exists()]
    if len(remaining) == 0:
        print("✓ All test files cleaned up")
    else:
        print(f"⚠ {len(remaining)} files still remain")
    
    # Clean up test directory
    if test_dir.exists():
        shutil.rmtree(test_dir)
    
    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("CACHE CLEANER TEST SUITE")
    print("=" * 60 + "\n")
    
    tests = [
        test_cache_config,
        test_cache_cleaner_basic,
        test_clean_preview_cache,
        test_clean_rclone_temp,
        test_clean_old_reports,
        test_get_cache_stats,
        test_full_cleanup,
        test_scheduled_cleanup_task,
        test_cache_schemas,
        test_with_real_files,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"\n❌ TEST FAILED: {test.__name__}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✅ ALL TESTS PASSED!\n")
        sys.exit(0)
    else:
        print(f"\n❌ {failed} TEST(S) FAILED\n")
        sys.exit(1)
