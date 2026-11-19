"""
Парсеры банковских выписок.

Каждый парсер — это класс с методом `parse(file)`, который возвращает
список словарей (транзакций в "сыром" виде). Celery-задача потом
сохраняет их в БД.
"""
import csv
from abc import ABC, abstractmethod

# класс для работы с датой и временем. 
#Нужен, чтобы преобразовать строку "2026-11-01" в объект date
from datetime import datetime

# обертка для бинарного файла, которая превращает его в текстовый. 
#Нужна, потому что default_storage.open(file_name, 'rb') открывает файл в бинарном режиме, 
# а csv.DictReader требует текстовый.
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
        """
        TextIOWrapper декодирует из битов в str.
        DictReader читает первую строку как заголовки (например, type,amount,category,date,description),
        а каждую следующую строку превращает в словарь, где ключи — это заголовки, а значения — данные.
        Парсинг строки даты в обьект, отбрасываем время оставляя дату.
        Если парсинг не сработал ставим сегодняшную дату чтобы сразу увидеть в каких данных ошибка.
        возможно лучше просто ValueError но если обьём даных небольшой можно потом отредактировать вручную.
        Создаём новый словарь используя словарь данный итератором.
        return transactions - этот список потом попадает в import_csv_task
        """
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