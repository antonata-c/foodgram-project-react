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
    with open(file_path, encoding='utf-8') as file:
        data = json.load(file)
    model_data = []
    for obj_data in data:
        try:
            model_data.append(model(**obj_data))
        except ValueError as error:
            print(f'Ошибка: {error}\nЗапись не была загружена.')
            return
    model.objects.bulk_create(model_data)
    print(f'Все данные модели {model.__name__} были успешно загружены')


class Command(BaseCommand):
    """Класс команды для загрузки в базу данных."""

    def handle(self, *args, **kwargs):
        load_data('ingredients.json', Ingredient)
        load_data('tags.json', Tag)
