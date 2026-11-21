"""
Модели приложения tracker.

Описывает основные бизнес-сущности: Категория, Транзакция и Задача импорта.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class Category(models.Model):
    """Категория транзакции (например, 'Еда' или 'Зарплата')."""

    name = models.CharField(max_length=100, verbose_name="Name")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
        verbose_name="Owner",
    )

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "name"], name="unique_category_per_user"
            )
        ]

    def __str__(self):
        return self.name


class Transaction(models.Model):
    """Финансовая операция (доход или расход).
    Django автоматически создаст метод get_type_display(), который мы используем в шаблонах.
    Константа TYPE_CHOICES — список кортежей. Она нужна для поля type, (значение_в_БД, человекочитаемое_имя)
    """

    TYPE_CHOICES = [
        ("income", "Income"),
        ("expense", "Expense"),
    ]
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Amount")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Type")
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="transactions",
        verbose_name="Category",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name="Owner",
    )
    date = models.DateField(default=timezone.now, verbose_name="Date", db_index=True)
    description = models.CharField(
        max_length=255, blank=True, verbose_name="Description"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-date", "-created_at"]
        indexes = [
            models.Index(fields=["owner", "date"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "date", "amount", "type", "description"],
                name="unique_transaction_per_user",
            )
        ]

    def __str__(self):
        return f"{self.get_type_display()} {self.amount} ({self.date})"  # type: ignore


# self.get_type_display() — Для поля с choices Django автоматически создаёт метод get_<field_name>_display(),
# который возвращает человеческое название выбранного варианта (например, Income вместо income).
# self.get_type_display() Метод возвращает строку вида: Income 100.00 (2026-11-05).


class ImportJob(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("done", "Done"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="import_jobs",
        verbose_name="User",
    )
    file_name = models.CharField(max_length=255, verbose_name="File name")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Status"
    )
    created_count = models.IntegerField(default=0, verbose_name="Created")
    skipped_count = models.IntegerField(default=0, verbose_name="Skipped")
    error_message = models.TextField(blank=True, verbose_name="Error message")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Import Job"
        verbose_name_plural = "Import Jobs"

    def __str__(self):
        return f"{self.file_name} ({self.status})"
