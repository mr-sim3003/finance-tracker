"""
Фоновые задачи Celery.

Здесь описана логика импорта CSV: чтение файла, парсинг и сохранение
с защитой от дубликатов (идемпотентность).
"""
from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.db import IntegrityError

from .models import Category, ImportJob, Transaction
from .parsers import GenericCSVParser

User = get_user_model()

# Декоратор @shared_task с настройками ретраев:
# если БД упадет или файл временно недоступен — Celery попробует снова.
@shared_task(                  #  @shared_task — декоратор, который говорит Celery, что это задача.
    autoretry_for=(Exception,),
    retry_backoff=True,        # Экспоненциальная задержка между попытками
    retry_backoff_max=600,     # Максимум 10 минут
    retry_jitter=True,         # Случайный разброс, чтобы не бить БД одновременно
    max_retries=3,             # Всего 3 попытки
)
def import_csv_task(job_id):
    try:
        job = ImportJob.objects.get(id=job_id)
        job.status = 'processing'
        job.save(update_fields=['status', 'updated_at'])

        user = job.user
        file_name = job.file_name
        
        with default_storage.open(file_name, 'rb') as f:
            parser = GenericCSVParser()           # <--- создаём парсер
            rows = parser.parse(f)                # <--- парсим в список словарей
            created_count = 0
            skipped_count = 0

            for row in rows:
                category_name = row['category']
                category, _ = Category.objects.get_or_create(owner=user, name=category_name)
                try:
                    Transaction.objects.create(
                       owner=user,
                       type=row['type'],
                       amount=row['amount'],
                       category=category,
                       date=row['date'],
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