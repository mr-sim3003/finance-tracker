from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import default_storage
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import DeleteView, UpdateView

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