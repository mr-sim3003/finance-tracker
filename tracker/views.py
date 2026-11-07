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
            transaction = form.save(commit=False)                              # form.save(commit=False) — мы не сохраняем сразу, потому что нам нужно добавить owner (владельца). Без commit=False Django попытался бы сохранить транзакцию без владельца и выдал бы ошибку.
            transaction.owner = request.user                                # Привязываем владельца
            transaction.save()                                           # Сохраняем
            return redirect('transaction_list')                            # после успешного сохранения перенаправляем на список транзакций (чтобы не было повторной отправки формы при обновлении страницы).
    else:
        form = TransactionForm(user=request.user)

    return render(request, 'tracker/add_transaction.html', {'form': form})

import csv
from datetime import datetime
from io import TextIOWrapper

from django.contrib import messages

from .forms import CSVUploadForm


@login_required
def upload_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']  
            if not csv_file.name.endswith('.csv'):                                  # Проверка на расширение
                messages.error(request, 'Файл должен быть в формате CSV.')
                return redirect('upload_csv')                      
            try:                                                             # Читаем файл. TextIOWrapper нужен для правильной работы с кодировкой (UTF-8)
                data_set = TextIOWrapper(csv_file.file, encoding='utf-8')    # Django загружает файл как байты. Мы оборачиваем его в текстовый поток с кодировкой UTF-8, чтобы csv мог читать русские буквы.
                reader = csv.DictReader(data_set)                            # csv.DictReader: Это магия Python. Он берет первую строку (type,amount,category...) и делает её ключами словаря. Теперь к данным можно обращаться по имени (row['amount']), а не по индексу (row[1]).
                created_count = 0
                for row in reader:                                           # Пытаемся найти категорию по имени (только для текущего пользователя)                 
                    category_name = row.get('category', '').strip()                        # сли в CSV указана категория «Еда», а у тебя её нет, скрипт сам создаст её. Это удобно.
                    category = Category.objects.filter(owner=request.user, name=category_name).first()                  
                    if not category:                                                                       # Если категории нет, создаем её                       
                        category = Category.objects.create(owner=request.user, name=category_name)                   
                    try:                                                                                   # Парсим дату (ожидаем формат YYYY-MM-DD)
                        date_obj = datetime.strptime(row['date'], '%Y-%m-%d').date()
                    except (ValueError, KeyError):
                        date_obj = datetime.now().date()                   
                    Transaction.objects.create(                                  # Создаем транзакцию
                        owner=request.user,
                        type=row['type'],
                        amount=row['amount'],
                        category=category,
                        date=date_obj,
                        description=row.get('description', '')
                    )
                    created_count += 1               
                messages.success(request, f'Успешно загружено {created_count} транзакций.')
                return redirect('transaction_list')                
            except Exception as e:
                messages.error(request, f'Ошибка при чтении файла: {e}')
                return redirect('upload_csv')
    else:
        form = CSVUploadForm()

    return render(request, 'tracker/upload_csv.html', {'form': form})