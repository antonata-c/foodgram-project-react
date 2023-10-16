from django.db.models import Sum, OuterRef, Exists
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (HTTP_201_CREATED, HTTP_204_NO_CONTENT,
                                   HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND)

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow, User
from .filters import NameSearchFilter, recipe_filter
from .pagination import CustomPageNumberPagination
from .permissions import AdminOrAuthorOrReadOnly, \
    IsAuthenticatedOrReadOnlyObject
from .serializers import (FavoriteSerializer, FollowGetSerializer,
                          FollowPostSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeGetSerializer,
                          ShoppingCartSerializer, TagSerializer,
                          UserSerializer)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = (Recipe.objects
                .select_related('author')
                .prefetch_related('tags', 'ingredients')
                # .annotate(
                #     is_favorited=Exists(Favorite.objects.filter(
                #         user=OuterRef('author'),
                #         recipe=OuterRef('pk')
                #     )),
                #     is_in_shopping_cart=Exists(ShoppingCart.objects.filter(
                #         user=OuterRef('author'),
                #         recipe=OuterRef('pk')
                #     )))
                )
    # По какой-то причине не получается это все подружить, пробовал
    # через ReadOnly, SerializerMethod, ничего так и не вышло,
    # хотя аннотируются они корректно, может быть можете дать подсказку?
    permission_classes = (AdminOrAuthorOrReadOnly,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        return recipe_filter(self.queryset, self.request)

    def favorite_shopping_post(self, request, pk, serializer):
        if not Recipe.objects.filter(id=pk).exists():
            return Response('Выбранного рецепта не существует!',
                            status=HTTP_400_BAD_REQUEST)
        user_recipe_data = {'recipe': pk, 'user': request.user.pk}
        serializer_to_save = serializer(
            data=user_recipe_data
        )
        serializer_to_save.is_valid(raise_exception=True)
        serializer_to_save.save()
        return Response(serializer_to_save.data,
                        status=HTTP_201_CREATED)

    def favorite_shopping_delete(self, request, pk, model):
        get_object_or_404(Recipe, pk=pk)
        if model.objects.filter(user=request.user,
                                recipe=pk).exists():
            model.objects.get(user=request.user,
                              recipe=pk).delete()
            return Response('Рецепт успешно удален',
                            status=HTTP_204_NO_CONTENT)
        return Response('Рецепта нет в списке',
                        status=HTTP_400_BAD_REQUEST)

    def form_shopping_cart(self, recipes_ingredients):
        shopping_cart = [f'Здравствуйте, {self.request.user}, это foodgram'
                         ', ваш список покупок:\n']
        shopping_cart += [
            (f'{ingredient["ingredient__name"]} '
             f'({ingredient["ingredient__measurement_unit"]})'
             f' - {ingredient["amount"]}')
            for ingredient in recipes_ingredients
        ]
        response = HttpResponse('\n'.join(shopping_cart),
                                content_type="text/plain")
        response['Content-Disposition'] = ('attachment; '
                                           'filename=shopping_cart_'
                                           f'{self.request.user}')
        return response

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH'):
            return RecipeCreateSerializer
        return RecipeGetSerializer

    @action(detail=True,
            methods=('post',),
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk):
        return self.favorite_shopping_post(
            request=self.request,
            pk=pk,
            serializer=FavoriteSerializer
        )

    @favorite.mapping.delete
    def favorite_delete(self, request, pk):
        return self.favorite_shopping_delete(
            request=self.request,
            pk=pk,
            model=Favorite
        )

    @action(detail=True,
            methods=('post',),
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        return self.favorite_shopping_post(
            request=self.request,
            pk=pk,
            serializer=ShoppingCartSerializer
        )

    @shopping_cart.mapping.delete
    def shopping_cart_delete(self, request, pk):
        return self.favorite_shopping_delete(
            request=self.request,
            pk=pk,
            model=ShoppingCart
        )

    @action(detail=False,
            methods=('get',),
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        if not self.request.user.shopping_cart.exists():
            return Response('Список покупок пуст',
                            status=HTTP_204_NO_CONTENT)
        recipes_ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=self.request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            amount=Sum('amount')
        ).order_by('id')
        return self.form_shopping_cart(recipes_ingredients)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (NameSearchFilter,)
    search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPageNumberPagination

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = IsAuthenticated,
        return super().get_permissions()

    @action(detail=True,
            methods=('post',),
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, **kwargs):
        try:
            author_id = int(kwargs.get('id'))
        except ValueError as exception:
            return Response({"pk": "Id пользователя должен быть числом!"},
                            status=HTTP_400_BAD_REQUEST)
        get_object_or_404(User, pk=author_id)
        serializer = FollowPostSerializer(
            data={
                'user': self.request.user.pk,
                'author': author_id
            },
            context={
                'request': request,
                'author': author_id
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,
                        status=HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, **kwargs):
        try:
            author = int(kwargs.get('id'))
        except ValueError as exception:
            return Response({"pk": "Id пользователя должен быть числом!"},
                            status=HTTP_400_BAD_REQUEST)
        author = get_object_or_404(User, pk=author)
        if Follow.objects.filter(user=self.request.user,
                                 author=author).exists():
            Follow.objects.get(user=self.request.user,
                               author=author).delete()
            return Response('Успешная отписка',
                            status=HTTP_204_NO_CONTENT)
        return Response('Подписки не существует!',
                        status=HTTP_400_BAD_REQUEST)

    @action(detail=False,
            methods=('get',),
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        serializer = FollowPostSerializer(
            self.paginate_queryset(
                Follow.objects.filter(user=self.request.user).order_by('id'),
            ),
            context={'request': request, 'author': self.request.user.pk},
            many=True)
        return self.get_paginated_response(serializer.data)
