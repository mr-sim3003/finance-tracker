import pytest
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from tracker.models import Transaction
from tracker.tasks import import_csv_task


@pytest.fixture                            # Фикстура: создаёт тестового пользователя
def user(db):
    User = get_user_model()
    return User.objects.create_user(username='testuser', password='testpassword')

                                                                                        
@pytest.fixture                                   # Фикстура: создаёт API-клиент
def api_client():
    return APIClient()

                                                                                        
@pytest.fixture                                    # Фикстура: авторизует клиент
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client

@pytest.mark.django_db(transaction=True)
def test_csv_import_is_idempotent(auth_client, user):
    
    csv_content = b"type,amount,category,date,description\n"                 #  Готовим CSV-файл в памяти
    csv_content += b"expense,150.50,Food,2026-11-01,Lunch\n"
    csv_content += b"income,1000.00,Salary,2026-11-05,November\n"
    # SimpleUploadedFile — это способ имитировать файл, который пользователь загружает через форму. Нам не нужен реальный файл на диске, достаточно «байтов в памяти».      
    csv_file = SimpleUploadedFile(
        "test.csv", 
        csv_content, 
        content_type="text/csv"
    )
    response1 = auth_client.post('/upload-csv/', {'file': csv_file})                    #  Загружаем файл ПЕРВЫЙ.  проверяет, что импорт работает
    assert response1.status_code == 302  
    file_name = default_storage.save("test.csv", csv_file)
    _ = import_csv_task(user.id, file_name)                                                                           # Редирект после успеха
    assert Transaction.objects.count() == 2                                           # Создалось 2 транзакции      

    csv_file_2 = SimpleUploadedFile(
        "test.csv", 
        csv_content, 
        content_type="text/csv"
    )
    response2 = auth_client.post('/upload-csv/', {'file': csv_file_2})
    print(f"Количество транзакций после первого импорта: {Transaction.objects.count()}")
    print(f"Response context: {response1.context}") 
    assert response2.status_code == 302
    # Проверяем, что количество НЕ изменилось (дубликаты не создались)
    assert Transaction.objects.count() == 2  # это контракт. Мы говорим: «Система гарантирует, что повторный импорт не создает дублей».

@pytest.mark.django_db(transaction=True)
def test_empty_csv_import(user):
    """
    Проверяет, что пустой CSV-файл не роняет задачу,
    а возвращает сообщение об успехе с 0 загруженных.
    """   
    # Создаем пустой CSV (только заголовки)
    csv_content = b"type,amount,category,date,description\n"
    csv_file = SimpleUploadedFile(
        "empty.csv", 
        csv_content, 
        content_type="text/csv"
    )
    
    # Сохраняем файл и вызываем задачу напрямую
    file_name = default_storage.save("empty.csv", csv_file)
    result = import_csv_task(user.id, file_name)
    
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
    csv_file = SimpleUploadedFile(
        "broken.csv", 
        csv_content, 
        content_type="text/csv"
    )
    
    file_name = default_storage.save("broken.csv", csv_file)
    result = import_csv_task(user.id, file_name)
    
    # Задача должна вернуть ошибку (или сообщение о 0 загруженных)
    # Главное — она не должна упасть с KeyError
    assert "Ошибка" in result or "Успешно загружено: 0" in result
    assert Transaction.objects.count() == 0