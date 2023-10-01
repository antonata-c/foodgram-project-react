import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from recipes.models import Recipe, Ingredient, Tag, RecipeIngredient


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


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

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'ingredients',
            # 'is_favorited',
            # 'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True)
    ingredients = RecipeIngredientSerializer(required=True, many=True)
    tags = serializers.SlugRelatedField(
        many=True, queryset=Tag.objects.all(), slug_field='id'
    )

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
        for ingredient in ingredients:
            RecipeIngredient.objects.create(
                ingredient=ingredient.get('id'),
                recipe=recipe,
                amount=ingredient.get('amount')
            )
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
        ]


class RecipeFollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
