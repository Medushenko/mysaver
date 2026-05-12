# 💰 9. Биллинг-метрики и учёт потребления

## 📊 Стратегия сбора данных
- **MVP**: логирование без блокировок, подготовка к будущей монетизации
- **Фаза 2**: мягкие лимиты, подписка Free/Pro
- **Фаза 3**: usage-based overage, enterprise-лицензии

## 🗃 Базовые таблицы
```sql
CREATE TABLE usage_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    task_id UUID REFERENCES tasks(id),
    bytes_transferred BIGINT,
    provider_src VARCHAR(32),
    provider_dst VARCHAR(32),
    duration_sec INT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE feature_flags (
    key VARCHAR(64) PRIMARY KEY,
    enabled BOOLEAN DEFAULT FALSE,
    value JSONB,
    description TEXT
);
```



## 🧩 Поля пользователей

- `is_pro BOOLEAN DEFAULT FALSE`
- `plan_id VARCHAR(32) DEFAULT 'free'`
- `monthly_bytes_quota BIGINT DEFAULT 10737418240` (10 GB)
- `soft_limit_warning_sent BOOLEAN DEFAULT FALSE`

## 📈 Эволюция монетизации



| Тариф | Цена         | Лимиты                       | Фичи                                         |
| ----- | ------------ | ---------------------------- | -------------------------------------------- |
| Free  | $0           | 3 облака, 10 ГБ/мес          | Базовые задачи, отчёты UI                    |
| Pro   | $5–9/мес     | Безлимит облаков, 500 ГБ/мес | Приоритет очереди, PDF/Email, бот-расширение |
| Team  | $15–25/польз | Всё из Pro +                 | Роли, аудит 30д, смарт-папки                 |

## ⚠️ Правила реализации

- ❌ Не интегрировать Stripe/YooKassa в MVP
- ✅ Логировать `usage_logs` с первого дня
- ✅ Использовать `feature_flags` для включения/отключения фич без деплоя
- ✅ «Мягкие» лимиты: уведомления при 80% и 100%, блокировка только по согласованию