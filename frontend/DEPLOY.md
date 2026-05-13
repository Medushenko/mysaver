# MySaver Frontend Deployment Guide

## Overview

This document describes how to deploy the MySaver frontend to work with the FastAPI backend on a production Linux server.

## Architecture

The frontend is a **vanilla JavaScript SPA** (Single Page Application) that:
- Uses **Tailwind CSS via CDN** (no build step required)
- Works as **static files** served by FastAPI or Nginx
- Communicates with the backend via **relative API paths** (`/api/v1/...`)
- Automatically detects development vs production environment

## File Structure

```
frontend/
├── index.html          # Main entry point
├── css/
│   └── style.css       # Custom styles
├── js/
│   ├── app.js          # Application initialization & routing
│   ├── api.js          # API client wrapper
│   ├── parser.js       # Link parsing functionality
│   ├── tree.js         # Preview tree rendering
│   ├── conflicts.js    # Conflict resolution UI
│   └── tasks.js        # Task monitoring with polling
└── DEPLOY.md           # This file
```

## Option 1: Serve via FastAPI (Recommended for Simple Deployments)

### Step 1: Update `backend/app/main.py`

Add static files mounting to your FastAPI application:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MySaver API")

# CORS for development (disable in production if serving from same domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend static files
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")

# Include API routers
from app.api.v1 import parse, preview, tasks, reports, cache

app.include_router(parse.router, prefix="/api/v1", tags=["parse"])
app.include_router(preview.router, prefix="/api/v1", tags=["preview"])
app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
app.include_router(reports.router, prefix="/api/v1", tags=["reports"])
app.include_router(cache.router, prefix="/api/v1", tags=["cache"])
```

### Step 2: Directory Structure

Ensure your project structure looks like this:

```
mysaver/
├── backend/
│   ├── app/
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── css/
│   └── js/
└── ...
```

### Step 3: Run the Application

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The frontend will be accessible at `http://your-server:8000/`
The API will be accessible at `http://your-server:8000/api/v1/...`

---

## Option 2: Serve via Nginx (Recommended for Production)

### Step 1: Copy Frontend Files

Copy frontend files to a web-accessible directory:

```bash
sudo mkdir -p /var/www/mysaver
sudo cp -r frontend/* /var/www/mysaver/
sudo chown -R www-data:www-data /var/www/mysaver
```

### Step 2: Configure Nginx

Create Nginx configuration file `/etc/nginx/sites-available/mysaver`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Serve frontend static files
    location / {
        root /var/www/mysaver;
        try_files $uri $uri/ /index.html;
        index index.html;
    }

    # Proxy API requests to FastAPI backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket support (if needed for real-time features)
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

### Step 3: Enable Site and Restart Nginx

```bash
sudo ln -s /etc/nginx/sites-available/mysaver /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 4: Run FastAPI Backend

Run the backend on port 8000 (localhost only, not exposed):

```bash
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Or use systemd service for production:

Create `/etc/systemd/system/mysaver.service`:

```ini
[Unit]
Description=MySaver Backend Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/mysaver/backend
ExecStart=/path/to/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mysaver
sudo systemctl start mysaver
sudo systemctl status mysaver
```

---

## Option 3: Docker Deployment

### Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy frontend
COPY frontend/ ./frontend/

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  mysaver:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./cache:/app/cache
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/mysaver
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mysaver
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

Run:

```bash
docker-compose up -d
```

---

## Environment Variables

Configure these environment variables for production:

```bash
# Backend Configuration
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/mysaver
REDIS_URL=redis://localhost:6379

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your_bot_token
ADMIN_CHAT_ID=your_chat_id

# Cache Configuration
CACHE_TTL_SECONDS=3600
MAX_CACHE_SIZE_BYTES=1073741824

# CORS (development only)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

---

## Testing Deployment

### 1. Health Check

```bash
curl http://your-domain.com/api/v1/health
```

Expected response: `{"status": "ok"}`

### 2. Frontend Loading

Open `http://your-domain.com` in browser and verify:
- ✅ Page loads without errors
- ✅ Tailwind CSS styles are applied
- ✅ Navigation works between pages
- ✅ No CORS errors in browser console

### 3. API Integration

Test API endpoints from browser DevTools Console:

```javascript
fetch('/api/v1/parse', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text: 'https://yadi.sk/d/test'})
}).then(r => r.json()).then(console.log);
```

---

## Troubleshooting

### Frontend not loading

1. Check file permissions: `ls -la /var/www/mysaver`
2. Verify Nginx config: `nginx -t`
3. Check Nginx logs: `tail -f /var/log/nginx/error.log`

### API requests failing

1. Ensure backend is running: `systemctl status mysaver`
2. Check backend logs: `journalctl -u mysaver -f`
3. Verify proxy settings in Nginx config

### CORS errors

- In production, frontend and API should be on same domain
- Remove or restrict CORS origins in `main.py`

### Mobile menu not working

- Ensure JavaScript modules are loading correctly
- Check browser console for module loading errors
- Verify MIME types are correct in Nginx config

---

## Security Considerations

1. **HTTPS**: Always use HTTPS in production
2. **CORS**: Restrict allowed origins
3. **Rate Limiting**: Implement rate limiting for API endpoints
4. **Authentication**: Add authentication for sensitive operations
5. **Input Validation**: Validate all user inputs on backend

---

## Performance Optimization

1. **Enable Gzip compression** in Nginx:
```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
gzip_min_length 1000;
```

2. **Set cache headers** for static assets:
```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

3. **Use HTTP/2** for better performance:
```nginx
listen 443 ssl http2;
```

---

## Support

For issues or questions:
- Check existing GitHub issues
- Review backend and frontend logs
- Contact: admin@medushenko.dev
