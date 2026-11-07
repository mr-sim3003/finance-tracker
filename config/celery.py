import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod') # Указываем Django, какой файл настроек использовать по умолчанию

app = Celery('config')  # Celery('config') — создаем экземпляр Celery (имя обычно совпадает с именем проекта).
app.config_from_object('django.conf:settings', namespace='CELERY')      # говорит Celery: «Читай настройки из Django, но только те, что начинаются на CELERY_». Это удобно, потому что мы можем задать CELERY_BROKER_URL в settings.py.
app.autodiscover_tasks()                                                # Автоматически ищем задачи в файлах tasks.py во всех приложениях из INSTALLED_APPS.  не нужно импортировать их вручную.