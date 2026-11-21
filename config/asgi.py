"""
Конфигурация ASGI для проекта config.

Она предоставляет возможность вызова ASGI в качестве переменной уровня модуля с именем `application`.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
