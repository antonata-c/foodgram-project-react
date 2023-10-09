from django.contrib import admin

from .models import Ingredient, Recipe, Tag

admin.site.register(Recipe)
admin.site.register(Ingredient)
admin.site.register(Tag)
