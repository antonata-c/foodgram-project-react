from collections import defaultdict

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import (HTTP_201_CREATED,
                                   HTTP_204_NO_CONTENT)

from .serializers import (RecipeCreateSerializer, IngredientSerializer,
                          RecipeGetSerializer, TagSerializer,
                          FavoriteSerializer, ShoppingCartSerializer)
from recipes.models import (Recipe, Ingredient, Tag,
                            Favorite, ShoppingCart, RecipeIngredient)


def post_delete(**kwargs):
    recipe = get_object_or_404(Recipe, id=kwargs.get('pk'))
    request = kwargs.get('request')
    if request.method == 'POST':
        serializer = kwargs.get('serializer')(
            data=kwargs.get('data'),
            context={'recipe': recipe, 'user': request.user}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, recipe=recipe)
        return Response(serializer.data,
                        status=HTTP_201_CREATED)
    get_object_or_404(kwargs.get('model'), recipe=recipe).delete()
    return Response('Рецепт успешно удален из избранного',
                    status=HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH'):
            return RecipeCreateSerializer
        return RecipeGetSerializer

    @action(detail=True,
            methods=('post', 'delete'))
    def favorite(self, request, pk):
        return post_delete(
            pk=pk,
            data=request.data,
            request=self.request,
            model=Favorite,
            serializer=FavoriteSerializer
        )

    @action(detail=True,
            methods=('post', 'delete'))
    def shopping_cart(self, request, pk):
        return post_delete(
            pk=pk,
            data=request.data,
            request=self.request,
            model=ShoppingCart,
            serializer=ShoppingCartSerializer
        )

    # TODO: Дописать метод, пагинация, пермишены, вербосы, фильтры, поиск
    @action(detail=False,
            methods=('get',))
    def download_shopping_cart(self, request):
        shopping_cart_txt = f'Список покупок пользователя {self.request.user}:'
        recipes_ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=self.request.user
        ).values('ingredient__name', 'ingredient__measurement_unit', 'amount')
        fixed_ingredients = defaultdict()
        for ingredient in recipes_ingredients:
            if fixed_ingredients.get(ingredient['ingredient__name']) is None:
                fixed_ingredients[ingredient['ingredient__name']] = 0
                fixed_ingredients[
                    ingredient['ingredient__name']
                ] = ingredient['ingredient__measurement_unit']
            fixed_ingredients[
                ingredient['ingredient__name']
            ] += ingredient['amount']
        print(fixed_ingredients)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
