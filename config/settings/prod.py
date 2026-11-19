import os

import dj_database_url
from dotenv import load_dotenv

from .base import *

load_dotenv()

SECRET_KEY = os.environ["SECRET_KEY"]

DEBUG = False

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")  # хост=домен

DATABASES = {"default": dj_database_url.config(conn_max_age=600)}
