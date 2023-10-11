from django.contrib import admin

from .models import User, Follow


class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email',
                    'first_name', 'last_name', 'role')
    list_filter = ('username', 'email',)


admin.site.register(User)
admin.site.register(Follow)
