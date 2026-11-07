from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Category, Transaction
from .serializers import CategorySerializer, TransactionSerializer


class CategoryViewSet(viewsets.ModelViewSet):                 # дает ему «из коробки» методы для CRUD-операций (создание, чтение, обновление, удаление) над категориями.
    serializer_class = CategorySerializer                      # Указывает, какой сериализатор использовать (CategorySerializer). 
    permission_classes = [IsAuthenticated]                     # Только для авторизованных  # noqa: RUF012

    def get_queryset(self):                                     # Метод get_queryset определяет, какие данные будут доступны для чтения (GET).
        return Category.objects.filter(owner=self.request.user) #функции срабатывают когда обращаються к их функционалу       
                                                                # это шов безопасности. 
                                                                # Он гарантирует, что пользователь увидит только свои категории, а не чужие. 
                                                                # Без этого любой мог бы видеть данные других.

    def perform_create(self, serializer):                         # вызывается автоматически при создании новой категории (POST-запрос).
        serializer.save(owner=self.request.user)                  #функции срабатывают когда обращаються к их функционалу
                                                                # При создании автоматически привязываем к текущему пользователю      
                                                                # — автоматизация. Клиенту не нужно передавать owner в JSON. DRF сам подставит текущего пользователя.
                                                                #  Это защищает от подделки (нельзя создать категорию от имени другого).


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]                               # Только для авторизованных  # noqa: RUF012

    def get_queryset(self):                                             # Фильтрация транзакций по текущему пользователю. 
        return Transaction.objects.filter(owner=self.request.user)      #Это критически важно для финансового трекера (утечка данных недопустима).
                                                                        #функции срабатывают когда обращаються к их функционалу
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)                         #функции срабатывают когда обращаються к их функционалу
                                                                        # При создании автоматически привязываем к текущему пользователю
                                                                        # При создании транзакции owner автоматически берется из запроса (пользователь, который делает запрос).
        



    # ViewSet отвечает за логику доступа (кто может смотреть, кто может создавать).

    # Serializer отвечает за валидацию и преобразование данных.

    # Model отвечает за хранение данных.


    # permission_classes — защита на уровне API (только авторизованные).

    # get_queryset — защита на уровне данных (только свои).

    # perform_create — защита на уровне создания (нельзя подделать владельца).



from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import TransactionForm
from .models import Transaction


@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=request.user)                # Передаем user
        if form.is_valid():
            transaction = form.save(commit=False)                              # Пока не сохраняем
            transaction.owner = request.user                                # Привязываем владельца
            transaction.save()                                           # Сохраняем
            return redirect('transaction_list')                            # Перенаправляем на список
    else:
        form = TransactionForm(user=request.user)

    return render(request, 'tracker/add_transaction.html', {'form': form})