from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import ListView

from tracker.models import Transaction
from tracker.views import add_transaction, upload_csv

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('tracker.api.urls')),  # <--- API здесь
    path('', ListView.as_view(
        model=Transaction,
        template_name='tracker/transaction_list.html',
        context_object_name='transactions'
    ), name='transaction_list'),
    path('add/', add_transaction, name='add_transaction'),
    path('upload-csv/', upload_csv, name='upload_csv'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
]
