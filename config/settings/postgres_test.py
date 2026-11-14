import os

from .postgres import *

DATABASES['default']['HOST'] = 'localhost'

CELERY_TASK_ALWAYS_EAGER = True   # задачи выполняются синхронно, чтобы тестировать без воркера
MEDIA_ROOT = '/tmp/test_media'    # отдельная директория для тестов
os.makedirs(MEDIA_ROOT, exist_ok=True)