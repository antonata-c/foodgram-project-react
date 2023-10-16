from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from colorfield.fields import ColorField

from backend.constants import (RECIPES_NAME_SIZE, REPR_SIZE,
                               MIN_VALUE, MAX_P_INT_VALUE)
from users.models import User


class Tag(models.Model):
    name = models.CharField(max_length=RECIPES_NAME_SIZE, unique=True,
                            verbose_name='Название тега')
    color = ColorField(verbose_name='Цвет тега')
    slug = models.SlugField(max_length=RECIPES_NAME_SIZE,
                            verbose_name='Слаг тега')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name[:REPR_SIZE]


class Ingredient(models.Model):
    name = models.CharField(max_length=RECIPES_NAME_SIZE,
                            verbose_name='Название ингредиента')
    measurement_unit = models.CharField(max_length=RECIPES_NAME_SIZE,
                                        verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = (
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'),
        )

    def __str__(self):
        return self.name[:REPR_SIZE]


class Recipe(models.Model):
    author = models.ForeignKey(User,
                               related_name='recipes',
                               on_delete=models.CASCADE,
                               verbose_name='Автор рецепта')
    name = models.CharField(max_length=RECIPES_NAME_SIZE,
                            verbose_name='Название рецепта')
    text = models.TextField(verbose_name='Текст рецепта')
    image = models.ImageField(upload_to='recipes/images/',
                              verbose_name='Картинка рецепта')
    cooking_time = models.PositiveSmallIntegerField(
        validators=(
            MinValueValidator(MIN_VALUE,
                              message='Значение должно быть больше 0!'),
            MaxValueValidator(MAX_P_INT_VALUE,
                              message='Значение должно быть меньше 32767!')
        ),
        verbose_name='Время приготовления')
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient',
                                         verbose_name='Ингредиенты рецепта')
    tags = models.ManyToManyField(Tag,
                                  verbose_name='Теги рецепта')

    pub_date = models.DateTimeField(
        verbose_name='Дата публикации рецепта',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name[:RECIPES_NAME_SIZE]


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='recipe_ingredient',
                               null=False, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient,
                                   null=False,
                                   related_name='recipe_ingredient',
                                   on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(validators=(
        MinValueValidator(MIN_VALUE,
                          message='Значение должно быть больше 0!'),
        MaxValueValidator(MAX_P_INT_VALUE,
                          message='Значение должно быть меньше 32767!')
    ))

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'


class FavoriteShoppingAbstractModel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Владелец избранного'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт в избранном'
    )

    class Meta:
        abstract = True
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_user_recipe'),
        )

    def __str__(self):
        return f"У {self.user} в списке находится {self.recipe}"


class Favorite(FavoriteShoppingAbstractModel):
    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'favorite'


class ShoppingCart(FavoriteShoppingAbstractModel):
    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'shopping_cart'
