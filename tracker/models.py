from django.conf import settings
from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Name") # verbose_name — это название для админки.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,                  # ссылка на кастомного пользователя
        on_delete=models.CASCADE,                  # если пользователя удалят, все его категории тоже удалятся.
        related_name='categories',                 # позволяет из пользователя достать его категории: user.categories.all().
        verbose_name="Owner"                       # verbose_name — это название для админки (человеческое).
    )                                              # Поле owner — связь «многие к одному» (FK). Один пользователь может иметь много категорий.

    class Meta:                                    # Названия таблицы, поля фильтрации, индексы. Hастройки модели, которые не создают колонок в БД.
        verbose_name = "Category"                  # как модель называется в админке (в единственном и множественном числе).
        verbose_name_plural = "Categories"         # как модель называется в админке (в единственном и множественном числе).
        constraints = [                                                                         # Это шов на уровне БД. UniqueConstraint запрещает дубликаты.  # noqa: RUF012
            models.UniqueConstraint(fields=['owner', 'name'], name='unique_category_per_user')  # Но не просто «уникальное имя», а уникальная пара (owner + name). 
        ]                                                                                       # То есть у одного пользователя не может быть двух категорий «Food», но у разных пользователей — может.

    def __str__(self):
        return self.name


class Transaction(models.Model):              
    TYPE_CHOICES = [                            # чтобы ограничить возможные значения (только income или expense).  # noqa: RUF012
        ('income', 'Income'),                   # Константа TYPE_CHOICES — список кортежей. Она нужна для поля type, 
        ('expense', 'Expense'),
    ]
    amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name="Amount"
    )                                                        # Шов 2: Decimal для денег (не float!)
    type = models.CharField(                                 # Поле type — строка. Но благодаря choices=TYPE_CHOICES, 
        max_length=10,                                       # Django будет проверять, что значение входит в список (income/expense). 
        choices=TYPE_CHOICES,                                # В БД хранится строка, а в админке отображается человеческое название.
        verbose_name="Type"
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.PROTECT,                          # Это защита. Если попытаться удалить категорию, в которой есть транзакции, база данных запретит это (выбросит ProtectedError). Мы не хотим терять финансовые данные.
        related_name='transactions',                       # из категории можно достать её транзакции: category.transactions.all().
        verbose_name="Category"
    )                                                      # Шов 3: Категория как FK, а не строка
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='transactions',
        verbose_name="Owner"
    )                                                                                      # Шов 4: owner через настройку, а не auth.User. Поле owner — FK на пользователя.
    date = models.DateField(default=timezone.now, verbose_name="Date")
    description = models.CharField(max_length=255, blank=True, verbose_name="Description") # description — описание. blank=True означает, что поле необязательное (может быть пустым).
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:                                                   #Названия таблицы, поля фильтрации, индексы.
        verbose_name = "Transaction"                              # Название таблицы
        verbose_name_plural = "Transactions"                      # Название таблицы
        ordering = ['-date', '-created_at']                       # По умолчанию: сначала новые  # noqa: RUF012
        constraints = [                                            #  Защита от дублей при импорте
            models.UniqueConstraint(
                fields=['owner', 'date', 'amount', 'type', 'description'],
                name='unique_transaction_per_user'
            )
        ]
    def __str__(self):
        return f"{self.get_type_display()} {self.amount} ({self.date})"



# self.get_type_display() — Для поля с choices Django автоматически создаёт метод get_<field_name>_display(), 
# который возвращает человеческое название выбранного варианта (например, Income вместо income).

# self.get_type_display() Метод возвращает строку вида: Income 100.00 (2026-11-05).