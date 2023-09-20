from django.urls import path, include
from rest_framework import routers

from .views import RecipeViewSet, IngredientViewSet, TagViewSet

router = routers.DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'ingredients',
                IngredientViewSet,
                basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')

urlpatterns = [
    path('', include(router.urls)),
]
