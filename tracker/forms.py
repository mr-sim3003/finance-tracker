"""
Формы приложения tracker.

Содержит форму для добавления транзакции (с логикой создания категории "на лету")
и форму для загрузки CSV.
"""

from django import forms

from .models import Category, Transaction


class TransactionForm(forms.ModelForm):
    """
    Форма транзакции.
    Позволяет либо выбрать существующую категорию, либо ввести новую.
    """

    # Это поле не привязано к модели, оно нужно только для UX.
    new_category = forms.CharField(
        required=False,
        label="Или создайте новую категорию",
        widget=forms.TextInput(attrs={"placeholder": "Например: Кафе"}),
    )

    class Meta:
        model = Transaction
        fields = ["type", "amount", "category", "date", "description"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.TextInput(attrs={"placeholder": "Необязательно"}),
        }

    def __init__(self, *args, **kwargs):
        # Мы передаем user в форму (из View), чтобы показать только его категории.
        # Иначе он увидел бы категории других пользователей.
        # Передаем user, чтобы отфильтровать категории только текущего пользователя.
        self.user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)
        # Забираем пользователя из аргументов
        # widgets — мы говорим Django, что date должно быть полем с календарем (type="date"),
        #  а description — текстовым полем с подсказкой.
        # Делаем поле category необязательным на уровне HTML валидации,
        # так как пользователь может выбрать "создать новую"
        self.fields["category"].required = False
        if self.user:
            # Показываем только категории текущего пользователя
            self.fields["category"].queryset = Category.objects.filter(owner=self.user)  # type: ignore

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount and amount <= 0:
            raise forms.ValidationError("Сумма должна быть больше нуля.")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get("category")
        new_category = cleaned_data.get("new_category")
        new_category = new_category.strip() if new_category else None
        # Валидация: пользователь должен либо выбрать категорию, либо ввести новую
        if not category and not new_category:
            raise forms.ValidationError(
                "Выберите категорию или введите название новой."
            )

        return cleaned_data

    def save(self, commit=True):
        # Если введена новая категория, создаем её перед сохранением транзакции.
        instance = super().save(commit=False)

        new_category_name = self.cleaned_data.get("new_category")
        # Очищаем от пробелов ДО проверки.
        # Если там были только пробелы, получится пустая строка, и мы не будем создавать категорию.
        if new_category_name:
            new_category_name = new_category_name.strip()

        if new_category_name:
            # get_or_create защищает от дублей, если пользователь введет название, которое уже есть
            category, _ = Category.objects.get_or_create(
                owner=self.user, name=new_category_name
            )
            instance.category = category

        if commit:
            instance.save()
        return instance


class CSVUploadForm(forms.Form):
    """Простая форма для загрузки CSV-файла."""

    file = forms.FileField(label="Выберите CSV-файл")
