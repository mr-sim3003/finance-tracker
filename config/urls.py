"""
Корневая URL-схема проекта.

Знает только: admin, два приложения (tracker, accounts) и spectacular.
Внутренности приложений — не его дело: /add/, /login/ и т.д. описаны
в tracker/urls.py и accounts/urls.py соответственно.
"""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Админка
    path('admin/', admin.site.urls),

    # Приложения.
    # tracker — без префикса: главная = список транзакций (/),
    # поэтому include('') сохраняет обратную совместимость URL
    # (/add/, /edit/1/, /upload-csv/). Если бы был path('tracker/', ...),
    # все URL съехали бы на /tracker/add/ и тесты покраснели бы.
    path('', include('tracker.urls')),
    path('accounts/', include('accounts.urls')),

    # OpenAPI / Swagger / ReDoc.
    # Здесь, а не в приложении: это документация ВСЕГО API проекта,
    # а не конкретного приложения.
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
