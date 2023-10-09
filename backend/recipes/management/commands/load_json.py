import json
import os

from django.conf import settings
from django.core.management import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Класс команды для загрузки в базу данных."""

    def handle(self, *args, **kwargs):
        file_path = os.path.join(settings.DATA_DIR_PATH, 'ingredients.json')
        if not os.path.exists(file_path):
            print(f'Файл по пути {file_path} не найден')
            return
        with open(file_path) as file:
            data = json.load(file)
        for ingredient_data in data:
            try:
                Ingredient(**ingredient_data).save()
            except ValueError as error:
                print(f'Ошибка: {error}\nЗапись не была загружена.')
                return
        print('Все данные были успешно загружены')

