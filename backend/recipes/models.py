from django.conf import settings
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from users.models import User


class Tag(models.Model):
    name = models.CharField(max_length=settings.RECIPES_NAME_SIZE, unique=True,
                            verbose_name='Название тега')
    color = models.CharField(max_length=settings.COLOR_SIZE,
                             validators=(RegexValidator(
                                 r'^#[A-F0-9]{6}$'
                             ),),
                             verbose_name='Цвет тега')
    slug = models.SlugField(max_length=settings.RECIPES_NAME_SIZE,
                            verbose_name='Слаг тега')

    def __str__(self):
        return self.name[:settings.REPR_SIZE]

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'


class Ingredient(models.Model):
    name = models.CharField(max_length=settings.RECIPES_NAME_SIZE,
                            null=False,
                            verbose_name='Название ингредиента')
    measurement_unit = models.CharField(max_length=settings.RECIPES_NAME_SIZE,
                                        null=False,
                                        blank=False,
                                        verbose_name='Единица измерения')

    def __str__(self):
        return self.name[:settings.REPR_SIZE]

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'


class Recipe(models.Model):
    author = models.ForeignKey(User,
                               related_name='recipes',
                               on_delete=models.CASCADE,
                               verbose_name='Автор рецепта')
    name = models.CharField(max_length=settings.RECIPES_NAME_SIZE,
                            null=False,
                            verbose_name='Название рецепта')
    text = models.TextField(null=False, verbose_name='Текст рецепта')
    image = models.ImageField(upload_to='recipes/images/',
                              null=False,
                              blank=False,
                              verbose_name='Картинка рецепта')
    cooking_time = models.IntegerField(validators=(
        MinValueValidator(settings.MIN_VALUE),
    ),
        verbose_name='Время приготовления')
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient',
                                         blank=False,
                                         verbose_name='Ингредиенты рецепта')
    tags = models.ManyToManyField(Tag,
                                  blank=False,
                                  verbose_name='Теги рецепта')

    def __str__(self):
        return self.name[:settings.RECIPES_NAME_SIZE]

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('id',)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='recipe_ingredient',
                               null=False, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient,
                                   null=False,
                                   related_name='recipe_ingredient',
                                   on_delete=models.CASCADE)
    amount = models.SmallIntegerField(validators=(
        MinValueValidator(settings.MIN_VALUE),
    ))


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        related_name='favorite',
        on_delete=models.CASCADE,
        verbose_name='Владелец избранного'
    )
    recipe = models.OneToOneField(
        Recipe,
        related_name='favorite',
        on_delete=models.CASCADE,
        verbose_name='Рецепт в избранном'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        related_name='shopping_cart',
        on_delete=models.CASCADE,
        verbose_name='Владелец списка покупок'
    )
    recipe = models.OneToOneField(
        Recipe,
        related_name='shopping_cart',
        on_delete=models.CASCADE,
        verbose_name='Рецепт в списке покупок'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
