import os

import dj_database_url
from dotenv import load_dotenv

from .base import *

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY", "default-unsafe-key")

DEBUG = os.environ.get("DEBUG", "False") == "True"

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

DATABASES = {"default": dj_database_url.config(conn_max_age=600)}

CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

DEBUG_PROPAGATE_EXCEPTIONS = True
