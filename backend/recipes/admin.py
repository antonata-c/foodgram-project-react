from django.contrib import admin

from .models import (Favorite, Ingredient, RecipeIngredient,
                     Recipe, ShoppingCart, Tag, )


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'name',)
    list_filter = ('name', 'author', 'tags')


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag)
admin.site.register(RecipeIngredient)
admin.site.register(ShoppingCart)
admin.site.register(Favorite)
