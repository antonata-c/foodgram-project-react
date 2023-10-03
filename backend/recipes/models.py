from django.core.validators import MinValueValidator
from django.db import models

from users.models import User


class Tag(models.Model):
    name = models.CharField(max_length=200, unique=True,
                            verbose_name='Название тега')
    color = models.CharField(max_length=7, verbose_name='Цвет тега')
    slug = models.SlugField(max_length=200, verbose_name='Слаг тега')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'



class Ingredient(models.Model):
    name = models.CharField(max_length=200, null=False)
    measurement_unit = models.CharField(max_length=200,
                                        null=False,
                                        blank=False)


class Recipe(models.Model):
    author = models.ForeignKey(User,
                               related_name='recipes',
                               on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=False)
    text = models.TextField(null=False)
    image = models.ImageField(upload_to='recipes/images/',
                              null=False,
                              blank=False)
    cooking_time = models.IntegerField(validators=(MinValueValidator(1),))
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient')
    tags = models.ManyToManyField(Tag)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='recipe_ingredient',
                               null=False, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient,
                                   null=False,
                                   related_name='recipe_ingredient',
                                   on_delete=models.CASCADE)
    amount = models.IntegerField()


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        related_name='favorite',
        on_delete=models.CASCADE
    )
    recipe = models.OneToOneField(
        Recipe,
        related_name='favorite',
        on_delete=models.CASCADE,
    )


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        related_name='shopping_cart',
        on_delete=models.CASCADE,
    )
    recipe = models.OneToOneField(
        Recipe,
        related_name='shopping_cart',
        on_delete=models.CASCADE,
    )

