"""
Healthcheck для инфраструктуры.

Вынесен из views.py, потому что это не бизнес-логика трекера,
а инфраструктурный эндпоинт: его дёргает Docker HEALTHCHECK,
балансировщик и мониторинг. Держать его рядом с транзакциями —
значит смешивать домены.
"""
import redis
from django.conf import settings
from django.db import connection
from django.http import JsonResponse


def healthz(request):
    """
    Проверка живости приложения: БД + Redis.

    Функция, а не CBV: проверка простая, без состояния и без шаблона.
    CBV (View/TemplateView) добавил бы boilerplate (as_view, класс,
    метод get) без пользы — здесь нечего переиспользовать.
    """
    health = {'status': 'ok', 'services': {}}

    # 1. Проверка PostgreSQL.
    # SELECT 1 — самый дешёвый запрос: не трогает таблицы, но проверяет,
    # что соединение живое и БД отвечает. Используем connection.cursor(),
    # а не ORM, чтобы не зависеть от моделей (healthcheck должен работать
    # даже если модели сломаны).
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health['services']['db'] = 'ok'
    except Exception as e:  # noqa: BLE001
        # Ловим Exception, а не конкретный тип: healthcheck должен
        # вернуть 503 при ЛЮБОЙ проблеме с БД, а не упасть с 500.
        # подавление правила Ruff "не лови Exception".
        health['services']['db'] = f'error: {e!s}'
        health['status'] = 'degraded'

    # 2. Проверка Redis.
    # Берём URL из CELERY_BROKER_URL, а не хардкодим: в разных окружениях
    # (local, Docker, прод) адрес Redis может отличаться, но healthcheck
    # должен проверять именно тот Redis, который использует Celery.
    try:
        redis_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://redis:6379/0')
        r = redis.from_url(redis_url)
        r.ping()
        health['services']['redis'] = 'ok'
    except Exception as e:  # noqa: BLE001
        health['services']['redis'] = f'error: {e!s}'
        health['status'] = 'degraded'

    # 503, а не 200 при degraded: Docker HEALTHCHECK и балансировщик
    # ориентируются на HTTP-код. 200 при нерабочей БД = ложноположительный
    # healthcheck, который скроет проблему от мониторинга.
    status_code = 200 if health['status'] == 'ok' else 503
    return JsonResponse(health, status=status_code)