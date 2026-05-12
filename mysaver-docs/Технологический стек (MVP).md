| Слой     | Технология                   | Обоснование                                                  |
| -------- | ---------------------------- | ------------------------------------------------------------ |
| Backend  | Python + FastAPI             | Быстрая разработка, `aiohttp`, `celery`, `asyncpg`, удобный subprocess management |
| Frontend | React/Vue + TypeScript + PWA | Кроссплатформенность, виртуализация списков, оффлайн-кеш UI  |
| Queue    | Redis + Celery / BullMQ      | Отказоустойчивость, приоритизация, retry/backoff             |
| DB       | PostgreSQL + Redis           | Транзакции, `ltree` для путей, кеш сессий/метаданных         |
| Engine   | `rclone` (v1.65+)            | Готовый server-side copy, checksum, chunked upload, rate-limit |
| Deploy   | Docker + Docker Compose      | Изоляция, масштабирование, простое обновление                |

## ⚙️ rclone Integration Strategy

- Запуск как сервис: `rclone rcd --rc-web-gui=false --rc-addr=127.0.0.1:5572 --rc-job-expire 10m`
- Общение через HTTP+JSON: `/rc/copy`, `/rc/job/status`, `/rc/core/stats`
- Валидация: флаг `--checksum` + парсинг итогового `checks == transfers`
- Fallback: если `rclone` не поддерживает провайдер → лёгкий wrapper на SDK (boto3/yandex-disk-sdk)
- Конфиги: генерируются динамически под сессию, удаляются после завершения (`rclone rc core/purge`)

## 📊 Data Flow (Task Execution)

1. UI/Bot → POST `/api/v1/tasks` → валидация квот/прав → статус `PENDING`
2. Worker забирает задачу → генерирует `rclone.conf` → вызывает `/rc/copy`
3. Мониторинг: GET `/rc/job/status` каждые 1–3с → пуш в WebSocket/бота
4. Завершение: проверка `error_count`, `checks` → статус `SUCCESS/PARTIAL/FAILED`
5. Отчёт: генерация JSON → HTML/PDF → push пользователю
6. Retry: фильтрация `failed_paths` → новая задача `--include-from`

## 🔑 Ключевые архитектурные решения

- **Гибридная валидация**: доверяем `rclone --checksum`, добавляем свой парсер отчётов и retry-логику.
- **Изоляция сессий**: временные конфиги, очистка токенов после сессии/логаута.
- **Асинхронность**: все тяжёлые операции в фоне, UI не блокируется.
- **Расширяемость**: адаптер-паттерн `StorageAdapter` для новых провайдеров без изменения ядра.