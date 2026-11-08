from django.contrib import admin
from django.urls import include, path
from django.views.generic import ListView
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views
from tracker.models import Transaction
from tracker.views import (
    CategoryViewSet,
    TransactionViewSet,
    add_transaction,
    upload_csv,
)

router = DefaultRouter()                                                     # Создаём роутер и регистрируем ViewSet
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('admin/', admin.site.urls),                                         # Подключаем API по префиксу /api/
    path('api/', include(router.urls)),
    path('', ListView.as_view(                                  # ListView — это встроенное представление Django. Оно берет модель Transaction, фильтрует (по умолчанию все) и передает в шаблон. Нам не нужно писать View для списка.
        model=Transaction,
        template_name='tracker/transaction_list.html',
        context_object_name='transactions'
    ), name='transaction_list'),
    path('add/', add_transaction, name='add_transaction'),
    path('upload-csv/', upload_csv, name='upload_csv'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('upload-csv/', upload_csv, name='upload_csv'),
]

