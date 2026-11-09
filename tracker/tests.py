import pytest
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from tracker.models import Category, Transaction
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

                                                                                       
@pytest.mark.django_db                     # Тест 1: Нельзя создать транзакцию с отрицательной суммой
def test_cannot_create_transaction_with_negative_amount(auth_client, user):
    category = Category.objects.create(name="Food", owner=user) 

 # Отправляем POST-запрос с отрицательной суммой                                                                                         
    response = auth_client.post('/api/transactions/', {              
        'type': 'income',
        'amount': '-100.00',
        'category': category.id,
        'date': '2026-11-02',
        'description': 'Test negative'
    })                                                         
    
                                                                                            
    assert response.status_code == 400                                       # Проверяем, что API вернул 400 Bad Request
                                                                                           
    assert 'amount' in response.data                                        # Проверяем, что ошибка именно в поле amount



                                                                                        
@pytest.mark.django_db                                                       # Тест 2: Пользователь видит только свои транзакции
def test_user_sees_only_own_transactions(api_client, user):
                                                                                           
    User = get_user_model()                                                    # Создаём второго пользователя
    user2 = User.objects.create_user(username='user2', password='password2')
    
                                                                                           
    cat1 = Category.objects.create(name="Food", owner=user)                      # Создаём категории и транзакции для обоих пользователей
    cat2 = Category.objects.create(name="Transport", owner=user2)
    
    t1 = Transaction.objects.create(type='income', amount=100, category=cat1, owner=user, date='2026-11-02')
    Transaction.objects.create(type='expense', amount=50, category=cat2, owner=user2, date='2026-11-02')
    
                                                                                            
    api_client.force_authenticate(user=user)                                      # Логинимся под ПЕРВЫМ пользователем
    
                                                                                            
    response = api_client.get('/api/transactions/')                                 # Запрашиваем список транзакций
    
                                                                                            
    assert response.status_code == 200                                                # Проверяем, что вернулся 200 OK
                                                                                            
    assert len(response.data) == 1                                                  # Проверяем, что в списке ТОЛЬКО 1 транзакция (t1)
                                                                                            
    assert response.data[0]['id'] == t1.id                                           # Проверяем, что это именно транзакция t1, а не t2


                                                                                       
@pytest.mark.django_db                                                            # Тест 3: Успешное создание транзакции
def test_create_valid_transaction(auth_client, user):
    category = Category.objects.create(name="Salary", owner=user)
    # auth_client — это фикстура из pytest-django, которая имитирует залогиненного пользователя. Твой View upload_csv защищен @login_required, поэтому без этого тест упал бы с 302 (редирект на логин).
    response = auth_client.post('/api/transactions/', {
        'type': 'income',
        'amount': '500.00',
        'category': category.id,
        'date': '2026-11-03',
        'description': 'Valid income'
    })
    
    assert response.status_code == 201
    assert Transaction.objects.count() == 1
    assert Transaction.objects.first().amount == 500


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
    result = import_csv_task(user.id, file_name)                                                                           # Редирект после успеха
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