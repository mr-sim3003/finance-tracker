import calendar
from datetime import date, datetime

import redis
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import default_storage
from django.db import connection
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, ListView, UpdateView

from .forms import CSVUploadForm, TransactionForm
from .models import ImportJob, Transaction
from .tasks import import_csv_task


@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)                # Передаем user
        if form.is_valid():
            transaction = form.save(commit=False)                              # form.save(commit=False) — мы не сохраняем сразу, потому что нам нужно добавить owner (владельца). Без commit=False Django попытался бы сохранить транзакцию без владельца и выдал бы ошибку.
            transaction.owner = request.user                                # Привязываем владельца
            transaction.save()                                           # Сохраняем
            return redirect('transaction_list')                            # после успешного сохранения перенаправляем на список транзакций (чтобы не было повторной отправки формы при обновлении страницы).
    else:
        form = TransactionForm(user=request.user)

    return render(request, 'tracker/add_transaction.html', {'form': form})


@login_required
def upload_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)

        if form.is_valid():
            csv_file = request.FILES['file']  

            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Файл должен быть в формате CSV.')
                return redirect('upload_csv')   
                     
            # 1. Сохраняем файл на диск (как и раньше)
            file_name = default_storage.save(csv_file.name, csv_file)
            
            # 2. Создаём ЗАПИСЬ В БД о том, что импорт начался (NEW!)
            job = ImportJob.objects.create(
                user=request.user,
                file_name=file_name,
                status='pending'  # начальный статус
            )
            
            # 3. Передаём в Celery ID задачи (а не user_id + file_name)
            import_csv_task.delay(job.id)
            
            messages.success(request, 'Файл принят в обработку. Результат появится чуть позже.')
            return redirect('transaction_list')
        
    else:
        form = CSVUploadForm()

    return render(request, 'tracker/upload_csv.html', {'form': form})

class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'tracker/add_transaction.html'  
    success_url = reverse_lazy('transaction_list')

    def get_queryset(self):
        return Transaction.objects.filter(owner=self.request.user)  # ВАЖНО: Защита от IDOR. Пользователь может редактировать только СВОИ транзакции

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()   # Передаем пользователя в форму, чтобы в выпадающем списке были только его категории
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Транзакция успешно обновлена.')
        return super().form_valid(form)


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    template_name = 'tracker/transaction_confirm_delete.html' 
    success_url = reverse_lazy('transaction_list')

    def get_queryset(self):
        return Transaction.objects.filter(owner=self.request.user) # ВАЖНО: Пользователь может удалять только СВОИ транзакции

    def form_valid(self, form):
        messages.success(self.request, 'Транзакция удалена.')
        return super().form_valid(form)

class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'tracker/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 15  # Пагинация внутри месяца

    def get_queryset(self):
        # 1. Определяем, за какой месяц показывать данные
        month_param = self.request.GET.get('month')
        try:
            # Пытаемся распарсить YYYY-MM
            parsed_date = datetime.strptime(month_param, '%Y-%m').date() if month_param else date.today()
        except ValueError:
            parsed_date = date.today()

        # 2. Вычисляем первый и последний день месяца
        first_day = parsed_date.replace(day=1)
        last_day = parsed_date.replace(day=calendar.monthrange(parsed_date.year, parsed_date.month)[1])

        # 3. Сохраняем для использования в шаблоне
        self.current_month = parsed_date
        self.first_day = first_day
        self.last_day = last_day

        # 4. Фильтруем транзакции пользователя за этот период
        return Transaction.objects.filter(
            owner=self.request.user,
            date__gte=first_day,
            date__lte=last_day
        ).select_related('category').order_by('-date', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['current_month'] = self.current_month
        context['month_name'] = self.current_month.strftime('%B %Y')
        
        prev_month_date = self.first_day - relativedelta(months=1)
        next_month_date = self.first_day + relativedelta(months=1)
        
        context['prev_month'] = prev_month_date.strftime('%Y-%m')
        context['next_month'] = next_month_date.strftime('%Y-%m')

        # Подсчет сумм за месяц ---
        # Берем все транзакции пользователя за этот месяц (без учета пагинации!)
        month_transactions = Transaction.objects.filter(
            owner=self.request.user,
            date__gte=self.first_day,
            date__lte=self.last_day
        )

        # Считаем сумму доходов (type='income')
        income_sum = month_transactions.filter(type='income').aggregate(total=Sum('amount'))['total'] or 0
        
        # Считаем сумму расходов (type='expense')
        expense_sum = month_transactions.filter(type='expense').aggregate(total=Sum('amount'))['total'] or 0

        context['total_income'] = income_sum
        context['total_expense'] = expense_sum
        context['balance'] = income_sum - expense_sum  # Баланс (доходы минус расходы)

        return context

class ImportJobListView(LoginRequiredMixin, ListView):
    model = ImportJob
    template_name = 'tracker/import_job_list.html'
    context_object_name = 'jobs'
    paginate_by = 10

    def get_queryset(self):
        return ImportJob.objects.filter(user=self.request.user)

def healthz(request):
    """Проверка живости приложения: БД, Redis."""
    health = {'status': 'ok', 'services': {}}
    
    # 1. Проверка PostgreSQL
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health['services']['db'] = 'ok'
    except Exception as e: # noqa: BLE001
        health['services']['db'] = f'error: {e!s}'
        health['status'] = 'degraded'
    
    # 2. Проверка Redis
    try:
        redis_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://redis:6379/0')
        # Redis URL может быть в формате redis://host:port/db
        r = redis.from_url(redis_url)
        r.ping()
        health['services']['redis'] = 'ok'
    except Exception as e: # noqa: BLE001
        health['services']['redis'] = f'error: {e!s}'
        health['status'] = 'degraded'
    
    status_code = 200 if health['status'] == 'ok' else 503
    return JsonResponse(health, status=status_code)