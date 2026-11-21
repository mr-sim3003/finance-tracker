# Деплой на VPS

Прод запущен на одном VPS: Docker Compose поднимает `db`, `redis`, `web`, `celery`
и `nginx`. Nginx принимает внешний трафик, терминирует TLS и проксирует запросы
в Gunicorn.

## Что где лежит

| Файл | Назначение |
|---|---|
| `docker-compose.yml` | сервисы: db, redis, web, celery, nginx |
| `docker-compose.override.yml` | локальные правки (Nginx выключен, порт 8000 проброшен) |
| `Dockerfile` | образ `web` и `celery`: Python 3.12, зависимости, Gunicorn |
| `deploy/gunicorn.conf.py` | bind `0.0.0.0:8000`, воркеры, таймауты, логи |
| `deploy/nginx.conf` | reverse proxy, TLS, rate limiting, статика |
| `.env` | секреты и параметры окружения (не в git) |

## Схема

```
клиент → :443 Nginx → web:8000 (Gunicorn) → Django
                    ↘ /static/ → статика из /app/staticfiles/
       ↘ Celery worker → Redis (брокер) → PostgreSQL
```

## Первый запуск на сервере

1. Установить Docker и Docker Compose plugin.
2. Клонировать репозиторий, создать `.env` на основе `.env.example`, заполнить
   `SECRET_KEY`, `ALLOWED_HOSTS`, `POSTGRES_*`, `DATABASE_URL`.
3. Поднять контейнеры:
   ```bash
   docker compose up -d --build
   ```
4. Применить миграции и собрать статику:
   ```bash
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py collectstatic --noinput
   ```
5. Создать суперпользователя:
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

## TLS

Сертификат Let's Encrypt выпускается через `certbot` (standalone или webroot).
Файлы монтируются в Nginx из `/etc/letsencrypt` (read-only). Продление — по cron
или systemd timer (`certbot renew`), Nginx перезагружается после продления.

## Безопасность

В `config/settings/prod.py`:
- `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` — Django доверяет
  заголовку от Nginx и считает запрос HTTPS;
- `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True` — cookie только по HTTPS.

В `deploy/nginx.conf`:
- `limit_req_zone` — rate limiting (10 r/s на IP, burst 20);
- `client_max_body_size 10M` — ограничение размера загружаемого файла;
- заголовки `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto` пробрасываются в Django.

## Healthcheck

Сервис `web` в `docker-compose.yml` проверяется через `curl -f http://localhost:8000/healthz/`.
Эндпоинт возвращает:
- `200` — БД и Redis отвечают;
- `503` — хотя бы один сервис недоступен (`status: degraded`).

Это позволяет Docker и внешнему балансировщику видеть деградацию, а не ложноположительный
«сервис жив».

## Обновление

```bash
git pull
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py collectstatic --noinput
```

## Полезное

- Логи: `docker compose logs -f web`, `docker compose logs -f celery`, `docker compose logs -f nginx`.
- Перезапуск одного сервиса: `docker compose restart web`.
- Проверка healthcheck вручную: `curl -i https://<домен>/healthz/`.