from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from tracker.views import CategoryViewSet, TransactionViewSet

# Создаём роутер и регистрируем наши ViewSet
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('admin/', admin.site.urls),
    # Подключаем API по префиксу /api/
    path('api/', include(router.urls)),
]