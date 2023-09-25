from django.core.validators import MinValueValidator
from django.db import models

from users.models import User


class Tag(models.Model):
    name = models.CharField(max_length=200, null=False)
    color = models.CharField(max_length=7)
    slug = models.SlugField(max_length=200)

    class Meta:
        default_related_name = 'tags'


class Ingredient(models.Model):
    name = models.CharField(max_length=200, null=False)
    measurement_unit = models.CharField(max_length=200,
                                        null=False,
                                        blank=False)

    class Meta:
        default_related_name = 'ingredients'


class Recipe(models.Model):
    # author = models.ForeignKey(User,
    #                            related_name='recipes',
    #                            on_delete=models.CASCADE)
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
