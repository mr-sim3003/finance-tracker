# Берем официальный образ Python (версия 3.12, как у тебя)
FROM python:3.12-slim

# Устанавливаем переменные окружения, чтобы Python не писал логи в буфер и не создавал .pyc файлы
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Устанавливаем системные зависимости (например, для PostgreSQL)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код проекта
COPY . /app/

# Открываем порт (пока просто для информации, проброс сделаем в compose)
EXPOSE 8000