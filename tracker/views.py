import calendar
from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import default_storage
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, ListView, UpdateView

from .forms import CSVUploadForm, TransactionForm
from .models import Transaction
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
                     
            file_name = default_storage.save(csv_file.name, csv_file)                           #  сохраняет файл на диск (например, в /app/media/), чтобы Celery мог его прочитать из другого процесса.                    
            import_csv_task.delay(request.user.id, file_name)                                    # Запускаем задачу в фоне Метод .delay() не выполняет задачу сразу. Он кладет задачу в очередь Redis и сразу возвращает управление. Пользователь сразу видит сообщение «Файл принят в обработку», не дожидаясь, пока парсинг закончится.    
            messages.success(request, 'Файл принят в обработку. Результат появится чуть позже.')  # Воркер Celery (отдельный процесс) забирает задачу из Redis и выполняет import_csv_task.
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