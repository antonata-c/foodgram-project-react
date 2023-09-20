from django.core.validators import MinValueValidator
from django.db import models


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
    name = models.CharField(max_length=200, null=False)
    text = models.TextField(null=False)
    image = models.ImageField(upload_to='recipes/images/',
                              null=False,
                              blank=False)
    cooking_time = models.IntegerField(validators=(MinValueValidator(1),))
    ingredients = models.ManyToManyField(Ingredient,
                                         through='RecipeIngredient',)
    tags = models.ManyToManyField(Tag)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, null=False, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, null=False,
                                   on_delete=models.CASCADE)
    amount = models.IntegerField(default=0, null=False)
