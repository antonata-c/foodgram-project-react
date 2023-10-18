from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.safestring import mark_safe

from .models import (Favorite, Ingredient, RecipeIngredient,
                     Recipe, ShoppingCart, Tag, )


class IngredientsInline(admin.TabularInline):
    model = RecipeIngredient
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'name',
                    'get_ingredients', 'get_favorited', 'get_image')
    list_filter = ('name', 'author', 'tags')
    filter_horizontal = ('ingredients',)
    list_display_links = ('id', 'name',)
    search_fields = ('author', 'name',)
    inlines = (IngredientsInline,)

    @admin.display(description='Избранное')
    def get_favorited(self, obj):
        return obj.favorite.all().count()

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, obj):
        return ', '.join([recipe_ingredients.ingredient.name
                          for recipe_ingredients
                          in obj.recipe_ingredient.all()])

    @admin.display(description='Картинка')
    def get_image(self, obj):
        return mark_safe(f'<img src={obj.image.url} width="80" height="60">')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    list_filter = ('name',)
    search_fields = ('name',)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount',)
    list_filter = ('ingredient',)
    list_display_links = ('recipe', 'ingredient')
    search_fields = ('recipe',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user',)
    list_display_links = ('recipe',)
    search_fields = ('recipe',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user',)
    list_display_links = ('recipe',)
    search_fields = ('recipe',)


admin.site.unregister(Group)
