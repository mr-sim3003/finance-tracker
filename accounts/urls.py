"""
URL-схема приложения accounts.

app_name='accounts' создает namespace, чтобы URL-ы не конфликтовали
с другими приложениями.
"""

from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from .views import UserProfileUpdateView, delete_account, profile, register

app_name = "accounts"

urlpatterns = [
    # Регистрация / профиль
    path("register/", register, name="register"),
    path("profile/", profile, name="profile"),
    # Смена пароля (используем встроенные CBV Django).
    path(
        "password-change/",
        auth_views.PasswordChangeView.as_view(
            success_url=reverse_lazy("accounts:password_change_done")
        ),
        name="password_change",
    ),
    path(
        "password-change/done/",
        auth_views.PasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    # Смена имени или email
    path("profile/edit/", UserProfileUpdateView.as_view(), name="profile_edit"),
    # Удаление аккаунта
    path("delete/", delete_account, name="delete_account"),
    # Логин / логаут.
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="tracker:transaction_list"),
        name="logout",
    ),
]
