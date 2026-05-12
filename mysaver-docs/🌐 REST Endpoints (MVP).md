| Method | Path                            | Описание                                |
| ------ | ------------------------------- | --------------------------------------- |
| `POST` | `/api/v1/tasks`                 | Создание задачи (авто-парсинг или JSON) |
| `GET`  | `/api/v1/tasks/{id}`            | Статус, прогресс, отчёт                 |
| `POST` | `/api/v1/tasks/{id}/retry`      | Повтор только ошибок                    |
| `GET`  | `/api/v1/reports/{task_id}`     | Экспорт PDF/MD                          |
| `POST` | `/api/v1/auth/guest`            | Создание гостевой сессии                |
| `POST` | `/api/v1/auth/oauth/{provider}` | Инициация OAuth2 flow                   |

## 📡 Webhook & Bot Contracts

- `task.updated`: `{"task_id", "status", "progress_pct", "eta"}`
- `task.completed`: `{"task_id", "success_count", "error_paths", "report_url"}`
- Telegram callback: `{"callback_data": "retry:{task_id}:{error_hash}"}`