from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from backend.constants import EMAIL_LENGTH, PERSONAL_FIELDS_LENGTH, REPR_SIZE


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name', 'password')

    email = models.EmailField(max_length=EMAIL_LENGTH,
                              unique=True,
                              verbose_name='Электронная почта')
    username = models.CharField(
        max_length=PERSONAL_FIELDS_LENGTH,
        validators=(RegexValidator(r'^[\w.@+-]+$'),),
        unique=True,
        verbose_name='Логин'
    )
    first_name = models.CharField(max_length=PERSONAL_FIELDS_LENGTH,
                                  verbose_name='Имя')
    last_name = models.CharField(max_length=PERSONAL_FIELDS_LENGTH,
                                 verbose_name='Фамилия')
    password = models.CharField(max_length=PERSONAL_FIELDS_LENGTH,
                                verbose_name='Пароль')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username[:REPR_SIZE]


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
        return f'{self.user} подписан на {self.author}'
