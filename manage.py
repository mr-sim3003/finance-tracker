#!/usr/bin/env python
# В Docker (продакшн) эта настройка будет перезаписана значением из .env

import os
import sys


def main():
    """Run administrative tasks."""
    # setdefault() задает значение только если переменная еще не задана.
    # В Docker Compose (.env) передается DJANGO_SETTINGS_MODULE=config.settings.prod,
    # поэтому в контейнере используется prod, а локально (без Docker) — local.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Не удалось импортировать Django. Вы уверены, что он установлен и"
            "доступен в вашей переменной среды PYTHONPATH?"
            "Вы забыли активировать виртуальную среду?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
