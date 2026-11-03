from django.db import models
from django.conf import settings
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Name")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='categories',
        verbose_name="Owner"
    )

    class Meta:
        #Названия таблицы, поля фильтрации, индексы.
        verbose_name = "Category" #Название таблицы
        verbose_name_plural = "Categories" #Название таблицы
        # Шов: уникальность категории для конкретного пользователя
        constraints = [
            models.UniqueConstraint(fields=['owner', 'name'], name='unique_category_per_user')
        ]

    def __str__(self):
        return self.name


class Transaction(models.Model):
    # Шов 1: Одна таблица, тип определяет доход или расход
    TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    
    # Шов 2: Decimal для денег (не float!)
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name="Amount"
    )
    type = models.CharField(
        max_length=10, 
        choices=TYPE_CHOICES, 
        verbose_name="Type"
    )
    
    # Шов 3: Категория как FK, а не строка
    category = models.ForeignKey(
        Category, 
        on_delete=models.PROTECT, # Защита: не удалять категорию, если в ней есть транзакции
        related_name='transactions',
        verbose_name="Category"
    )
    
    # Шов 4: owner через настройку, а не auth.User
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='transactions',
        verbose_name="Owner"
    )
    
    date = models.DateField(default=timezone.now, verbose_name="Date")
    description = models.CharField(max_length=255, blank=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        #Названия таблицы, поля фильтрации, индексы.
        verbose_name = "Transaction"  # Название таблицы
        verbose_name_plural = "Transactions" # Название таблицы
        ordering = ['-date', '-created_at'] # По умолчанию: сначала новые

    def __str__(self):
        return f"{self.get_type_display()} {self.amount} ({self.date})"
