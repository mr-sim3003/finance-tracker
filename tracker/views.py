from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Category, Transaction
from .serializers import CategorySerializer, TransactionSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated] # Только для авторизованных

    def get_queryset(self):
        #функции срабатывают когда обращаються к их функционалу
        # Показываем только категории текущего пользователя
        return Category.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        #функции срабатывают когда обращаються к их функционалу
        # При создании автоматически привязываем к текущему пользователю
        serializer.save(owner=self.request.user)


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated] # Только для авторизованных

    def get_queryset(self):
        #функции срабатывают когда обращаються к их функционалу
        # Показываем только транзакции текущего пользователя
        return Transaction.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        #функции срабатывают когда обращаються к их функционалу
        # При создании автоматически привязываем к текущему пользователю
        serializer.save(owner=self.request.user)
