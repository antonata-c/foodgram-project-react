from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from .models import User, Follow
from .mixins import CreateRetrieveListMixin
from .serializers import (UserSerializer,
                          SetPasswordSerializer,
                          FollowSerializer)


class UserViewSet(CreateRetrieveListMixin):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False,
            methods=('get',))
    def me(self, request):
        return Response(UserSerializer(self.request.user,
                                       context={'request': request}).data)

    @action(detail=False,
            methods=('post',))
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(serializer.data.get('new_password'))
        self.request.user.save()
        return Response('Пароль успешно изменен',
                        status=HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=('post', 'delete'))
    def subscribe(self, request, pk):
        author = get_object_or_404(User, id=pk)
        if self.request.method == 'POST':
            serializer = FollowSerializer(
                data=request.data,
                context={'request': request, 'author': author}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=self.request.user, author=author)
            return Response(serializer.data,
                            status=HTTP_201_CREATED)
        get_object_or_404(Follow, user=self.request.user,
                          author=author).delete()
        return Response('Успешная отписка',
                        status=HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=('get',))
    def subscriptions(self, request):
        return Response(FollowSerializer(
            Follow.objects.filter(user=self.request.user),
            context={'request': request, 'author': self.request.user},
            many=True
        ).data)
