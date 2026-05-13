#!/bin/bash
# MySaver Test Runner
# Автоматический запуск тестов с PostgreSQL (высоконагруженная система)

set -e

# Переход в директорию проекта
cd "$(dirname "$0")/.."

# Загрузка переменных окружения из .env файла
if [ -f "backend/.env" ]; then
    export $(grep -v '^#' backend/.env | xargs)
    echo "✅ Переменные окружения загружены из backend/.env"
fi

# Экспорт переменных окружения для тестов
export TEST_DATABASE_URL="${TEST_DATABASE_URL:-postgresql+asyncpg://postgres:postgres@localhost:5432/mysaver_test}"
export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/mysaver}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
export RCLONE_RC_ADDR="${RCLONE_RC_ADDR:-http://localhost:5572}"
export PYTHONPATH="${PYTHONPATH:-$(pwd)/backend}:$PYTHONPATH"
export AI_SANDBOX="${AI_SANDBOX:-false}"

echo "======================================"
echo "🧪 MySaver Test Suite (PostgreSQL)"
echo "======================================"
echo "Database: $TEST_DATABASE_URL"
echo "Python Path: $PYTHONPATH"
echo ""

# Проверка доступности PostgreSQL
check_postgres() {
    if command -v psql &> /dev/null; then
        if psql -h localhost -U postgres -c '\q' 2>/dev/null; then
            echo "✅ PostgreSQL доступен"
            return 0
        fi
    fi
    echo "⚠️  PostgreSQL недоступен. Некоторые тесты будут пропущены."
    return 1
}

# Проверка доступности pytest
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest не найден. Установка..."
    pip install pytest pytest-asyncio httpx psycopg2-binary asyncpg --quiet
fi

# Проверка PostgreSQL перед запуском
if ! check_postgres; then
    echo ""
    echo "💡 Для запуска тестов убедитесь, что PostgreSQL запущен:"
    echo "   docker run -d -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:15"
    echo ""
fi

# Запуск тестов
if [ "$1" == "--all" ]; then
    echo "📋 Запуск ВСЕХ тестов (включая интеграционные)..."
    echo "⚠️  Убедитесь, что сервер запущен: uvicorn app.main:app --port 8000"
    pytest tests/ -v "$@"
elif [ "$1" == "--quick" ]; then
    echo "⚡ Запуск быстрых тестов песочницы..."
    AI_SANDBOX=true pytest tests/internal_sandbox/ -v "$@"
elif [ "$1" == "--parsers" ]; then
    echo "🔗 Запуск тестов парсеров..."
    pytest tests/test_parsers.py -v "$@"
elif [ "$1" == "--db" ]; then
    echo "🗄️  Запуск тестов базы данных..."
    pytest tests/test_db_integration.py -v "$@"
else
    echo "📋 Запуск unit тестов (без интеграционных)..."
    pytest tests/test_parsers.py tests/internal_sandbox/ -v "$@"
fi

echo ""
echo "======================================"
echo "✅ Тесты завершены!"
echo "======================================"
