"""
Конфигурация WSGI для проекта config.

Она предоставляет возможность вызова WSGI в качестве переменной уровня модуля с именем `application`.
"""
# В Docker (продакшн) эта настройка будет перезаписана значением из .env

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
                                 
application = get_wsgi_application()

          