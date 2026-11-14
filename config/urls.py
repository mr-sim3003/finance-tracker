from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from tracker.views import (
    TransactionDeleteView,
    TransactionListView,
    TransactionUpdateView,
    add_transaction,
    upload_csv,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('tracker.api.urls')),  # <--- API здесь
    path('', TransactionListView.as_view(), name='transaction_list'),

    path('add/', add_transaction, name='add_transaction'),
    path('edit/<int:pk>/', TransactionUpdateView.as_view(), name='transaction_edit'),
    path('delete/<int:pk>/', TransactionDeleteView.as_view(), name='transaction_delete'),
    
    path('upload-csv/', upload_csv, name='upload_csv'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='transaction_list'), name='logout'),
]
