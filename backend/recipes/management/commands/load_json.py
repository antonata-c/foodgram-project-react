import json
import os

from django.conf import settings
from django.core.management import BaseCommand

from recipes.models import Ingredient, Tag


def load_data(filename, model):
    file_path = os.path.join(settings.DATA_DIR_PATH, filename)
    if not os.path.exists(file_path):
        print(f'Файл по пути {file_path} не найден')
        return
    try:
        with open(file_path, encoding='utf-8') as file:
            data = json.load(file)
    except IOError:
        print("Что-то пошло не так. Файл уже открыт.")
        return
    if not file.closed:
        file.close()
    model_data = []
    for obj_data in data:
        model_data.append(model(**obj_data))
    model.objects.bulk_create(model_data)
    print(f'Все данные модели {model.__name__} были успешно загружены')



class Command(BaseCommand):
    """Класс команды для загрузки в базу данных."""

    def handle(self, *args, **kwargs):
        load_data('ingredients.json', Ingredient)
        load_data('tags.json', Tag)
