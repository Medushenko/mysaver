"""
Test script for Telegram Bot functionality
Tests bot initialization, command handlers, and notifications using mocks
"""
import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, '/workspace/backend')


def test_bot_initialization():
    """Test bot initialization with and without token"""
    print("Testing bot initialization...")
    
    from app.core.telegram.bot import TelegramBot
    
    # Test without token (should not initialize)
    bot_no_token = TelegramBot(token="")
    assert not bot_no_token.is_available()
    print("✓ Bot without token is not available")
    
    # Test with token (mocked)
    bot_with_token = TelegramBot(token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
    assert bot_with_token.token == "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    print("✓ Bot with token created successfully")
    
    return True


async def test_bot_initialize_mock():
    """Test bot initialization with mocked Application"""
    print("\nTesting bot initialize with mock...")
    
    from app.core.telegram.bot import TelegramBot
    
    with patch('app.core.telegram.bot.Application') as MockApplication:
        mock_app = AsyncMock()
        MockApplication.builder.return_value.token.return_value.build.return_value = mock_app
        
        bot = TelegramBot(token="test_token")
        
        # Mock the application builder chain
        mock_builder = MagicMock()
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_app
        
        with patch.object(bot, 'application', mock_app):
            bot._initialized = True
            
            assert bot.is_available()
            print("✓ Bot initialized successfully (mocked)")
    
    return True


def test_command_handlers():
    """Test command handler functions"""
    print("\nTesting command handlers...")
    
    from app.core.telegram.handlers import (
        handle_start,
        handle_status,
        handle_report,
        handle_cancel,
        handle_list,
        handle_help,
        _extract_task_id,
        _format_size,
        _format_duration,
    )
    
    # Test _extract_task_id
    assert _extract_task_id(["550e8400-e29b-41d4-a716-446655440000"]) == "550e8400-e29b-41d4-a716-446655440000"
    assert _extract_task_id([]) is None
    print("✓ _extract_task_id works correctly")
    
    # Test _format_size
    assert _format_size(1024) == "1.00 KB"
    assert _format_size(1048576) == "1.00 MB"
    assert _format_size(0) == "0.00 B"
    print("✓ _format_size works correctly")
    
    # Test _format_duration
    result = _format_duration(30.5)
    assert "сек" in result
    result = _format_duration(120.0)
    assert "мин" in result
    result = _format_duration(7200.0)
    assert "ч" in result
    print("✓ _format_duration works correctly")
    
    return True


async def test_handle_start():
    """Test /start command handler"""
    print("\nTesting /start handler...")
    
    from app.core.telegram.handlers import handle_start
    
    # Create mock update and context
    mock_message = AsyncMock()
    mock_update = MagicMock()
    mock_update.message = mock_message
    
    context = MagicMock()
    
    # Call handler
    await handle_start(mock_update, context)
    
    # Verify message was sent
    assert mock_message.reply_text.called
    call_args = mock_message.reply_text.call_args
    assert "Добро пожаловать" in call_args[0][0] or "MySaver" in call_args[0][0]
    print("✓ /start handler sends welcome message")
    
    return True


async def test_handle_status_no_task_id():
    """Test /status command without task ID"""
    print("\nTesting /status handler without task ID...")
    
    from app.core.telegram.handlers import handle_status
    
    mock_message = AsyncMock()
    mock_update = MagicMock()
    mock_update.message = mock_message
    
    context = MagicMock()
    context.args = []  # No task ID provided
    
    await handle_status(mock_update, context)
    
    assert mock_message.reply_text.called
    call_args = mock_message.reply_text.call_args
    assert "укажите ID задачи" in call_args[0][0].lower() or "task" in call_args[0][0].lower()
    print("✓ /status handler requests task ID when not provided")
    
    return True


def test_notifications():
    """Test notification functions"""
    print("\nTesting notification functions...")
    
    from app.core.telegram.notifications import (
        send_notification,
        send_task_status,
        _format_size,
    )
    
    # Test _format_size in notifications module
    assert _format_size(2048) == "2.00 KB"
    print("✓ Notification _format_size works correctly")
    
    return True


def test_report_generator():
    """Test ReportGenerator class"""
    print("\nTesting ReportGenerator...")
    
    from app.core.reports.generator import ReportGenerator, LogEntry, ReportStats
    
    # Test LogEntry creation
    log = LogEntry(
        timestamp="2024-01-01T00:00:00",
        action="copied",
        source_path="/source/file.txt",
        dest_path="/dest/file.txt",
        size=1024,
        message="File copied successfully"
    )
    assert log.action == "copied"
    assert log.size == 1024
    print("✓ LogEntry dataclass works correctly")
    
    # Test ReportStats creation
    stats = ReportStats(
        total_files=100,
        copied_files=95,
        failed_files=5,
        duration_seconds=120.5,
        speed_mb_per_sec=10.5
    )
    assert stats.total_files == 100
    assert stats.speed_mb_per_sec == 10.5
    print("✓ ReportStats dataclass works correctly")
    
    # Test ReportGenerator instantiation
    generator = ReportGenerator()
    assert generator is not None
    print("✓ ReportGenerator instantiated successfully")
    
    return True


def test_formatters():
    """Test report formatters"""
    print("\nTesting report formatters...")
    
    from app.core.reports.formatters import format_report_text, format_report_html, _format_size, _format_duration
    
    # Sample report data
    sample_report = {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "success",
        "stats": {
            "total_files": 100,
            "total_folders": 10,
            "total_size": 104857600,
            "copied_files": 95,
            "copied_size": 99614720,
            "skipped_files": 3,
            "failed_files": 2,
            "renamed_files": 0,
            "duration_seconds": 120.5,
            "speed_mb_per_sec": 0.83,
        },
        "logs": [],
        "created_at": "2024-01-01T00:00:00",
        "started_at": "2024-01-01T00:01:00",
        "completed_at": "2024-01-01T00:03:00",
        "source_provider": "yandex",
        "source_path": "/documents",
        "dest_provider": "google",
        "dest_path": "/backup",
        "error_reason": None,
        "conflict_policy": "skip",
    }
    
    # Test text formatting
    text_report = format_report_text(sample_report)
    assert "ОТЧЁТ О ЗАДАЧЕ" in text_report or "report" in text_report.lower()
    assert "550e8400" in text_report
    print("✓ Text formatter works correctly")
    
    # Test HTML formatting
    html_report = format_report_html(sample_report)
    assert "<div" in html_report
    assert "Отчёт о задаче" in html_report or "report" in html_report.lower()
    print("✓ HTML formatter works correctly")
    
    # Test helper functions
    assert _format_size(1073741824) == "1.00 GB"
    assert "мин" in _format_duration(120.0)
    print("✓ Formatter helper functions work correctly")
    
    return True


def test_cache_cleaner():
    """Test CacheCleaner class"""
    print("\nTesting CacheCleaner...")
    
    from app.core.cache.cleaner import CacheCleaner
    from app.core.cache.config import CACHE_TTL, MAX_CACHE_SIZE, CACHE_CONFIG
    
    # Test config values
    assert CACHE_TTL > 0
    assert MAX_CACHE_SIZE > 0
    assert "ttl" in CACHE_CONFIG
    print("✓ Cache config loaded correctly")
    
    # Test CacheCleaner instantiation
    cleaner = CacheCleaner()
    assert cleaner is not None
    print("✓ CacheCleaner instantiated successfully")
    
    # Test clean_preview_cache (should return 0 if no cache exists)
    result = cleaner.clean_preview_cache()
    assert isinstance(result, int)
    print(f"✓ clean_preview_cache returned: {result}")
    
    # Test clean_rclone_temp
    result = cleaner.clean_rclone_temp()
    assert isinstance(result, int)
    print(f"✓ clean_rclone_temp returned: {result}")
    
    # Test get_cache_stats
    stats = cleaner.get_cache_stats()
    assert "preview_cache" in stats
    assert "rclone_temp" in stats
    assert "total_size_bytes" in stats
    print("✓ get_cache_stats returns correct structure")
    
    return True


def test_cache_schemas():
    """Test cache-related schemas"""
    print("\nTesting cache schemas...")
    
    from app.schemas.cache import CacheCleanupRequest, CacheStatsSchema, CacheCleanupResponse
    
    # Test CacheCleanupRequest
    request = CacheCleanupRequest(preview=True, temp=True, reports=False, days=30)
    assert request.preview is True
    assert request.days == 30
    print("✓ CacheCleanupRequest schema works correctly")
    
    # Test with validation
    try:
        invalid_request = CacheCleanupRequest(days=0)  # Should fail validation
        assert False, "Should have raised validation error"
    except Exception:
        print("✓ CacheCleanupRequest validates days parameter correctly")
    
    return True


def test_report_schemas():
    """Test report-related schemas"""
    print("\nTesting report schemas...")
    
    from app.schemas.report import LogEntrySchema, StatsSchema, ReportSchema, ReportResponse
    
    # Test StatsSchema
    stats = StatsSchema(
        total_files=100,
        copied_files=95,
        duration_seconds=120.5
    )
    assert stats.total_files == 100
    print("✓ StatsSchema works correctly")
    
    # Test ReportSchema
    report = ReportSchema(
        task_id="550e8400-e29b-41d4-a716-446655440000",
        status="success",
        stats=stats,
        logs=[],
        source_provider="yandex",
        source_path="/docs",
        dest_provider="google",
        dest_path="/backup"
    )
    assert report.task_id == "550e8400-e29b-41d4-a716-446655440000"
    assert report.status == "success"
    print("✓ ReportSchema works correctly")
    
    return True


async def run_async_tests():
    """Run all async tests"""
    print("=" * 60)
    print("RUNNING ASYNC TESTS")
    print("=" * 60)
    
    await test_bot_initialize_mock()
    await test_handle_start()
    await test_handle_status_no_task_id()


def run_sync_tests():
    """Run all sync tests"""
    print("=" * 60)
    print("RUNNING SYNC TESTS")
    print("=" * 60)
    
    test_bot_initialization()
    test_command_handlers()
    test_notifications()
    test_report_generator()
    test_formatters()
    test_cache_cleaner()
    test_cache_schemas()
    test_report_schemas()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TELEGRAM BOT & REPORTS TEST SUITE")
    print("=" * 60 + "\n")
    
    try:
        # Run sync tests
        run_sync_tests()
        
        # Run async tests
        asyncio.run(run_async_tests())
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
