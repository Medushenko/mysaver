# 🤖 7. Telegram-бот и интеграции

## 📜 Команды
| Команда | Описание |
|---------|----------|
| `/start` | Приветствие, меню, ссылка на веб-интерфейс |
| `/save [текст/ссылка]` | Парсинг → превью → подтверждение → очередь |
| `/status` | Список активных задач, прогресс, ETA |
| `/reports` | Ссылки на последние отчёты (PDF/MD) |
| `/cancel [task_id]` | Остановка задачи, очистка очереди |
| `/settings` | Настройки уведомлений, логирования, квот |

## 🔘 Inline-UI
- Кнопки подтверждения: `✅ Start`, `❌ Cancel`, `⚙️ Advanced`
- Прогресс: `📊 Copying... 45/102 (44%) | ~2 min`
- Ошибки: `⚠️ 3 files failed. 🔁 Retry All | 📄 View Report`

## 🔄 Логика работы
1. Webhook → backend → валидация → очередь
2. Статусы пушатся через `sendMessage` с `reply_markup`
3. Fallback: при overload бота → `⏳ Task queued, will notify when started`
4. Привязка к сессии: `session_id` хранится в Redis, маппится на `user_id`