import os

from .base import *

CELERY_TASK_ALWAYS_EAGER = True            # Отключаем всё, что мешает тестам (кеши, celery)

MEDIA_ROOT = '/tmp/test_media'                   # отдельная директория для тестов
os.makedirs(MEDIA_ROOT, exist_ok=True)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

SECRET_KEY = 'test-secret-key-for-ci'            # Тестовый ключ (не секретный, только для CI)