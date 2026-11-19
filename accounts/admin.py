"""
Настройка админ-панели для приложения accounts.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Кастомизация отображения пользователей в админке.
    Наследуемся от UserAdmin, чтобы сохранить стандартные поля и логику.
    """
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets
    add_fieldsets = UserAdmin.add_fieldsets