from .celery import app as celery_app

__all__ = ('celery_app',) # Когда Django запускается, он импортирует пакет config, и вместе с ним автоматически загружается Celery. Без этого celery_app не будет найден.