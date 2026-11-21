"""
Формы приложения accounts.

Содержит формы для регистрации и удаления аккаунта.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """
    Форма регистрации на основе кастомной модели пользователя.
    """

    class Meta:
        model = CustomUser
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update({"placeholder": "Имя пользователя"})
        self.fields["email"].widget.attrs.update(
            {"placeholder": "Email (необязательно)"}
        )
        self.fields["password1"].widget.attrs.update({"placeholder": "Пароль"})
        self.fields["password2"].widget.attrs.update(
            {"placeholder": "Повторите пароль"}
        )


class DeleteAccountForm(forms.Form):
    """
    Форма подтверждения удаления аккаунта.
    Требует ввода пароля, чтобы случайно не удалить аккаунт.
    """

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"placeholder": "Введите пароль для подтверждения"}
        ),
        label="Пароль",
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        assert self.user is not None, "DeleteAccountForm requires 'user' argument"
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if self.user and not self.user.check_password(password):
            raise forms.ValidationError("Неверный пароль.")
        return password


class UserProfileForm(forms.ModelForm):
    """Форма для редактирования имени пользователя и email."""

    class Meta:
        model = CustomUser
        fields = ("username", "email")
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Имя пользователя"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = False
