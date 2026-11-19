import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(username='testuser', password='testpassword')

@pytest.mark.django_db
def test_register_user(client):
    """Проверяет, что регистрация создаёт пользователя и логинит его."""
    response = client.post(reverse('accounts:register'), {
        'username': 'newuser',
        'email': 'new@example.com',
        'password1': 'testpass123',
        'password2': 'testpass123',
    })

    # После регистрации — редирект на главную
    assert response.status_code == 302
    assert response.url == reverse('tracker:transaction_list')

    # Пользователь создан
    User = get_user_model()
    user = User.objects.get(username='newuser')
    assert user.email == 'new@example.com'

    # Пользователь залогинен
    assert '_auth_user_id' in client.session


@pytest.mark.django_db
def test_register_password_mismatch(client):
    """Проверяет, что при несовпадении паролей пользователь не создаётся."""
    response = client.post(reverse('accounts:register'), {
        'username': 'newuser',
        'email': 'new@example.com',
        'password1': 'testpass123',
        'password2': 'different123',
    })

    
    assert response.status_code == 200
    assert not get_user_model().objects.filter(username='newuser').exists()

@pytest.mark.django_db
def test_admin_can_see_users(client, user):  # <--- добавляем user
    """Проверяет, что админка доступна только суперпользователю."""
    
    # 1. Обычный пользователь не может зайти в админку
    client.login(username='testuser', password='testpassword')
    response = client.get('/admin/')
    assert response.status_code == 302  # редирект на логин админки

    # 2. Суперпользователь может
    User = get_user_model()
    User.objects.create_superuser(username='admin2', password='adminpass') # type: ignore
    client.login(username='admin2', password='adminpass')
    response = client.get('/admin/')
    assert response.status_code == 200

@pytest.mark.django_db
def test_profile_requires_login(client):
    """Проверяет, что профиль доступен только авторизованным."""
    response = client.get('/accounts/profile/')
    assert response.status_code == 302  # редирект на логин
    assert '/accounts/login/' in response.url


@pytest.mark.django_db
def test_profile_shows_user_info(client, user):
    """Проверяет, что профиль показывает данные пользователя."""
    client.force_login(user)
    response = client.get('/accounts/profile/')
    assert response.status_code == 200
    assert user.username in response.content.decode()


@pytest.mark.django_db
def test_password_change(client, user):
    """Проверяет, что смена пароля работает."""
    client.force_login(user)
    response = client.post('/accounts/password-change/', {
        'old_password': 'testpassword',
        'new_password1': 'newtestpass123',
        'new_password2': 'newtestpass123',
    })
    assert response.status_code == 302  # редирект на "пароль изменён"

    # Проверяем, что пароль реально изменился
    user.refresh_from_db()
    assert user.check_password('newtestpass123')

@pytest.mark.django_db
def test_delete_account_requires_login(client):
    """Проверяет, что удаление доступно только авторизованным."""
    response = client.get('/accounts/delete/')
    assert response.status_code == 302
    assert '/accounts/login/' in response.url


@pytest.mark.django_db
def test_delete_account_wrong_password(client, user):
    """Проверяет, что с неверным паролем аккаунт не удаляется."""
    client.force_login(user)
    response = client.post('/accounts/delete/', {'password': 'wrongpass'})
    
    # Форма невалидна — остаёмся на странице (200)
    assert response.status_code == 200
    assert get_user_model().objects.filter(username='testuser').exists()


@pytest.mark.django_db
def test_delete_account_success(client, user):
    """Проверяет, что с верным паролем аккаунт удаляется."""
    client.force_login(user)
    response = client.post('/accounts/delete/', {'password': 'testpassword'})
    
    # Редирект на главную
    assert response.status_code == 302
    assert response.url == '/'
    
    # Пользователь удалён
    assert not get_user_model().objects.filter(username='testuser').exists()
    
    # Пользователь разлогинен
    assert '_auth_user_id' not in client.session

@pytest.mark.django_db
def test_profile_update(client, user):
    """Проверяет, что пользователь может изменить свое имя и email."""
    client.force_login(user)
    response = client.post('/accounts/profile/edit/', {
        'username': 'newname',
        'email': 'new@example.com',
    })
    assert response.status_code == 302  # редирект в профиль
    
    user.refresh_from_db()
    assert user.username == 'newname'
    assert user.email == 'new@example.com'