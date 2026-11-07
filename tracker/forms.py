from django import forms

from .models import Category, Transaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['type', 'amount', 'category', 'date', 'description']                   # noqa: RUF012
        widgets = {                                                                      # noqa: RUF012
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.TextInput(attrs={'placeholder': 'Необязательно'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)                                                # <--- Забираем пользователя из аргументов
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['category'].queryset = Category.objects.filter(owner=self.user)    # Показываем только категории текущего пользователя

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Сумма должна быть больше нуля.")
        return amount