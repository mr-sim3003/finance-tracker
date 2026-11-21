"""
Общие фикстуры для тестов приложения tracker.

Фикстура `user` вынесена сюда, потому что используется в test_api.py,
test_views.py, test_tasks.py и test_health.py — дублировать её в каждом
файле не нужно. pytest подхватывает conftest.py автоматически для всех
тестов в директории и поддиректориях.
"""

import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def user(db):
    """Тестовый пользователь (testuser / testpassword)."""
    User = get_user_model()
    return User.objects.create_user(username="testuser", password="testpassword")
