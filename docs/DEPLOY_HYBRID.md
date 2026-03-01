# Deploy Hybrid (Astro SSR + Static)

## Архитектура

```
nginx (80/443) → static files (99% трафик)
                → proxy /api/* → Node.js :4321 (PM2)
```

## 1. Nginx конфигурация

На VPS: `/etc/nginx/sites-available/skklubb.ru`

```nginx
# Rate limiting zone for API
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;

server {
    listen 443 ssl http2;
    server_name skklubb.ru www.skklubb.ru;

    ssl_certificate /etc/letsencrypt/live/skklubb.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/skklubb.ru/privkey.pem;

    # Static files (prerendered pages)
    root /var/www/skklubb.ru/app/client;

    # Block dotfiles
    location ~ /\. {
        deny all;
    }

    # Static assets
    location / {
        try_files $uri $uri/index.html @node;
    }

    # API → Node.js with rate limiting
    location /api/ {
        limit_req zone=api burst=5 nodelay;
        proxy_pass http://127.0.0.1:4321;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Fallback → Node.js
    location @node {
        proxy_pass http://127.0.0.1:4321;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name skklubb.ru www.skklubb.ru;
    return 301 https://$host$request_uri;
}
```

## 2. PM2 на VPS

```bash
cd /var/www/skklubb.ru/app
npm ci --production

# Создать .env
echo "OPENROUTER_API_KEY=sk-or-v1-..." > .env

# Запустить
HOST=127.0.0.1 PORT=4321 pm2 start server/entry.mjs --name skklubb
pm2 save
pm2 startup
```

## 3. Переменные окружения на VPS

Файл: `/var/www/skklubb.ru/app/.env`

```
OPENROUTER_API_KEY=sk-or-v1-...
HOST=127.0.0.1
PORT=4321
```

## 4. GitHub Secrets

Нужно обновить `BEGET_DEPLOY_PATH`:
- Было: `/var/www/skklubb.ru/`
- Стало: `/var/www/skklubb.ru/app/` (если хотим держать всё в подпапке)

Или оставить как есть и адаптировать nginx root.

## 5. Проверки

```bash
# На VPS:
pm2 status                          # skklubb running
pm2 logs skklubb --lines 10        # нет ошибок
curl -s http://127.0.0.1:4321/     # HTML ответ

# Через домен:
curl -s https://skklubb.ru/        # статика через nginx
curl -X POST https://skklubb.ru/api/generate \
  -H "Content-Type: application/json" \
  -d '{"problemSlug":"parking","instanceId":"uk"}'
```

## 6. Стоимость AI

OpenRouter + Claude Haiku: ~$0.001 за генерацию
При 100 генераций/мес = ~$0.10
