import os

from .base import *

# Для тестов используем быструю SQLite в памяти
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Тестовый ключ (не секретный, только для CI)
SECRET_KEY = 'test-secret-key-for-ci'

# Отключаем всё, что мешает тестам (кеши, celery)
CELERY_TASK_ALWAYS_EAGER = True

MEDIA_ROOT = '/tmp/test_media'
os.makedirs(MEDIA_ROOT, exist_ok=True)