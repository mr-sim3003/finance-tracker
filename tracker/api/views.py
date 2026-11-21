"""
DRF ViewSets для REST API.

Обеспечивают CRUD для транзакций и категорий.
Изолируют данные пользователя (защита от IDOR).
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from tracker.models import Category, Transaction

from .serializers import CategorySerializer, TransactionSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    """API для категорий (CRUD)."""

    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Пользователь видит только свои категории.
        return Category.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        # Владелец берется из запроса, его нельзя подделать из JSON.
        serializer.save(owner=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    """API для транзакций (CRUD)."""

    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Защита от IDOR + select_related для оптимизации запросов.
        return Transaction.objects.filter(owner=self.request.user).select_related(
            "category"
        )

    def perform_create(self, serializer):
        # Владелец всегда берется из запроса.
        serializer.save(owner=self.request.user)
