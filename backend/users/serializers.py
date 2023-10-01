from rest_framework import serializers
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.validators import ValidationError

from recipes.models import Recipe
from .models import User, Follow
from api.serializers import RecipeFollowSerializer


class UserSerializer(serializers.ModelSerializer):
    # is_subscribed = serializers.SerializerMethodField()

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
            # 'is_subscribed'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            #'is_subscribed': {'read_only': True}
        }


class FollowSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

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

    class Meta:
        model = Follow
        fields = (
            'email', 'id',
            'username', 'first_name',
            'last_name', 'is_subscribed',
            'recipes', 'recipes_count'
        )


class SetPasswordSerializer(serializers.Serializer):
    model = User
    current_password = serializers.CharField(max_length=150, required=True)
    new_password = serializers.CharField(max_length=150, required=True)

    def validate(self, data):
        if not self.context.get('request').user.check_password(
                data.get("current_password")
        ):
            raise ValidationError({"current_password": ["Wrong password."]})
        return data
