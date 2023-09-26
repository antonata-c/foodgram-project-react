from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

# TODO: verboses, consts to settings
class User(AbstractUser):
    USER = 'user'
    ADMIN = 'admin'
    ROLES = (
        (USER, 'Пользователь'),
        (ADMIN, 'Админ')
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name', 'password')

    email = models.EmailField(max_length=254,
                              blank=False,
                              null=False,
                              unique=True,
                              verbose_name='Электронная почта')
    username = models.CharField(
        max_length=150,
        blank=False,
        null=False,
        validators=(RegexValidator(r'^[\w.@+-]+$'),),
        unique=True,
        verbose_name='Логин'
    )
    first_name = models.CharField(max_length=150, blank=False,
                                  null=False, verbose_name='Имя')
    last_name = models.CharField(max_length=150, blank=False,
                                 null=False, verbose_name='Фамилия')
    password = models.CharField(max_length=150, blank=False,
                                null=False, verbose_name='Пароль')
    role = models.CharField(
        max_length=max([len(verbose) for _, verbose in ROLES]),
        choices=ROLES,
        default=USER,
        verbose_name='Роль'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    @property
    def is_admin(self):
        return self.role == self.ADMIN

    def __str__(self):
        return self.username[:15]
