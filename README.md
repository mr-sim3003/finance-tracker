# finance-tracker
Finance Tracker — это веб-приложение для учета личных доходов и расходов. Проект позволяет добавлять транзакции вручную, импортировать выписки из банка в формате CSV (с защитой от дубликатов) и просматривать историю операций.

🔗 Живая демонстрация: [http://194.113.35.11/](http://194.113.35.11/)

🚀 Стек технологий
1) Backend: Python 3.12, Django 5.2, Django REST Framework

2) База данных: PostgreSQL

2) Асинхронность: Celery, Redis (для фоновой обработки CSV)

4) Инфраструктура: Docker, Docker Compose, Nginx, Gunicorn

5) Тестирование: Pytest, Pytest-Django

6) CI/CD: GitHub Actions (линтер Ruff, тесты)

⚙️ Основные возможности

1) Аутентификация: Кастомная модель пользователя (CustomUser), доступ к данным только для авторизованных пользователей.

2) CRUD транзакций: Создание, просмотр, фильтрация доходов и расходов.

3) Импорт CSV: Загрузка файлов с транзакциями. Задача обрабатывается в фоне через Celery. Реализована идемпотентность (повторная загрузка того же файла не создает дубликатов).

4) Админ-панель: Управление категориями и транзакциями.
🛠 Запуск локально (через Docker)

Для запуска вам понадобятся Docker и Docker Compose.

Клонируйте репозиторий:
```bash

git clone https://github.com/mr-sim3003/finance-tracker.git
cd finance-tracker
```
Создайте файл `.env` в корне проекта на основе `.env.example`:
```bash
   cp .env.example .env
```
(Убедитесь, что в .env указаны корректные SECRET_KEY, DATABASE_URL и ALLOWED_HOSTS).

Запустите контейнеры:
```bash

docker compose up -d --build
```
Примените миграции:
```bash

docker compose exec web python manage.py migrate
```
Создайте суперпользователя (для доступа в админку):
```bash

docker compose exec web python manage.py createsuperuser
```
Приложение будет доступно по адресу: [http://localhost/](http://localhost/)

🧪 Тестирование

Проект покрыт тестами (API, валидация, идемпотентность импорта).

Запуск тестов внутри контейнера:
```bash

docker compose exec web pytest
```
без контенера
```bash
pytest
```
📁 Структура проекта
```text
.
├── accounts/         # Кастомная модель пользователя (CustomUser)
├── config/           # Настройки Django (base, local, prod, test)
├── tracker/          # Основное приложение (модели, API, задачи Celery)
├── nginx/            # Конфигурация Nginx
├── templates/        # HTML-шаблоны
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

📝 Лицензия
Проект создан в учебных целях.
