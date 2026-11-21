"""
Тесты моделей tracker: constraints, validators, поведение ORM.

Не путать с test_api.py (DRF) и test_views.py (Django-вью).
"""

import pytest
from django.db import IntegrityError

from tracker.models import Category, Transaction


@pytest.mark.django_db
def test_unique_category_per_user(user):
    """UniqueConstraint на (owner, name) запрещает дубликаты категорий."""
    Category.objects.create(name="Food", owner=user)

    with pytest.raises(IntegrityError):
        Category.objects.create(name="Food", owner=user)


@pytest.mark.django_db
def test_unique_transaction_constraint(user):
    """
    UniqueConstraint на (owner, date, amount, type, description) запрещает
    две одинаковые транзакции — это осознанное упрощение для идемпотентности
    импорта (см. README, «Ограничения»).

    Тест фиксирует КОНТРАКТ, а не ловит баг: если кто-то уберёт constraint,
    тест покраснеет — это сигнал обновить README и осознанно принять
    изменение поведения.
    """
    cat = Category.objects.create(name="Food", owner=user)
    Transaction.objects.create(
        type="expense",
        amount=150,
        category=cat,
        owner=user,
        date="2026-11-01",
        description="Кофе",
    )

    with pytest.raises(IntegrityError):
        Transaction.objects.create(
            type="expense",
            amount=150,
            category=cat,
            owner=user,
            date="2026-11-01",
            description="Кофе",
        )
