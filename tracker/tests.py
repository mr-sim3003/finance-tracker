import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from tracker.models import Category, Transaction


                                                                                        # Фикстура: создаёт тестового пользователя
@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(username='testuser', password='testpassword')

                                                                                        # Фикстура: создаёт API-клиент
@pytest.fixture
def api_client():
    return APIClient()

                                                                                        # Фикстура: авторизует клиент
@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client

                                                                                        # Тест 1: Нельзя создать транзакцию с отрицательной суммой
@pytest.mark.django_db
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
    
                                                                                            # Проверяем, что API вернул 400 Bad Request
    assert response.status_code == 400
                                                                                            # Проверяем, что ошибка именно в поле amount
    assert 'amount' in response.data



                                                                                        # Тест 2: Пользователь видит только свои транзакции
@pytest.mark.django_db
def test_user_sees_only_own_transactions(api_client, user):
                                                                                            # Создаём второго пользователя
    User = get_user_model()
    user2 = User.objects.create_user(username='user2', password='password2')
    
                                                                                            # Создаём категории и транзакции для обоих пользователей
    cat1 = Category.objects.create(name="Food", owner=user)
    cat2 = Category.objects.create(name="Transport", owner=user2)
    
    t1 = Transaction.objects.create(type='income', amount=100, category=cat1, owner=user, date='2026-11-02')
    Transaction.objects.create(type='expense', amount=50, category=cat2, owner=user2, date='2026-11-02')
    
                                                                                            # Логинимся под ПЕРВЫМ пользователем
    api_client.force_authenticate(user=user)
    
                                                                                            # Запрашиваем список транзакций
    response = api_client.get('/api/transactions/')
    
                                                                                            # Проверяем, что вернулся 200 OK
    assert response.status_code == 200
                                                                                            # Проверяем, что в списке ТОЛЬКО 1 транзакция (t1)
    assert len(response.data) == 1
                                                                                            # Проверяем, что это именно транзакция t1, а не t2
    assert response.data[0]['id'] == t1.id


                                                                                        # Тест 3: Успешное создание транзакции
@pytest.mark.django_db
def test_create_valid_transaction(auth_client, user):
    category = Category.objects.create(name="Salary", owner=user)
    
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