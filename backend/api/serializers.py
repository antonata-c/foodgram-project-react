import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.validators import ValidationError

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow, User


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class ShoppingFavoriteAbstractSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='recipe',
        read_only=True
    )
    name = serializers.CharField(
        source='recipe.name',
        read_only=True
    )
    image = serializers.ImageField(
        source='recipe.image',
        read_only=True
    )
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time',
        read_only=True
    )

    def validate(self, data, detail=None, model=None):
        if model.objects.filter(
                user=self.context.get('user'),
                recipe=self.context.get('recipe')
        ).exists():
            raise ValidationError(
                detail=f'Выбранный рецепт уже есть в {detail}.',
                code=HTTP_400_BAD_REQUEST)
        return data

    class Meta:
        abstract = True


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    def to_representation(self, instance):
        to_repr = super(UserSerializer, self).to_representation(instance)
        if self.context.get('request').method == 'POST':
            to_repr.pop('is_subscribed')
        return to_repr

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Follow.objects.filter(
            user=user, author=obj
        ).exists()

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
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user,
                                       recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            user=user,
            recipe=obj
        ).exists()


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

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
        request = self.context.get('request')
        serializer = RecipeGetSerializer(instance,
                                         context={'request': request})
        return serializer.data

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        recipe_ingredients = []
        for ingredient in ingredients:
            recipe_ingredients.append(RecipeIngredient(
                ingredient=ingredient.get('id'),
                recipe=recipe,
                amount=ingredient.get('amount')
            ))
        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        RecipeIngredient.objects.filter(recipe=instance).delete()
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                ingredient=ingredient.get('id'),
                recipe=instance,
                amount=ingredient.get('amount')
            )
        instance.tags.set(tags)
        instance.image = validated_data.get('image')
        instance.text = validated_data.get('text')
        instance.name = validated_data.get('name')
        instance.cooking_time = validated_data.get('cooking_time')
        instance.save()
        return instance

    def validate(self, data):
        if data.get('ingredients') is None:
            raise ValidationError(
                {'ingredients': 'Обязательное поле.'}
            )
        if data.get('tags') is None:
            raise ValidationError(
                {'tags': 'Обязательное поле.'}
            )
        return data

    def validate_ingredients(self, value):
        if not value:
            raise ValidationError(
                {'ingredients': 'Поле не может быть пустым'}
            )
        tmp_ingredients = []
        for ingredient in value:
            if ingredient in tmp_ingredients:
                raise ValidationError(
                    {'ingredients': 'В поле не может быть повторений'}
                )
            tmp_ingredients.append(ingredient)
        return value

    def validate_tags(self, value):
        if not value:
            raise ValidationError(
                {'tags': 'Поле не может быть пустым'})
        if list(set(value)) != value:
            raise ValidationError(
                {'tags': 'В поле не может быть повторений'})
        return value


class FavoriteSerializer(ShoppingFavoriteAbstractSerializer):
    def validate(self, data):
        return super().validate(data,
                                detail='избранном',
                                model=Favorite)

    class Meta:
        model = Favorite
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartSerializer(ShoppingFavoriteAbstractSerializer):
    def validate(self, data):
        return super().validate(data,
                                detail='списке покупок',
                                model=ShoppingCart)

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = (
            'email', 'id',
            'username', 'first_name',
            'last_name', 'is_subscribed',
            'recipes', 'recipes_count'
        )

    def to_representation(self, instance):
        to_repr = super(FollowSerializer, self).to_representation(instance)
        request = self.context.get('request')
        if request and request.query_params.get('recipes_limit'):
            to_repr['recipes'] = (to_repr['recipes'][:int(
                request.query_params.get('recipes_limit')
            )])
        return to_repr

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(user=obj.user, author=obj.author).exists()

    def get_recipes(self, obj):
        recipes = Recipe.objects.filter(author=obj.author)
        return RecipeFollowSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj.author).count()

    def validate(self, data):
        user = self.context.get('request').user
        if user == self.context.get('author'):
            raise ValidationError(
                detail='Самоподписка запрещена.',
                code=HTTP_400_BAD_REQUEST)
        if Follow.objects.filter(
                author=self.context.get('author'),
                user=user).exists():
            raise ValidationError(
                detail='Подписка на этого пользователя уже существует.',
                code=HTTP_400_BAD_REQUEST)
        return data


class SetPasswordSerializer(serializers.Serializer):
    model = User
    current_password = serializers.CharField(max_length=150, required=True)
    new_password = serializers.CharField(max_length=150, required=True)

    def validate(self, data):
        if not self.context.get('request').user.check_password(
                data.get("current_password")
        ):
            raise ValidationError({"current_password": ["Неверный пароль!"]})
        return data


class RecipeFollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
