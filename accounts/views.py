"""
Views приложения accounts.

Обрабатывает регистрацию, просмотр профиля, редактирование и удаление аккаунта.(CRUD)
"""
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from .forms import CustomUserCreationForm, DeleteAccountForm, UserProfileForm
from .models import CustomUser


def register(request):
    """Регистрация нового пользователя с автоматическим входом."""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # login() создает сессию для пользователя сразу после регистрации,
            # чтобы ему не приходилось вводить пароль еще раз.
            login(request, user)  
            return redirect('tracker:transaction_list')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


@login_required
def profile(request):
    """Страница с информацией о пользователе."""
    return render(request, 'registration/profile.html')


@login_required
def delete_account(request):
    """
    Удаление аккаунта.
    
    Требует подтверждения паролем (через форму), чтобы избежать
    случайного удаления данных.
    """
    if request.method == 'POST':
        form = DeleteAccountForm(request.POST, user=request.user)
        if form.is_valid():
            user = request.user
            # Сначала разлогиниваем, потом удаляем: 
            # после удаления объект request.user станет невалидным.
            logout(request) 
            user.delete()
            return redirect('tracker:transaction_list')
    else:
        form = DeleteAccountForm(user=request.user)

    return render(request, 'registration/delete_account.html', {'form': form})

class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    Редактирование имени пользователя и email.
    
    Используем UpdateView, так как это стандартный кейс: 
    форма + сохранение + редирект. Переопределяем только get_object,
    чтобы всегда брать текущего пользователя (защита от IDOR).
    """
    model = CustomUser
    form_class = UserProfileForm
    template_name = 'registration/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        # Возвращаем именно текущего пользователя, 
        # чтобы нельзя было через URL поменять чужой профиль (защита от IDOR).
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Профиль успешно обновлен.')
        return super().form_valid(form)