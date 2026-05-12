# 🏗 3. Архитектура и технологический стек

## 🌐 High-Level Схема
```mermaid
graph TD
    UI[PWA / Telegram Bot] --> API[Backend API Gateway]
    API --> Q[Task Queue (Redis/Celery)]
    Q --> W[Worker Node]
    W --> R[rclone RC API (localhost)]
    W --> SDK[Provider SDKs / REST]
    W --> DB[(PostgreSQL + Redis)]
    R --> Cloud[Cloud Providers]
    W --> Bot[Webhook → Telegram]
    W --> Logger[Usage & Audit Logger]