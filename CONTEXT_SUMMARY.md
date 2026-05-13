# MySaver — Контекст для Итерации 2.1

## Стек
- **Backend:** Python 3.12, FastAPI, SQLAlchemy async, Celery, Redis, PostgreSQL
- **Storage:** rclone (RC API на порту 5572)
- **Frontend:** пока временный `/build-status`, планируется React/Vue
- **Telegram Bot:** python-telegram-bot (требует токен в .env)

## API Endpoints (v1)
- `POST /api/v1/parse` — извлечение ссылок из текста (Yandex, Google, local)
- `POST /api/v1/tasks` — создание задачи копирования
- `GET /api/v1/preview/{id}` — превью-дерево файлов
- `GET /api/v1/reports/{id}` — отчёт о задаче
- `DELETE /api/v1/cache` — очистка кеша (preview, temp, reports)
- `GET /api/v1/build-status` — статус разработки (временный UI)
- `GET /health` — health check

## Ключевые модули
- `app/core/parsers/` — извлечение ссылок (YandexLinkParser, GoogleLinkParser, LocalPathParser)
- `app/core/preview/` — построение дерева файлов (TreeBuilder, PreviewTree)
- `app/core/telegram/` — бот для уведомлений (TelegramBot)
- `app/core/reports/` — генерация отчётов (ReportGenerator)
- `app/core/cache/` — очистка временных файлов (CacheCleaner)
- `app/core/conflicts/` — разрешение конфликтов (ConflictResolver)

## База данных
- **Движок:** PostgreSQL (asyncpg)
- **ORM:** SQLAlchemy 2.0 (async)
- **Таблицы:** users, tasks, usage_logs, feature_flags
- **Миграции:** Alembic (папка `alembic/`, но пока не используется активно)
- **Новые поля в tasks (итерация 1.2):** parsed_links (JSONB), conflict_policy (VARCHAR), preview_tree (JSONB)

## Запуск проекта

### 1. Зависимости (Docker через Colima)
```bash
~/dev/env-manager/🚀\ Start\ Environment.command
# Запускает: postgres (5432), redis (6379), rclone (5572), api (8000)
```

### 2. Celery Worker
```bash
cd /Users/medushenko/dev/MySaver/backend
source venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info
```

### 3. FastAPI Server
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Тестирование

### Парсинг ссылок
```bash
python scripts/test_parser.py
# Или через API:
curl -X POST http://127.0.0.1:8000/api/v1/parse \
  -H "Content-Type: application/json" \
  -d '{"text":"https://yadi.sk/d/test"}' | jq .
```

### Проверка превью
```bash
curl http://127.0.0.1:8000/api/v1/preview/{task_id} | jq .
```

### Telegram Bot
```bash
# Требует TELEGRAM_BOT_TOKEN в .env
python -m app.core.telegram.bot
```

## Переменные окружения (.env)
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/mysaver
REDIS_URL=redis://localhost:6379/0
RCLONE_RC_ADDR=http://localhost:5572
TELEGRAM_BOT_TOKEN=your_token_here
ADMIN_CHAT_ID=your_chat_id_here
DEBUG=true
```

## Известные проблемы
- Alembic миграции требуют ручной правки при смене типов (VARCHAR → ENUM)
- Для разработки используется ручной `ALTER TABLE` вместо миграций
- Telegram-бот требует токен (получается у @BotFather)

## Следующая цель: Итерация 2.1
- Интерактивное дерево с чекбоксами (React/Vue или чистый JS)
- Drag-and-drop для выбора файлов
- Адаптивный дизайн (мобильные)
- Интеграция с Telegram-ботом через API
```

---

