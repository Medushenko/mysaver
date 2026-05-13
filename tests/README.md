# MySaver Test Suite

Автоматические тесты для ключевых систем проекта MySaver.

## 📁 Структура тестов

```
tests/
├── __init__.py                 # Инициализация пакета тестов
├── conftest.py                 # Фикстуры и конфигурация pytest
├── test_parsers.py             # Тесты парсеров ссылок (Unit)
├── test_core_components.py     # Тесты основных компонентов (Unit)
├── test_api_integration.py     # Интеграционные тесты API
└── internal_sandbox/
    └── test_sandbox_quick.py   # Быстрые тесты для AI песочницы
```

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
cd /workspace/backend
pip install pytest pytest-asyncio httpx psycopg2-binary asyncpg
```

### 2. Запуск всех тестов

```bash
# Из корня проекта
cd /workspace
./tests/run_tests.sh --all
```

### 3. Запуск по категориям

```bash
# Только unit тесты парсеров
pytest tests/test_parsers.py -v

# Только тесты компонентов
pytest tests/test_core_components.py -v

# Только интеграционные тесты (требуется запущенный сервер)
pytest tests/test_api_integration.py -v

# Только тесты для AI песочницы
pytest tests/internal_sandbox/ -v

# Тесты базы данных
pytest tests/test_db_integration.py -v
```

### 4. Использование скрипта запуска

```bash
# Все тесты
./tests/run_tests.sh --all

# Быстрые тесты песочницы
./tests/run_tests.sh --quick

# Только парсеры
./tests/run_tests.sh --parsers

# Тесты БД
./tests/run_tests.sh --db

# Unit тесты (по умолчанию)
./tests/run_tests.sh
```

### 4. Запуск с фильтрами

```bash
# По имени теста
pytest tests/ -k "test_parse_yandex" -v

# По классу тестов
pytest tests/test_parsers.py::TestYandexLinkParser -v

# С выводом print statements
pytest tests/ -v -s

# С покрытием кода (требуется pytest-cov)
pytest tests/ --cov=backend/app --cov-report=html
```

## 📋 Описание тестовых файлов

### `test_parsers.py`
Unit тесты для системы парсинга ссылок:
- `TestYandexLinkParser` — парсинг ссылок Яндекс.Диск
- `TestGoogleLinkParser` — парсинг ссылок Google Drive
- `TestLocalPathParser` — парсинг локальных путей (Unix/Windows)
- `TestCombinedParsing` — интеграционный тест комбинированного парсинга

**Зависимости:** Нет (чистые unit тесты)

### `test_core_components.py`
Unit тесты ключевых компонентов:
- `TestPreviewTree` — построение и сериализация дерева файлов
- `TestConflictResolver` — разрешение конфликтов (4 политики)
- `TestCacheCleaner` — очистка кеша (preview, temp, reports)
- `TestReportGenerator` — генерация отчётов и форматирование

**Зависимости:** Нет (кроме asyncio для некоторых тестов)

### `test_api_integration.py`
Интеграционные тесты через HTTP:
- `TestHealthCheck` — проверка доступности API
- `TestParseEndpoint` — тесты эндпоинта `/api/v1/parse`
- `TestTasksEndpoint` — CRUD операции с задачами
- `TestFullWorkflow` — сквозной тест полного цикла

**Требования:** 
- Запущенный сервер: `uvicorn app.main:app --port 8000`
- Рабочая база данных

### `internal_sandbox/test_sandbox_quick.py`
Специальные тесты для AI песочницы:
- `TestSandboxEnvironment` — проверка окружения
- `TestSandboxParsers` — быстрые тесты парсеров
- `TestSandboxQuickCheck` — проверка импорта модулей

**Особенности:** 
- Используют абсолютные пути (`/workspace/backend`)
- Минимальные зависимости
- Быстрое выполнение для оперативной проверки

## 🔧 Конфигурация

### Переменные окружения

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `TEST_DATABASE_URL` | URL тестовой БД | `postgresql+asyncpg://postgres:postgres@localhost:5432/mysaver_test` |
| `TEST_API_URL` | URL тестового API | `http://localhost:8000` |
| `CI` | Режим CI/CD | `false` |
| `AI_SANDBOX` | Режим AI песочницы | `false` |

### Автоматическое определение среды

- **Все среды (локальная, CI/CD, AI песочница):** PostgreSQL
- Для локальной разработки используйте Docker: `docker run -d -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:15`

## 📊 Формат отчётов об ошибках

При ошибке тесты выводят подробную информацию:

```
❌ ОШИБКА ТЕСТА: Parse Yandex links
────────────────────────────────
Status Code: 500
Response Body: {"detail": "Internal Server Error"}
Request URL: http://localhost:8000/api/v1/parse
────────────────────────────────
Пример запроса для воспроизведения:
curl -X POST http://localhost:8000/api/v1/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "..."}'
```

Эта информация готова для передачи AI агенту на анализ.

## 🎯 Примеры использования

### 1. Быстрая проверка после изменений

```bash
# Запустить только быстрые тесты песочницы
pytest tests/internal_sandbox/ -v -s
```

### 2. Полная проверка перед коммитом

```bash
# Все тесты кроме интеграционных (не требуют сервера)
pytest tests/test_parsers.py tests/test_core_components.py -v
```

### 3. Проверка API после запуска сервера

```bash
# В одном терминале запустить сервер
cd backend && uvicorn app.main:app --reload

# В другом терминале запустить интеграционные тесты
pytest tests/test_api_integration.py -v -s
```

### 4. Поиск конкретной ошибки

```bash
# Запустить один конкретный тест с подробным выводом
pytest tests/test_parsers.py::TestYandexLinkParser::test_parse_short_link -v -s
```

## 📈 Интерпретация результатов

### ✅ Успешное выполнение

```
======================== 15 passed in 2.34s ========================
```

Все тесты пройдены. Можно продолжать разработку.

### ⚠️ Частичный успех

```
=================== 12 passed, 3 skipped in 1.89s ===================
```

Некоторые тесты пропущены (обычно из-за отсутствия зависимостей).

### ❌ Ошибки

```
=================== 10 passed, 5 FAILED in 3.45s ===================
```

Просмотрите вывод выше для деталей ошибок. Скопируйте информацию об ошибках для анализа AI агентом.

## 🔗 Полезные ссылки

- [Документация pytest](https://docs.pytest.org/)
- [pytest-asyncio для асинхронных тестов](https://pytest-asyncio.readthedocs.io/)
- [Фикстуры pytest](https://docs.pytest.org/en/latest/explanation/fixtures.html)
