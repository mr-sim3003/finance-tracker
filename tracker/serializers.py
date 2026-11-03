from rest_framework import serializers

from .models import Category, Transaction


class CategorySerializer(serializers.ModelSerializer):
    #Действует похоже как Form и ModelForm
    class Meta:
        #с какой моделью работать и какие поля показать
        model = Category
        fields = ['id', 'name', 'owner']
        read_only_fields = ['owner'] # Владельца будем брать из запроса, а не из JSON


class TransactionSerializer(serializers.ModelSerializer):
    #Действует похоже как Form и ModelForm
    # Добавляем читаемое поле для типа (Income/Expense), чтобы фронтенду было удобнее
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    # Добавляем имя категории для удобства (чтобы не делать второй запрос)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        #с какой моделью работать и какие поля показать
        model = Transaction
        fields = [
            'id', 'type', 'type_display', 'amount', 'category', 'category_name', 
            'date', 'description', 'owner', 'created_at'
        ]
        read_only_fields = ['owner', 'created_at']

    def validate_amount(self, value):
        #функции срабатывают когда обращаються к их функционалу
        if value <= 0:
            raise serializers.ValidationError("Сумма должна быть больше нуля.")
        return value