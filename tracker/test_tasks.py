import pytest
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from tracker.models import ImportJob, Transaction
from tracker.tasks import import_csv_task


@pytest.fixture  # Фикстура: создаёт тестового пользователя
def user(db):
    User = get_user_model()
    return User.objects.create_user(username="testuser", password="testpassword")


@pytest.fixture  # Фикстура: создаёт API-клиент
def api_client():
    return APIClient()


@pytest.fixture  # Фикстура: авторизует клиент
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db(transaction=True)
def test_csv_import_is_idempotent(auth_client, user):
    csv_content = (
        b"type,amount,category,date,description\n"  #  Готовим CSV-файл в памяти
    )
    csv_content += b"expense,150.50,Food,2026-11-01,Lunch\n"
    csv_content += b"income,1000.00,Salary,2026-11-05,November\n"
    # SimpleUploadedFile — это способ имитировать файл, который пользователь загружает через форму. Нам не нужен реальный файл на диске, достаточно «байтов в памяти».
    csv_file = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")

    response1 = auth_client.post(
        "/upload-csv/", {"file": csv_file}
    )  #  Загружаем файл ПЕРВЫЙ.  проверяет, что импорт работает
    assert response1.status_code == 302

    # ВАЖНО: API уже прочитал файл, курсор в конце.
    # Перематываем его в начало, чтобы сохранить заново.
    csv_file.seek(0)

    file_name = default_storage.save("test.csv", csv_file)
    job = ImportJob.objects.create(user=user, file_name=file_name, status="pending")
    result = import_csv_task(job.id)  # Редирект после успеха
    assert "Успешно загружено: 2" in result
    assert Transaction.objects.count() == 2  # Создалось 2 транзакции

    csv_file_2 = SimpleUploadedFile("test.csv", csv_content, content_type="text/csv")
    response2 = auth_client.post("/upload-csv/", {"file": csv_file_2})
    print(f"Количество транзакций после первого импорта: {Transaction.objects.count()}")
    print(f"Response context: {response1.context}")
    assert response2.status_code == 302
    # Проверяем, что количество НЕ изменилось (дубликаты не создались)
    assert (
        Transaction.objects.count() == 2
    )  # это контракт. Мы говорим: «Система гарантирует, что повторный импорт не создает дублей».


@pytest.mark.django_db(transaction=True)
def test_empty_csv_import(user):
    """
    Проверяет, что пустой CSV-файл не роняет задачу,
    а возвращает сообщение об успехе с 0 загруженных.
    """
    # Создаем пустой CSV (только заголовки)
    csv_content = b"type,amount,category,date,description\n"
    csv_file = SimpleUploadedFile("empty.csv", csv_content, content_type="text/csv")

    # Сохраняем файл и вызываем задачу напрямую
    file_name = default_storage.save("empty.csv", csv_file)
    job = ImportJob.objects.create(user=user, file_name=file_name, status="pending")
    result = import_csv_task(job.id)

    # Проверяем, что задача вернула успех с 0
    assert "Успешно загружено: 0" in result
    assert Transaction.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_broken_csv_import(user):
    """
    Проверяет, что CSV с неправильной структурой (нет заголовков)
    не роняет задачу, а возвращает ошибку.
    """
    # CSV без заголовков (только данные)
    csv_content = b"expense,150.50,Food,2026-11-01,Lunch\n"
    csv_file = SimpleUploadedFile("broken.csv", csv_content, content_type="text/csv")

    file_name = default_storage.save("broken.csv", csv_file)
    job = ImportJob.objects.create(user=user, file_name=file_name, status="pending")
    result = import_csv_task(job.id)

    # Задача должна вернуть ошибку (или сообщение о 0 загруженных)
    # Главное — она не должна упасть с KeyError
    assert "Ошибка" in result or "Успешно загружено: 0" in result
    assert Transaction.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_import_task_is_idempotent_on_retry(user):
    """
    Повторный вызов задачи для уже выполненного job
    не должен менять счётчики и не должен падать.
    """
    csv_content = (
        b"type,amount,category,date,description\n"
        b"expense,150.50,Food,2026-11-01,Lunch\n"
    )
    csv_file = SimpleUploadedFile("retry.csv", csv_content, content_type="text/csv")
    file_name = default_storage.save("retry.csv", csv_file)
    job = ImportJob.objects.create(user=user, file_name=file_name, status="pending")

    # Первый прогон
    result1 = import_csv_task(job.id)
    assert "Успешно загружено: 1" in result1
    job.refresh_from_db()
    assert job.status == "done"
    assert job.created_count == 1
    assert job.skipped_count == 0
    assert Transaction.objects.count() == 1

    # Второй прогон того же job — должен быть ранний выход
    result2 = import_csv_task(job.id)
    assert "Уже выполнено ранее" in result2

    job.refresh_from_db()
    assert job.status == "done"
    assert job.created_count == 1  # не изменилось
    assert job.skipped_count == 0  # не изменилось
    assert Transaction.objects.count() == 1  # дублей нет


@pytest.mark.django_db(transaction=True)
def test_import_with_broken_date_skips_row(user):
    """Проверяет, что строка с неверной датой пропускается, а не сохраняется с сегодняшней."""
    csv_content = (
        b"type,amount,category,date,description\n"
        b"expense,150.50,Food,INVALID_DATE,Lunch\n"
        b"income,1000.00,Salary,2026-11-05,November\n"
    )
    csv_file = SimpleUploadedFile(
        "broken_date.csv", csv_content, content_type="text/csv"
    )
    file_name = default_storage.save("broken_date.csv", csv_file)
    job = ImportJob.objects.create(user=user, file_name=file_name, status="pending")

    import_csv_task(job.id)

    job.refresh_from_db()
    # Должна сохраниться только одна транзакция (с валидной датой)
    assert job.created_count == 1
    assert job.skipped_count == 1
    assert Transaction.objects.count() == 1
    assert Transaction.objects.first().amount == 1000
