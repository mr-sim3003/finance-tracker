"""
Корневая URL-схема проекта.

Знает только: admin, два приложения (tracker, accounts) и spectacular.
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
    path("admin/", admin.site.urls),
    # Приложения.
    path("", include("tracker.urls")),
    path("accounts/", include("accounts.urls")),
    # OpenAPI / Swagger / ReDoc.
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
