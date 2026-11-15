import os

from .postgres import *

CELERY_TASK_ALWAYS_EAGER = True

MEDIA_ROOT = '/tmp/test_media'                   # отдельная директория для тестов
os.makedirs(MEDIA_ROOT, exist_ok=True)

DATABASES['default']['HOST'] = 'localhost'