from rest_framework import serializers

from recipes.models import Recipe, Ingredient, Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):

    def create(self, validated_data):

        return Recipe.objects.create(**validated_data)

    class Meta:
        model = Recipe
        fields = '__all__'
