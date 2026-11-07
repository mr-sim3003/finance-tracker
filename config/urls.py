from django.contrib import admin
from django.urls import include, path
from django.views.generic import ListView
from rest_framework.routers import DefaultRouter

from tracker.models import Transaction
from tracker.views import CategoryViewSet, TransactionViewSet, add_transaction

router = DefaultRouter()                                                     # Создаём роутер и регистрируем ViewSet
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('admin/', admin.site.urls),                                         # Подключаем API по префиксу /api/
    path('api/', include(router.urls)),
    path('', ListView.as_view(
        model=Transaction,
        template_name='tracker/transaction_list.html',
        context_object_name='transactions'
    ), name='transaction_list'),
    path('add/', add_transaction, name='add_transaction'),
]

