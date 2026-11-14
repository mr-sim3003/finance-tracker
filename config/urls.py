from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from accounts.views import delete_account, profile, register
from tracker.views import (
    ImportJobListView,
    TransactionDeleteView,
    TransactionListView,
    TransactionUpdateView,
    add_transaction,
    healthz,
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
    #  import
    path('upload-csv/', upload_csv, name='upload_csv'),
    path('import-jobs/', ImportJobListView.as_view(), name='import_job_list'),
    #  account
    path('accounts/register/', register, name='register'),
    path('accounts/profile/', profile, name='profile'),
    path('accounts/password-change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('accounts/password-change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    path('accounts/delete/', delete_account, name='delete_account'),
    #  auth
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='transaction_list'), name='logout'),
    
    path('healthz/', healthz, name='healthz'),
]
