import os

from dotenv import load_dotenv

from .base import *

load_dotenv()  

SECRET_KEY = os.environ.get('SECRET_KEY', 'default-unsafe-key')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'tracker_db'),
        'USER': os.environ.get('POSTGRES_USER', 'tracker_user'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'crotplot'),
        'HOST': os.environ.get('POSTGRES_HOST', 'db'),   
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}
