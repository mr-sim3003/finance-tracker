import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from rest_framework.test import APIClient

from tracker.models import Category, Transaction


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
                                                                                            
    assert response.data['count'] == 1                                      # Проверяем count в пагинации
    assert len(response.data['results']) == 1                                           # Проверяем длину списка results
    assert response.data['results'][0]['id'] == t1.id                                    # Проверяем ID в results                                         
                                                                                            
                                     


                                                                                       
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

@pytest.mark.django_db
def test_upload_non_csv_file_rejected(auth_client, user):
    """
    Проверяет, что файл с расширением .txt отклоняется.
    View должен вернуть редирект (302) и сообщение об ошибке.
    """
    # Создаем файл с расширением .txt
    txt_file = SimpleUploadedFile(
        "test.txt", 
        b"some text content", 
        content_type="text/plain"
    )
    
    response = auth_client.post('/upload-csv/', {'file': txt_file})
    
    # Проверяем, что View вернул редирект (302), а не 200
    assert response.status_code == 302
    
    # Проверяем, что транзакции НЕ создались
    assert Transaction.objects.count() == 0


@pytest.mark.django_db
def test_amount_exceeds_max_digits(auth_client, user):
    """
    Проверяет, что сумма, которая не влезает в max_digits=12,
    возвращает 400 Bad Request.
    """
    category = Category.objects.create(name="Food", owner=user)
    
    # 11 цифр до запятой + 2 после = 13 цифр (больше max_digits=12)
    response = auth_client.post('/api/transactions/', {
        'type': 'income',
        'amount': '10000000000.00',  # 10 миллиардов
        'category': category.id,
        'date': '2026-11-02',
    })
    
    assert response.status_code == 400
    assert 'amount' in response.data

@pytest.mark.django_db
def test_user_cannot_modify_other_users_transaction(auth_client, user):
    """
    Проверяет, что пользователь не может получить, изменить или удалить
    чужую транзакцию. Все три операции должны возвращать 404.
    """
    # Создаем второго пользователя и его транзакцию
    User = get_user_model()
    user2 = User.objects.create_user(username='user2', password='password2')
    cat2 = Category.objects.create(name="Food", owner=user2)
    t2 = Transaction.objects.create(
        type='income', 
        amount=100, 
        category=cat2, 
        owner=user2, 
        date='2026-11-02'
    )
    
    # Логинимся под ПЕРВЫМ пользователем
    auth_client.force_authenticate(user=user)
    
    # Пытаемся получить чужую транзакцию
    response_get = auth_client.get(f'/api/transactions/{t2.id}/')
    assert response_get.status_code == 404
    
    # Пытаемся изменить чужую транзакцию
    response_patch = auth_client.patch(f'/api/transactions/{t2.id}/', {'amount': '999.99'})
    assert response_patch.status_code == 404
    
    # Пытаемся удалить чужую транзакцию
    response_delete = auth_client.delete(f'/api/transactions/{t2.id}/')
    assert response_delete.status_code == 404
    
    # Проверяем, что транзакция не изменилась и не удалилась
    t2.refresh_from_db()
    assert t2.amount == 100
    assert Transaction.objects.filter(id=t2.id).exists()



@pytest.mark.django_db
def test_unique_category_per_user(user):
    """
    Проверяет, что нельзя создать две одинаковые категории
    у одного пользователя (UniqueConstraint на owner+name).
    """
    # Создаем первую категорию
    Category.objects.create(name="Food", owner=user)
    
    # Пытаемся создать вторую с тем же именем и владельцем
    with pytest.raises(IntegrityError):
        Category.objects.create(name="Food", owner=user)


@pytest.mark.django_db
def test_user_cannot_edit_other_users_transaction(client, user):
    User = get_user_model() # 1. Создаем второго пользователя и его транзакцию
    user2 = User.objects.create_user(username='user2', password='password2')
    cat2 = Category.objects.create(name="Food", owner=user2)

    t2 = Transaction.objects.create(
        type='income', amount=100, category=cat2, owner=user2, date='2026-11-02'
    )
    client.force_login(user)                       # 2. Логинимся под ПЕРВЫМ пользователем
    
    response = client.get(f'/edit/{t2.id}/')        # 3. Пытаемся открыть страницу редактирования чужой транзакции   
    assert response.status_code == 404               # 4. Должна быть 404 (Not Found)
    
    response_delete = client.get(f'/delete/{t2.id}/') # 5. Пытаемся удалить чужую транзакцию
    assert response_delete.status_code == 404

@pytest.mark.django_db
def test_user_can_edit_own_transaction(client, user):
    cat = Category.objects.create(name="Food", owner=user) # Создаем свою транзакцию

    t1 = Transaction.objects.create(
        type='income', amount=100, category=cat, owner=user, date='2026-11-02'
    )
    client.force_login(user)

    response = client.get(f'/edit/{t1.id}/')               # Открываем свою транзакцию — должна быть 200 (OK)
    assert response.status_code == 200