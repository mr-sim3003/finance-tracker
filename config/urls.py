from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from tracker.views import (
    ImportJobListView,
    TransactionDeleteView,
    TransactionListView,
    TransactionUpdateView,
    add_transaction,
    upload_csv,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    #  API 
    path('api/', include('tracker.api.urls')),

    # Swagger / OpenAPI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    #  Web 
    path('', TransactionListView.as_view(), name='transaction_list'),
    path('add/', add_transaction, name='add_transaction'),
    path('edit/<int:pk>/', TransactionUpdateView.as_view(), name='transaction_edit'),
    path('delete/<int:pk>/', TransactionDeleteView.as_view(), name='transaction_delete'),
    
    path('upload-csv/', upload_csv, name='upload_csv'),
    path('import-jobs/', ImportJobListView.as_view(), name='import_job_list'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='transaction_list'), name='logout'),
]
