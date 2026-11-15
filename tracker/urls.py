"""
URL-схема приложения tracker.

app_name='tracker' — namespace: в шаблонах пишем {% url 'tracker:...' %},
во view — redirect('tracker:...'). Защищает от коллизий имён, если
в другом приложении появится view с тем же именем (например, 'login').
"""
from django.urls import include, path

from .health import healthz
from .imports import ImportJobListView, upload_csv
from .views import (
    TransactionDeleteView,
    TransactionListView,
    TransactionUpdateView,
    add_transaction,
)

app_name = 'tracker'

urlpatterns = [
    # Транзакции
    path('', TransactionListView.as_view(), name='transaction_list'),
    path('add/', add_transaction, name='add_transaction'),
    path('edit/<int:pk>/', TransactionUpdateView.as_view(), name='transaction_edit'),
    path('delete/<int:pk>/', TransactionDeleteView.as_view(), name='transaction_delete'),

    # Импорт CSV
    path('upload-csv/', upload_csv, name='upload_csv'),
    path('import-jobs/', ImportJobListView.as_view(), name='import_job_list'),

    # Healthcheck
    path('healthz/', healthz, name='healthz'),

    # DRF API (роутер уже есть в tracker/api/urls.py)
    path('api/', include('tracker.api.urls')),
]