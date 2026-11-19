"""
Фоновые задачи Celery.

Здесь описана логика импорта CSV: чтение файла, парсинг и сохранение
с защитой от дубликатов (идемпотентность).
"""

from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction

from .models import Category, ImportJob, Transaction
from .parsers import GenericCSVParser

User = get_user_model()


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def import_csv_task(job_id):
    try:
        job = ImportJob.objects.get(id=job_id)

        # Идемпотентность: если задача уже выполнена — не запускаем повторно.
        # Это защита от ретрая Celery после успешного завершения
        # (например, воркер упал между save() и return).
        if job.status == "done":
            return (
                f"Уже выполнено ранее. Загружено: {job.created_count}. "
                f"Пропущено: {job.skipped_count}."
            )

        job.status = "processing"
        job.save(update_fields=["status", "updated_at"])
        user = job.user
        file_name = job.file_name

        if not default_storage.exists(file_name):
            job.status = "failed"
            job.error_message = "Файл не найден (возможно, уже обработан)."
            job.save(update_fields=["status", "error_message", "updated_at"])
            return f"Ошибка: файл {file_name} не найден."

        with default_storage.open(file_name, "rb") as f:
            parser = GenericCSVParser()
            rows = parser.parse(f)
            created_count = 0
            skipped_count = 0

            for row in rows:
                category_name = row["category"]

                # 1. Проверка на битую дату
                if row.get("date_error"):
                    skipped_count += 1
                    # Можно добавить в лог для отладки (опционально)
                    continue
                # Пропускаем строки с пустой категорией
                if not category_name:
                    skipped_count += 1
                    continue

                category, _ = Category.objects.get_or_create(
                    owner=user, name=category_name
                )
                try:
                    # Оборачиваем в atomic(), чтобы при IntegrityError
                    # транзакция откатилась и следующая строка обработалась нормально
                    with transaction.atomic():
                        Transaction.objects.create(
                            owner=user,
                            type=row["type"],
                            amount=row["amount"],
                            category=category,
                            date=row["date"],
                            description=row.get("description", ""),
                        )
                    created_count += 1
                except IntegrityError:
                    skipped_count += 1
                    continue

        job.status = "done"
        job.created_count = created_count
        job.skipped_count = skipped_count
        job.save(
            update_fields=["status", "created_count", "skipped_count", "updated_at"]
        )

        # Удаляем файл только после успешного завершения.
        # exists() — защита от гонки, если файл уже удалён.
        if default_storage.exists(file_name):
            default_storage.delete(file_name)

        return f"Успешно загружено: {created_count}. Пропущено дублей: {skipped_count}."

    except ImportJob.DoesNotExist:
        return f"Ошибка: ImportJob {job_id} не найден"
    except Exception as e:
        try:
            job = ImportJob.objects.get(id=job_id)
            job.status = "failed"
            job.error_message = str(e)
            job.save(update_fields=["status", "error_message", "updated_at"])
        except ImportJob.DoesNotExist:
            pass
        raise
