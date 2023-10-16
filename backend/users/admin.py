from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Follow


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'username',
                    'email', 'first_name',
                    'last_name', 'get_follow_count', 'get_recipes_count')
    list_filter = ('username', 'email',)

    def get_follow_count(self, obj):
        return obj.follower.count()

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    get_follow_count.short_description = 'Количество подписок'
    get_recipes_count.short_description = 'Количество рецептов'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    list_filter = ('user',)
    search_fields = ('user', 'author',)
