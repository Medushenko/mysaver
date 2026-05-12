# 🔐 6. Безопасность и соответствие

## 🔑 Авторизация и токены
- OAuth2 flow через backend-proxy (никогда не передаём токен фронтенду напрямую)
- Хранение: шифрование AES-256-GCM в PostgreSQL, ключи ротация по расписанию
- Гостевой режим: токены только в RAM, удаление по `logout` / `TTL expiry`

## 📜 Аудит и логирование
- Таблица `audit_logs`: `user_id`, `action`, `resource`, `ip`, `user_agent`, `timestamp`
- WORM-стиль: запрет `UPDATE/DELETE` записей старше 24ч (архивация в S3)
- Экспорт: CSV/JSON для compliance (GDPR, 152-ФЗ)

## 🛡 Защита данных
- Transit: TLS 1.3 everywhere
- At rest: DB encryption, encrypted backups
- Rate-limiting: API + rclone proxy (100 req/min/user)
- Sandbox: загружаемые файлы сканируются, запрет на исполняемые скрипты

## 🔮 Roadmap безопасности
- MVP: базовая защита, аудит, мягкие лимиты
- V2: 2FA, клиентское шифрование (опция), KMS-интеграция
- V3: Zero-knowledge режим, аппаратные ключи, SOC2-готовность