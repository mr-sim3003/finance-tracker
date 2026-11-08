from celery import shared_task
from django.contrib.auth import get_user_model
from .models import Transaction, Category
import csv
from io import TextIOWrapper
from datetime import datetime
from django.core.files.storage import default_storage
from django.db import IntegrityError

User = get_user_model()

@shared_task                                        #  @shared_task — декоратор, который говорит Celery, что это задача.
def import_csv_task(user_id, file_path):
    try:
        user = User.objects.get(id=user_id)                  # default_storage.open() — открывает файл, который Django сохранил на диск (в папку MEDIA_ROOT). Это работает, если ты настроил MEDIA_ROOT в settings.py.
        with default_storage.open(file_path, 'rb') as f:     # Открываем файл из хранилища (Django сохранил его на диск)
            data_set = TextIOWrapper(f, encoding='utf-8')
            reader = csv.DictReader(data_set)            
            created_count = 0
            skipped_count = 0                               # <--- Считаем пропущенные

            for row in reader:
                category_name = row.get('category', '').strip()
                category, _ = Category.objects.get_or_create(owner=user, name=category_name)
                
                try:
                    date_obj = datetime.strptime(row['date'], '%Y-%m-%d').date()
                except (ValueError, KeyError):
                    date_obj = datetime.now().date()

                try:
                    Transaction.objects.create(
                    owner=user,
                    type=row['type'],
                    amount=row['amount'],
                    category=category,
                    date=date_obj,
                    description=row.get('description', '')
                )
                    created_count += 1
                except IntegrityError:                   
                    skipped_count += 1        # Если сработал UniqueConstraint, значит, транзакция уже есть
                    continue # <--- Переходим к следующей строке
                        
            default_storage.delete(file_path) # # Удаляем файл после обработки, чтобы не засорять диск
            return f'Успешно загружено: {created_count}. Пропущено дублей: {skipped_count}.'
            
    except Exception as e:
        return f'Ошибка: {e}'