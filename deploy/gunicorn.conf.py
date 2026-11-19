# deploy/gunicorn.conf.py
import multiprocessing

# Слушаем все интерфейсы внутри контейнера
bind = "0.0.0.0:8000"

# Количество воркеров: (2 * ядра) + 1.
workers = min(multiprocessing.cpu_count() * 2 + 1, 4)

# Таймаут: если воркер не ответил за 30 секунд, Gunicorn его убьет.
timeout = 30

# Перезапускать воркер после 1000 запросов (защита от утечек памяти)
max_requests = 1000
max_requests_jitter = 100

# Логирование (чтобы видеть, что происходит внутри контейнера)
accesslog = "-"
errorlog = "-"
loglevel = "info"
