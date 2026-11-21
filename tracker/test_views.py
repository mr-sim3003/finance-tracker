"""
Тесты Django-вью (HTML-страницы, не DRF API).

Всё, что ходит на /, /add/, /edit/<id>/, /delete/<id>/, /upload-csv/.
DRF-тесты (/api/...) — в test_api.py.
"""

from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from tracker.models import Category, Transaction


@pytest.mark.django_db
def test_upload_non_csv_file_rejected(client, user):
    """
    Проверяет, что файл с расширением .txt отклоняется.
    View должен вернуть редирект (302) и сообщение об ошибке.
    """
    txt_file = SimpleUploadedFile(
        "test.txt", b"some text content", content_type="text/plain"
    )

    client.force_login(user)
    response = client.post("/upload-csv/", {"file": txt_file})

    assert response.status_code == 302
    assert Transaction.objects.count() == 0


@pytest.mark.django_db
def test_user_cannot_edit_other_users_transaction(client, user):
    """Пользователь не может открыть/удалить чужую транзакцию (404)."""
    User = get_user_model()
    user2 = User.objects.create_user(username="user2", password="password2")
    cat2 = Category.objects.create(name="Food", owner=user2)

    t2 = Transaction.objects.create(
        type="income", amount=100, category=cat2, owner=user2, date="2026-11-02"
    )
    client.force_login(user)

    response = client.get(f"/edit/{t2.id}/")
    assert response.status_code == 404

    response_delete = client.get(f"/delete/{t2.id}/")
    assert response_delete.status_code == 404


@pytest.mark.django_db
def test_user_can_edit_own_transaction(client, user):
    """Своя транзакция открывается на редактирование (200)."""
    cat = Category.objects.create(name="Food", owner=user)
    t1 = Transaction.objects.create(
        type="income", amount=100, category=cat, owner=user, date="2026-11-02"
    )
    client.force_login(user)

    response = client.get(f"/edit/{t1.id}/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_main_page_requires_login(client):
    """Неавторизованный пользователь редиректится на логин."""
    response = client.get("/")
    assert response.status_code == 302
    assert "/accounts/login/" in response.url


@pytest.mark.django_db
def test_user_sees_only_own_transactions_on_main_page(client, user):
    """На главной странице — только свои транзакции."""
    User = get_user_model()
    user2 = User.objects.create_user(username="user2", password="password2")

    cat1 = Category.objects.create(name="Food", owner=user)
    cat2 = Category.objects.create(name="Transport", owner=user2)

    t1 = Transaction.objects.create(
        type="income", amount=100, category=cat1, owner=user, date="2026-11-02"
    )
    Transaction.objects.create(
        type="expense", amount=50, category=cat2, owner=user2, date="2026-11-02"
    )

    client.force_login(user)
    response = client.get("/")

    assert response.status_code == 200
    assert len(response.context["transactions"]) == 1
    assert response.context["transactions"][0].id == t1.id


@pytest.mark.django_db
def test_create_transaction_with_new_category(client, user):
    """При вводе новой категории она создаётся и привязывается к транзакции."""
    client.force_login(user)

    response = client.post(
        "/add/",
        {
            "type": "expense",
            "amount": "150.00",
            "new_category": "Кофе",
            "date": "2026-11-05",
            "description": "Утренний кофе",
        },
    )

    assert response.status_code == 302
    category = Category.objects.get(owner=user, name="Кофе")
    assert category is not None
    transaction = Transaction.objects.get(owner=user, amount=150)
    assert transaction.category == category


@pytest.mark.django_db
def test_main_page_filters_by_month(client, user):
    """Главная по умолчанию показывает только текущий месяц."""
    cat = Category.objects.create(name="Food", owner=user)
    today_dt = date.today()

    t_current = Transaction.objects.create(
        type="income", amount=100, category=cat, owner=user, date=today_dt
    )
    prev_month_dt = today_dt.replace(day=1) - timedelta(days=1)
    t_prev = Transaction.objects.create(
        type="income", amount=50, category=cat, owner=user, date=prev_month_dt
    )

    client.force_login(user)

    response = client.get("/")
    assert len(response.context["transactions"]) == 1
    assert response.context["transactions"][0].id == t_current.id

    response_prev = client.get(f"/?month={prev_month_dt.strftime('%Y-%m')}")
    assert len(response_prev.context["transactions"]) == 1
    assert response_prev.context["transactions"][0].id == t_prev.id


@pytest.mark.django_db
def test_monthly_totals_calculation(client, user):
    """Агрегаты (income/expense/balance) считаются по месяцу, не по странице."""
    cat = Category.objects.create(name="Food", owner=user)
    today = date.today()

    Transaction.objects.create(
        type="income", amount=1000, category=cat, owner=user, date=today
    )
    Transaction.objects.create(
        type="income", amount=500, category=cat, owner=user, date=today
    )
    Transaction.objects.create(
        type="expense", amount=300, category=cat, owner=user, date=today
    )
    prev_month = today.replace(day=1) - timedelta(days=1)
    Transaction.objects.create(
        type="expense", amount=9999, category=cat, owner=user, date=prev_month
    )

    client.force_login(user)
    response = client.get("/")

    assert response.context["total_income"] == 1500
    assert response.context["total_expense"] == 300
    assert response.context["balance"] == 1200


@pytest.mark.django_db
def test_create_transaction_with_whitespace_category(client, user):
    """Категория из одних пробелов не создаётся (ошибка валидации)."""
    client.force_login(user)

    response = client.post(
        "/add/",
        {
            "type": "expense",
            "amount": "100.00",
            "new_category": "   ",
            "date": "2026-11-05",
            "description": "Test",
        },
    )

    assert response.status_code == 200
    assert not Category.objects.filter(name="").exists()


@pytest.mark.django_db
def test_import_job_list_idor(client, user):
    """
    Пользователь видит только свои ImportJob'ы, чужие — нет.

    Регресс на IDOR: без filter(user=...) в ImportJobListView.get_queryset
    пользователь увидел бы историю импортов всех юзеров.
    """
    from tracker.models import ImportJob

    User = get_user_model()
    other_user = User.objects.create_user(username="other", password="otherpass")

    my_job = ImportJob.objects.create(user=user, file_name="mine.csv", status="done")
    other_job = ImportJob.objects.create(
        user=other_user, file_name="theirs.csv", status="done"
    )

    client.force_login(user)
    response = client.get("/import-jobs/")

    assert response.status_code == 200
    jobs = response.context["jobs"]
    assert len(jobs) == 1
    assert jobs[0].id == my_job.id
    # Чужой job не попал в контекст
    assert all(job.id != other_job.id for job in jobs)
