#!/bin/bash
# MySaver Test Runner
# Автоматический запуск тестов с правильной настройкой окружения

set -e

# Переход в директорию проекта
cd "$(dirname "$0")/.."

# Экспорт переменных окружения
export DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///./backend/mysaver.db}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
export RCLONE_RC_ADDR="${RCLONE_RC_ADDR:-http://localhost:5572}"
export PYTHONPATH="${PYTHONPATH:-$(pwd)/backend}:$PYTHONPATH"

echo "======================================"
echo "🧪 MySaver Test Suite"
echo "======================================"
echo "Database: $DATABASE_URL"
echo "Python Path: $PYTHONPATH"
echo ""

# Проверка доступности pytest
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest не найден. Установка..."
    pip install pytest pytest-asyncio httpx aiosqlite --quiet
fi

# Запуск тестов
if [ "$1" == "--all" ]; then
    echo "📋 Запуск ВСЕХ тестов (включая интеграционные)..."
    echo "⚠️  Убедитесь, что сервер запущен: uvicorn app.main:app --port 8000"
    pytest tests/ -v "$@"
elif [ "$1" == "--quick" ]; then
    echo "⚡ Запуск быстрых тестов песочницы..."
    pytest tests/internal_sandbox/ -v "$@"
elif [ "$1" == "--parsers" ]; then
    echo "🔗 Запуск тестов парсеров..."
    pytest tests/test_parsers.py -v "$@"
else
    echo "📋 Запуск unit тестов (без интеграционных)..."
    pytest tests/test_parsers.py tests/internal_sandbox/ -v "$@"
fi

echo ""
echo "======================================"
echo "✅ Тесты завершены!"
echo "======================================"
