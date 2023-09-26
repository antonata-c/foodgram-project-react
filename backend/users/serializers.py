from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    # is_subscribed = ...

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


class SetPasswordSerializer(serializers.Serializer):
    model = User
    current_password = serializers.CharField(max_length=150, required=True)
    new_password = serializers.CharField(max_length=150, required=True)

