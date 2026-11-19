"""
Сериализаторы DRF.

Преобразуют модели в JSON и валидируют входящие данные.
"""

from rest_framework import serializers

from tracker.models import Category, Transaction


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class TransactionSerializer(serializers.ModelSerializer):
    # Дополнительные поля только для чтения, чтобы фронтенду было удобнее.
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "type",
            "type_display",
            "amount",
            "category",
            "category_name",
            "date",
            "description",
            "owner",
            "created_at",
        ]
        read_only_fields = ["owner", "created_at"]

    def validate_amount(self, value):
        # Валидация на уровне API: сумма должна быть положительной.
        if value <= 0:
            raise serializers.ValidationError("Сумма должна быть больше нуля.")
        return value
