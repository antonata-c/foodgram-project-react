from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (HTTP_201_CREATED, HTTP_204_NO_CONTENT,
                                   HTTP_400_BAD_REQUEST)

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow, User

from .filters import CustomSearchFilter
from .mixins import CreateRetrieveListMixin
from .pagination import CustomPageNumberPagination
from .permissions import AdminOrAuthorOrReadOnly
from .serializers import (FavoriteSerializer, FollowSerializer,
                          IngredientSerializer, RecipeCreateSerializer,
                          RecipeGetSerializer, SetPasswordSerializer,
                          ShoppingCartSerializer, TagSerializer,
                          UserSerializer)


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
    if not kwargs.get('model').objects.filter(recipe=recipe).exists():
        return Response('Рецепта нет в списке',
                        status=HTTP_400_BAD_REQUEST)
    kwargs.get('model').objects.get(recipe=recipe).delete()
    return Response('Рецепт успешно удален',
                    status=HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (AdminOrAuthorOrReadOnly,)
    http_method_names = ['get', 'post', 'patch', 'delete']
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        author = self.request.query_params.get('author')
        if author:
            self.queryset = self.queryset.filter(author=author)
        tags = self.request.query_params.getlist('tags')
        if tags:
            self.queryset = self.queryset.filter(
                tags__slug__in=tags
            ).order_by('id').distinct()
        if self.request.user.is_anonymous:
            return self.queryset

        is_favorited = self.request.query_params.get('is_favorited')
        if is_favorited == '1':
            self.queryset = self.queryset.filter(
                favorite__user=self.request.user
            )
        if is_favorited == '0':
            self.queryset = self.queryset.exclude(
                favorite__user=self.request.user
            )

        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart'
        )
        if is_in_shopping_cart == '1':
            self.queryset = self.queryset.filter(
                shopping_cart__user=self.request.user
            )
        if is_in_shopping_cart == '0':
            self.queryset = self.queryset.exclude(
                shopping_cart__user=self.request.user
            )

        return self.queryset

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PATCH'):
            return RecipeCreateSerializer
        return RecipeGetSerializer

    @action(detail=True,
            methods=('post', 'delete'),
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk):
        return post_delete(
            pk=pk,
            data=request.data,
            request=self.request,
            model=Favorite,
            serializer=FavoriteSerializer
        )

    @action(detail=True,
            methods=('post', 'delete'),
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        return post_delete(
            pk=pk,
            data=request.data,
            request=self.request,
            model=ShoppingCart,
            serializer=ShoppingCartSerializer
        )

    @action(detail=False,
            methods=('get',),
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        if not self.request.user.shopping_cart.exists():
            return Response('Список покупок пуст',
                            status=HTTP_204_NO_CONTENT)
        shopping_cart = [f'Здравствуйте, {self.request.user}, это foodgram'
                         ', ваш список покупок:\n']
        recipes_ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=self.request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            amount=Sum("amount")
        )
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


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (CustomSearchFilter,)
    search_fields = ('^name',)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class UserViewSet(CreateRetrieveListMixin):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # permission_classes = (IsAuthenticatedOrReadOnlyObject,)
    pagination_class = CustomPageNumberPagination

    @action(detail=False,
            methods=('get',),
            permission_classes=(IsAuthenticated,))
    def me(self, request):
        return Response(UserSerializer(self.request.user,
                                       context={'request': request}).data)

    @action(detail=False,
            methods=('post',),
            permission_classes=(IsAuthenticated,))
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(serializer.data.get('new_password'))
        self.request.user.save()
        return Response('Пароль успешно изменен',
                        status=HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=('post', 'delete'),
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, pk):
        author = get_object_or_404(User, id=pk)
        if self.request.method == 'POST':
            context = {
                'request': request,
                'author': author
            }
            serializer = FollowSerializer(
                data=request.data,
                context=context
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=self.request.user, author=author)
            return Response(serializer.data,
                            status=HTTP_201_CREATED)
        if not Follow.objects.filter(user=self.request.user,
                                     author=author).exists():
            return Response('Вы не подписаны на этого пользователя!',
                            status=HTTP_400_BAD_REQUEST)
        get_object_or_404(Follow, user=self.request.user,
                          author=author).delete()
        return Response('Успешная отписка',
                        status=HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=('get',),
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        serializer = FollowSerializer(
            self.paginate_queryset(
                Follow.objects.filter(user=self.request.user).order_by('id'),
            ),
            context={'request': request, 'author': self.request.user},
            many=True)
        return self.get_paginated_response(serializer.data)
