from rest_framework.filters import SearchFilter
from django_filters import FilterSet, ModelMultipleChoiceFilter
from django_filters.rest_framework import BooleanFilter

from recipes.models import Recipe, Tag


class NameSearchFilter(SearchFilter):
    search_param = 'name'


class RecipeFilter(FilterSet):
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = BooleanFilter(field_name='is_favorited')
    is_in_shopping_cart = BooleanFilter(field_name='is_in_shopping_cart')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')
