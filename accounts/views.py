
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import CustomUserCreationForm, DeleteAccountForm


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # автоматический вход после регистрации
            return redirect('transaction_list')
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile(request):
    """Страница профиля пользователя."""
    return render(request, 'registration/profile.html')

@login_required
def delete_account(request):
    if request.method == 'POST':
        form = DeleteAccountForm(request.POST, user=request.user)
        if form.is_valid():
            user = request.user
            logout(request)
            user.delete()
            return redirect('transaction_list')
    else:
        form = DeleteAccountForm(user=request.user)

    return render(request, 'registration/delete_account.html', {'form': form})
