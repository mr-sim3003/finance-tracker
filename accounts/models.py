"""
Модели приложения accounts.

Хранит кастомную модель пользователя. Мы наследуемся от AbstractUser,
чтобы в будущем легко добавить поля (например, аватар или настройки),
не ломая структуру БД.
"""

from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    pass
