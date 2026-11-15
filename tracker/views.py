"""
View-слой транзакций.

Здесь только CRUD и список транзакций. Импорт — в imports.py,
healthcheck — в health.py. Разделение по доменам: имя файла = контекст.
"""
import calendar
from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, ListView, UpdateView

from .forms import TransactionForm
from .models import Transaction


@login_required
def add_transaction(request):
    """
    Ручное добавление транзакции.

    Функция, а не CBV (CreateView): логика простая (форма → save → редирект),
    но есть нюанс — нужно подставить owner до сохранения. CreateView
    потребовал бы переопределять form_valid, что не короче, а менее явно.
    """
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            transaction = form.save(commit=False)
            # commit=False + owner: form.save() не знает о request.user,
            # передача user в форму для сохранения смешивание слоёв.
            # Присвоение owner самый прозрачный вариант.
            transaction.owner = request.user
            transaction.save()
            return redirect('tracker:transaction_list')
    else:
        form = TransactionForm(user=request.user)

    return render(request, 'tracker/add_transaction.html', {'form': form})


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    """
    Редактирование транзакции.

    UpdateView, а не View. стандартный кейс (форма, сохранение, редирект),
    всё переиспользуется. Переопределяем только get_queryset (IDOR)
    и get_form_kwargs (передача user в форму).
    """
    model = Transaction
    form_class = TransactionForm
    template_name = 'tracker/add_transaction.html'
    success_url = reverse_lazy('tracker:transaction_list')

    def get_queryset(self):
        # Защита от IDOR. пользователь может редактировать только свои транзакции.
        # Без этого filter(owner=...) любой мог бы открыть /edit/<чужой_id>/ и увидеть/изменить чужие данные.
        return Transaction.objects.filter(owner=self.request.user)

    def get_form_kwargs(self):
        # Передаём user в форму, чтобы в выпадающем списке категорий были только категории текущего пользователя.
        #  Без этого пользователь увидел бы чужие категории (утечка данных).
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Транзакция успешно обновлена.')
        return super().form_valid(form)


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    """
    Удаление транзакции с подтверждением.

    DeleteView, а не View: стандартный кейс (подтверждение → удаление → редирект).
    Переопределяем только get_queryset (IDOR) и form_valid (сообщение).
    """
    model = Transaction
    template_name = 'tracker/transaction_confirm_delete.html'
    success_url = reverse_lazy('tracker:transaction_list')

    def get_queryset(self):
        # Защита от IDOR: удалять можно только свои транзакции.
        return Transaction.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Транзакция удалена.')
        return super().form_valid(form)


class TransactionListView(LoginRequiredMixin, ListView):
    """
    Список транзакций за месяц с агрегатами.

    ListView, а не View: нужна пагинация + стандартный рендеринг.
    View потребовал бы ручной paginate_by + context + render — то же самое,
    но больше кода. Переопределяем get_queryset (фильтр по месяцу + owner)
    и get_context_data (агрегаты).
    """
    model = Transaction
    template_name = 'tracker/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 15

    def get_queryset(self):
        # 1. Определяем месяц: из GET-параметра или текущий.
        # try/except ValueError — защита от мусора в ?month=(например, ?month=abc).
        #  Без неё был бы 500 вместо фолбэка.
        month_param = self.request.GET.get('month')
        try:
            parsed_date = datetime.strptime(month_param, '%Y-%m').date() if month_param else date.today()
        except ValueError:
            parsed_date = date.today()

        # 2. Первый и последний день месяца.
        first_day = parsed_date.replace(day=1)
        last_day = parsed_date.replace(day=calendar.monthrange(parsed_date.year, parsed_date.month)[1])

        # 3. Сохраняем для get_context_data (там нужны для агрегатов и для ссылок «предыдущий/следующий месяц»).
        self.current_month = parsed_date
        self.first_day = first_day
        self.last_day = last_day

        # 4. Фильтр по owner + месяцу + select_related(category).
        # select_related — чтобы не было N+1 при рендеринге {{ t.category.name }}
        # в шаблоне: один JOIN вместо 15 запросов (по числу транзакций на странице).
        return Transaction.objects.filter(
            owner=self.request.user,
            date__gte=first_day,
            date__lte=last_day,
        ).select_related('category').order_by('-date', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['current_month'] = self.current_month
        context['month_name'] = self.current_month.strftime('%B %Y')

        prev_month_date = self.first_day - relativedelta(months=1)
        next_month_date = self.first_day + relativedelta(months=1)
        context['prev_month'] = prev_month_date.strftime('%Y-%m')
        context['next_month'] = next_month_date.strftime('%Y-%m')

        # Агрегаты считаем по ВСЕМ транзакциям месяца, а не по странице:
        # пагинация режет queryset, но суммы должны быть за месяц целиком.
        # Поэтому отдельный queryset, а не self.object_list.
        month_transactions = Transaction.objects.filter(
            owner=self.request.user,
            date__gte=self.first_day,
            date__lte=self.last_day,
        )

        # or 0 — на случай пустого месяца: aggregate(Sum) вернёт None,
        # а шаблон ждёт число ({{ total_income }} ₽).
        income_sum = month_transactions.filter(type='income').aggregate(total=Sum('amount'))['total'] or 0
        expense_sum = month_transactions.filter(type='expense').aggregate(total=Sum('amount'))['total'] or 0

        context['total_income'] = income_sum
        context['total_expense'] = expense_sum
        context['balance'] = income_sum - expense_sum

        return context


