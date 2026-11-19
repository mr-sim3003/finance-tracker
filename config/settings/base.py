import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',                          # Стороние приложения
    'drf_spectacular',
    'drf_spectacular_sidecar',
    
    'accounts',                               # Мои приложения
    'tracker',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'config.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'config.wsgi.application'


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.CustomUser'


CELERY_BROKER_URL = 'redis://redis:6379/0'                # --- Celery ---  # адрес Redis, где Celery будет хранить очередь задач. redis:6379 — это имя сервиса из docker-compose.yml.
CELERY_RESULT_BACKEND = 'redis://redis:6379/0'              # где хранить результаты выполнения задач (тоже Redis).
CELERY_ACCEPT_CONTENT = ['json']                     #CELERY_ACCEPT_CONTENT и сериализаторы — говорим Celery использовать JSON (безопаснее и читаемее, чем pickle).
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'                   #часовой пояс для планировщика (если будем использовать Celery Beat).



MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

CELERY_TASK_ALWAYS_EAGER = False

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    # Глобальная защита: все API по умолчанию требуют логина.
    # Если в каком-то ViewSet нужно разрешить анонимный доступ,
    # это можно переопределить локально через permission_classes.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],

    # Ограничение частоты запросов (защита от спама и брутфорса).
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '1000/day',   # Авторизованный пользователь: 1000 запросов в день
        'anon': '100/day',    # Анонимный: 100 запросов в день
    },
}



SPECTACULAR_SETTINGS = {
    'TITLE': 'Finance Tracker API',
    'DESCRIPTION': 'API для учёта личных доходов и расходов',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    
    #Локальные ассеты вместо внешних CDN 
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    
    # Удобства для Swagger UI 
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,  # токен не слетает при перезагрузке страницы
    },
}


