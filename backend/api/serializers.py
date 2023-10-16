from django.core.validators import MinValueValidator
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.validators import ValidationError

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow, User


class RecipeShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingFavoriteAbstractSerializer(serializers.ModelSerializer):
    def validate(self, data):
        if self.Meta.model.objects.filter(
                user=data.get('user'),
                recipe=data.get('recipe')
        ).exists():
            raise ValidationError(
                detail='Выбранный рецепт уже есть в '
                       f'{self.Meta.model.__name__}.',
                code=HTTP_400_BAD_REQUEST)
        return data

    def to_representation(self, instance):
        return RecipeShortSerializer(instance.recipe,
                                     context=self.context).data


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request
                and request.user.is_authenticated
                and request.user.follower.filter(author=obj).exists())

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
            'is_subscribed',
        )
        extra_kwargs = {
            'password': {'write_only': True},
        }
        read_only_fields = ("is_subscribed",)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class RecipeIngredientGetSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeGetSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientGetSerializer(
        source='recipe_ingredient',
        many=True
    )
    tags = TagSerializer(many=True)
    author = UserSerializer()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags',
            'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image',
            'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.method == 'POST':
            return False
        return (request
                and request.user.is_authenticated
                and obj.is_favorited)

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.method == 'POST':
            return False
        return (request
                and request.user.is_authenticated
                and obj.is_in_shopping_cart)


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField(validators=(
        MinValueValidator(1, 'Количество ингредиента должно быть не менее 1!'),
    ))

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    ingredients = RecipeIngredientSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    cooking_time = serializers.IntegerField(validators=(
        MinValueValidator(1, 'Время приготовления должно быть не менее 1!'),
    ))

    class Meta:
        model = Recipe
        fields = [
            'id',
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
            'author'
        ]
        required_fields = ('ingredients', 'tags')

    def to_representation(self, instance):
        return RecipeGetSerializer(instance,
                                   context=self.context).data

    def add_recipes_ingredients_tags(self, recipe, ingredients, tags):
        recipe.tags.set(tags)
        for ingredient in ingredients:
            RecipeIngredient.objects.update_or_create(
                ingredient=ingredient.get('id'),
                recipe=recipe,
                amount=ingredient.get('amount')
            )

        # в джанге 4.1 можно добавить параметр update_conflicts и нормально
        # использовать в духе bulk_update_or_create,
        # есть ли решение в 3.2.3 или оставить как сделано выше?
        # RecipeIngredient.objects.bulk_create(recipe_ingredients,
        #                                      update_conflicts=True)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        # Тут ведь автор уже есть в validated_data
        recipe = Recipe.objects.create(**validated_data)
        self.add_recipes_ingredients_tags(recipe, ingredients, tags)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        RecipeIngredient.objects.filter(recipe=instance).delete()
        self.add_recipes_ingredients_tags(instance, ingredients, tags)
        return super().update(instance, validated_data)

    def validate(self, data):
        if not data.get('tags'):
            raise ValidationError(
                {'tags': 'Поле не может быть пустым'}
            )
        if not data.get('ingredients'):
            raise ValidationError(
                {'ingredients': 'Поле не может быть пустым'}
            )
        tmp_ingredients = [Ingredient(ingredient.get('id'))
                           for ingredient in data.get('ingredients')]
        if list(set(tmp_ingredients)) != tmp_ingredients:
            raise ValidationError(
                {'ingredients': 'В поле не может быть повторений'}
            )
        return data

    def validate_image(self, value):
        if not value:
            raise ValidationError(
                {'image': 'Поле не может быть пустым'}
            )
        return value

    def validate_tags(self, value):
        if list(set(value)) != value:
            raise ValidationError(
                {'tags': 'В поле не может быть повторений'})
        return value


class FavoriteSerializer(ShoppingFavoriteAbstractSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')


class ShoppingCartSerializer(ShoppingFavoriteAbstractSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')


class FollowGetSerializer(UserSerializer):
    recipes_count = serializers.ReadOnlyField(source='recipes.count')
    recipes = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id',
            'username', 'first_name',
            'last_name', 'is_subscribed',
            'recipes', 'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        queryset = get_object_or_404(User,
                                     pk=self.context.get('author')
                                     ).recipes.all()
        if recipes_limit:
            try:
                limit = int(request.query_params.get('recipes_limit'))
            except ValueError:
                return {"recipes_limit": "Поле должно быть числовым!"}
            queryset = queryset[:limit]
        return RecipeShortSerializer(
            queryset, context=self.context, many=True
        ).data


class FollowPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('user', 'author')

    def to_representation(self, instance):
        return FollowGetSerializer(instance.author,
                                   context=self.context).data

    def validate(self, data):
        user = data.get('user')
        author = data.get('author')
        if user == author:
            raise ValidationError(
                detail='Самоподписка запрещена.',
                code=HTTP_400_BAD_REQUEST)
        if Follow.objects.filter(
                author=author,
                user=user).exists():
            raise ValidationError(
                detail='Подписка на этого пользователя уже существует.',
                code=HTTP_400_BAD_REQUEST)
        return data
