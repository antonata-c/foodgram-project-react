from rest_framework import viewsets

from api.serializers import RecipeSerializer
from recipes.models import Recipe


class RecipeViewSet(viewsets.ViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
