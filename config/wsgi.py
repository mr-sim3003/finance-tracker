"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

# Импорт модуля os. Он нужен, чтобы работать с переменными окружения 
# (например, сказать Django, какой файл настроек использовать).
from django.core.wsgi import get_wsgi_application

                                                            #Эта функция  которая создает WSGI-приложение. Именно её Gunicorn будет вызывать для каждого запроса.

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
                                                            #DJANGO_SETTINGS_MODULE — это переменная окружения.
                                                            #config.settings.local — путь к файлу настроек (тот самый local.py, который  создали для разделения настроек).
                                                            #setdefault — это хитрость. Он говорит: «Если переменная DJANGO_SETTINGS_MODULE уже задана в окружении (например, Docker передал config.settings.prod), используй её. Если нет — используй config.settings.local».
                                                            #Локально работаешь с local.py, а в Docker-контейнере (через docker-compose.yml) передается prod.py. Один и тот же файл wsgi.py работает в обоих режимах.

application = get_wsgi_application()

                                                            #Здесь создается само WSGI-приложение. Функция get_wsgi_application() загружает настройки,
                                                            #  инициализирует Django и возвращает объект application.
                                                            #Почему именно application: Gunicorn (или uWSGI) ищет в файле wsgi.py переменную с именем application. 
                                                            # Это стандарт WSGI. Когда Gunicorn запускается командой gunicorn config.wsgi:application,
                                                            #  он ищет config/wsgi.py и берет оттуда переменную application.