import csv
from datetime import datetime
from io import TextIOWrapper

from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.db import IntegrityError

from .models import Category, ImportJob, Transaction

User = get_user_model()

@shared_task(
    autoretry_for=(Exception,),           # retry при любой ошибке
    retry_backoff=True,                   # экспоненциальный backoff: 1, 2, 4, 8, ...
    retry_backoff_max=600,                # максимум 10 минут между попытками
    retry_jitter=True,                    # случайный разброс, чтобы не бить БД одновременно
    max_retries=3,                        # всего 3 попытки
)                                      #  @shared_task — декоратор, который говорит Celery, что это задача.
def import_csv_task(job_id):
    try:
        job = ImportJob.objects.get(id=job_id)
        job.status = 'processing'
        job.save(update_fields=['status', 'updated_at'])

        user = job.user
        file_name = job.file_name
        
        with default_storage.open(file_name, 'rb') as f:
            data_set = TextIOWrapper(f, encoding='utf-8')
            reader = csv.DictReader(data_set)
            created_count = 0
            skipped_count = 0

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
                    skipped_count += 1
                    continue

        # Обновляем успешный результат
        job.status = 'done'
        job.created_count = created_count
        job.skipped_count = skipped_count
        job.save(update_fields=['status', 'created_count', 'skipped_count', 'updated_at'])

        default_storage.delete(file_name)
        return f'Успешно загружено: {created_count}. Пропущено дублей: {skipped_count}.'

    except ImportJob.DoesNotExist:
        return f'Ошибка: ImportJob {job_id} не найден'
    except Exception as e:
        # Если задача упала фатально — обновляем статус и пробрасываем ошибку для retry
        try:
            job = ImportJob.objects.get(id=job_id)
            job.status = 'failed'
            job.error_message = str(e)
            job.save(update_fields=['status', 'error_message', 'updated_at'])
        except ImportJob.DoesNotExist:
            pass
        raise