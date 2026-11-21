"""
View-слой импорта CSV.

Вынесен из views.py, потому что импорт — отдельный сценарий:
загрузка файла → создание ImportJob → фоновая задача Celery → история.
Он не пересекается с ручным CRUD транзакций, хотя и работает
с той же моделью Transaction. Имя файла = контекст: открыл imports.py —
сразу видишь всё про импорт.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.storage import default_storage
from django.shortcuts import redirect, render
from django.utils.text import get_valid_filename
from django.views.generic import ListView

from .forms import CSVUploadForm
from .models import ImportJob
from .tasks import import_csv_task


@login_required
def upload_csv(request):
    """
    Приём CSV-файла и постановка задачи в Celery.

    Функция, а не CBV: логика линейная (проверить → сохранить → создать job
    → запустить задачу → редирект), без переиспользуемых частей. CBV
    (FormView) добавил бы класс и методы без выгоды — здесь один сценарий.
    """
    if request.method == "POST":
        form = CSVUploadForm(request.POST, request.FILES)

        if form.is_valid():
            csv_file = request.FILES["file"]

            # Проверка расширения — на уровне view, а не формы:
            # CSVUploadForm — простая форма без валидации расширения,
            # потому что она же может использоваться для других типов файлов
            # в будущем. Валидация расширения — ответственность конкретного view.
            if not csv_file.name.endswith(".csv"):
                messages.error(request, "Файл должен быть в формате CSV.")
                return redirect("tracker:upload_csv")

            # default_storage, а не MEDIA_ROOT напрямую: работает и локально
            # (FileSystemStorage), и в облаке (S3Storage) без правок кода —
            # достаточно поменять DEFAULT_FILE_STORAGE в settings.
            safe_name = get_valid_filename(csv_file.name)
            file_name = default_storage.save(safe_name, csv_file)

            # ImportJob создаём ДО запуска задачи: если Celery недоступен,
            # у нас останется запись со статусом 'pending' — пользователь
            # увидит её в истории и поймёт, что импорт не начался.
            # Альтернатива (создавать job внутри задачи) хуже: при падении
            # Celery пользователь не увидит вообще ничего.
            job = ImportJob.objects.create(
                user=request.user,
                file_name=file_name,
                status="pending",
            )

            # .delay() — асинхронный вызов. Передаём только job.id, а не
            # весь объект: Celery сериализует аргументы в JSON, а модель
            # Django не сериализуется. Задача сама достанет job из БД.
            import_csv_task.delay(job.id)  # type: ignore

            # Сообщение «принят в обработку», а не «импортирован»:
            # задача ещё не выполнена, результат появится в истории импортов.
            messages.success(
                request, "Файл принят в обработку. Результат появится чуть позже."
            )
            return redirect("tracker:transaction_list")

    else:
        form = CSVUploadForm()

    return render(request, "tracker/upload_csv.html", {"form": form})


class ImportJobListView(LoginRequiredMixin, ListView):
    """
    История импортов пользователя.

    ListView, а не View: нужна пагинация + стандартный рендеринг списка.
    View потребовал бы ручной paginate_by + context + render — то же самое,
    но больше кода.
    """

    model = ImportJob
    template_name = "tracker/import_job_list.html"
    context_object_name = "jobs"
    paginate_by = 10

    def get_queryset(self):
        # Фильтр по user — защита от IDOR: пользователь видит только
        # свои импорты, даже если угадает чужой ID. Тот же паттерн,
        # что в TransactionListView и DRF-ViewSet'ах.
        return ImportJob.objects.filter(user=self.request.user)
