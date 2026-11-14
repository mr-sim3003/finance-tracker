from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Админка для кастомного пользователя."""
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    
    # Поля, которые можно редактировать в форме пользователя
    fieldsets = UserAdmin.fieldsets  # стандартные поля Django (username, password, email, permissions)
    add_fieldsets = UserAdmin.add_fieldsets  # поля при создании нового пользователя
