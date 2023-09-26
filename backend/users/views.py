from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT

from .models import User
from .serializers import UserSerializer, SetPasswordSerializer


class UserViewSet(viewsets.ModelViewSet):
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
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(serializer.data.get('new_password'))
        self.request.user.save()
        return Response('Пароль успешно изменен',
                        status=HTTP_204_NO_CONTENT)
