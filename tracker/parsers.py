"""
Парсеры банковских выписок.

Каждый парсер — это класс с методом `parse(file)`, который возвращает
список словарей (транзакций в "сыром" виде). Celery-задача потом
сохраняет их в БД.
"""
import csv
from abc import ABC, abstractmethod
from datetime import datetime
from io import TextIOWrapper


class BaseStatementParser(ABC):
    """
    Абстрактный базовый парсер. Все банки наследуются от него.
    """

    @abstractmethod
    def parse(self, file) -> list[dict]:
        """
        Принимает открытый файл (binary mode), возвращает список словарей:
        [
            {
                'type': 'income' | 'expense',
                'amount': Decimal,
                'category': str,
                'date': date,
                'description': str,
            },
            ...
        ]
        """
        raise NotImplementedError


class GenericCSVParser(BaseStatementParser):
    """
    Текущий формат: type,amount,category,date,description.
    """

    def parse(self, file) -> list[dict]:
        data_set = TextIOWrapper(file, encoding='utf-8')
        reader = csv.DictReader(data_set)
        transactions = []

        for row in reader:
            try:
                date_obj = datetime.strptime(row['date'], '%Y-%m-%d').date()
            except (ValueError, KeyError):
                date_obj = datetime.now().date()

            transactions.append({
                'type': row.get('type', 'expense'),
                'amount': row.get('amount', '0'),
                'category': row.get('category', '').strip(),
                'date': date_obj,
                'description': row.get('description', ''),
            })

        return transactions