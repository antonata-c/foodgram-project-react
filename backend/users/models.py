from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    USER = 'user'
    ADMIN = 'admin'
    ROLES = (
        (USER, 'Пользователь'),
        (ADMIN, 'Админ')
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name', 'password')

    email = models.EmailField(max_length=settings.EMAIL_LENGTH,
                              blank=False,
                              null=False,
                              unique=True,
                              verbose_name='Электронная почта')
    username = models.CharField(
        max_length=settings.PERSONAL_FIELDS_LENGTH,
        blank=False,
        null=False,
        validators=(RegexValidator(r'^[\w.@+-]+$'),),
        unique=True,
        verbose_name='Логин'
    )
    first_name = models.CharField(max_length=settings.PERSONAL_FIELDS_LENGTH,
                                  blank=False,
                                  null=False,
                                  verbose_name='Имя')
    last_name = models.CharField(max_length=settings.PERSONAL_FIELDS_LENGTH,
                                 blank=False,
                                 null=False,
                                 verbose_name='Фамилия')
    password = models.CharField(max_length=settings.PERSONAL_FIELDS_LENGTH,
                                blank=False,
                                null=False,
                                verbose_name='Пароль')
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
        return self.role == self.ADMIN or self.is_superuser or self.is_staff

    def __str__(self):
        return self.username[:settings.REPR_SIZE]


class Follow(models.Model):
    user = models.ForeignKey(User,
                             related_name='follower',
                             on_delete=models.CASCADE,
                             verbose_name='Подписчик')
    author = models.ForeignKey(User,
                               related_name='following',
                               on_delete=models.CASCADE,
                               verbose_name='Автор подписчика')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = (
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow'),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='check_self_follow')
        )

    def __str__(self):
        return f"{self.user} подписан на {self.author}"
