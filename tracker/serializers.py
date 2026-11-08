from rest_framework import serializers # предоставляет классы ModelSerializer, CharField, ValidationError.  # noqa: I001

from .models import Category, Transaction


class CategorySerializer(serializers.ModelSerializer):
    class Meta:                                            # внутренний класс с настройками. Сам по себе он не создает поля, 
        model = Category                                                    #а говорит ModelSerializer, как их генерировать.  
        fields = ['id', 'name', 'owner']                    # белый список. В JSON попадут только эти поля. Если бы я не указал fields, DRF включил бы все поля модели (включая те, что не нужно отдавать).
        read_only_fields = ['owner']                        # Владельца будем брать из запроса, а не из JSON
                                                            #«поле owner нельзя изменять через API». Клиент может его только читать. 
                                                            # Это шов безопасности: злоумышленник не сможет создать категорию от имени другого пользователя, даже если передаст owner в JSON. Владелец всё равно подставится из request.user (в perform_create).
class TransactionSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)     # Добавляем читаемое поле для типа (Income-Доходы / Expense-Расходы), чтобы фронтенду было удобнее
    category_name = serializers.CharField(source='category.name', read_only=True)       # source='get_type_display' — откуда брать значение. Не из атрибута type_display (его нет в модели), а из метода get_type_display() (который Django автоматически создаёт для поля с choices).
                                                                                        #  read_only=True «только для чтения». Это вычисляемое поле, клиент не может его записать.
                                                                                        # Добавляем имя категории для удобства (чтобы не делать второй запрос)
                                                                                        # source='category.name' — DRF «проваливается» внутрь связи. Он берёт self.category, затем category.name и кладёт в JSON.
                                                                                        # read_only=True — клиент не может записать это поле.
    class Meta:                                                                                         # внутренний класс с настройками. Сам по себе он не создает поля, 
        model = Transaction
        fields = [
            'id', 'type', 'type_display', 'amount', 'category', 'category_name', 
            'date', 'description', 'owner', 'created_at'
        ]
        read_only_fields = ['owner', 'created_at']                                              # а говорит ModelSerializer, как их генерировать.
                                                                                                # owner — нельзя записывать (владелец берётся из request.user).
                                                                                                # created_at — нельзя записывать (заполняется автоматически при создании через auto_now_add).
    def validate_amount(self, value):                                                                                              # validate_<field_name> — это соглашение DRF. 
        if value <= 0:                                                                           #Когда приходит POST с полем amount, DRF автоматически вызывает validate_amount и передаёт туда значение (value).
            raise serializers.ValidationError("Сумма должна быть больше нуля.")
        return value                                                                             # DRF перехватывает это исключение и возвращает клиенту 400 Bad Request с JSON: {"amount": ["Сумма должна быть больше нуля."]}.
        


    #Сериализатор — это граница безопасности и удобства:

    #Безопасность: read_only_fields не дают подделать владельца или дату.

    #Валидация: validate_amount не даёт записать мусор в базу.

    #Удобство: source='category.name' избавляет фронтенд от лишних запросов.

    #Когда ты смотришь на этот файл, ты видишь контракт API: какие поля клиент может читать, какие — писать,
    #  и какие правила валидации действуют. Это не просто «код», это документация твоего API.








