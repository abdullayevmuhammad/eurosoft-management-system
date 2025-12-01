# accounts/views.py
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied

from .models import User
from .serializers import UserSerializer, UserCreateSerializer
from .permissions import IsOwnerOrPM


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /accounts/users/  -> Owner va PM userlarni ko'radi
    POST /accounts/users/  -> Owner/PM yangi user qo'shadi

    RBAC:
    - OWNER: istalgan rol (OWNER, PM, DEV, VIEWER) yaratishi mumkin
    - PM: faqat DEV (va xohlasang VIEWER) yaratishi mumkin
    - DEV/VIEWER: umuman kira olmaydi (IsOwnerOrPM bloklaydi)
    """
    queryset = User.objects.all()
    permission_classes = [IsOwnerOrPM]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer

    def perform_create(self, serializer):
        creator = self.request.user
        new_role = serializer.validated_data.get('role', User.Role.DEV)

        if creator.role == User.Role.OWNER:
            # Owner hamma rolni qo'sha oladi
            pass
        elif creator.role == User.Role.PM:
            # PM faqat Developer (va istasang VIEWER) qo'sha oladi
            if new_role not in (User.Role.DEV, User.Role.VIEWER):
                raise PermissionDenied("PM faqat DEV yoki VIEWER user qo'sha oladi.")
        else:
            # Teorik jihatdan bu yerga kelmaydi, chunki IsOwnerOrPM bloklab qo'ygan
            raise PermissionDenied("Faqat OWNER yoki PM user qo'sha oladi.")

        serializer.save()


class UserDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /accounts/users/<id>/
    PATCH  /accounts/users/<id>/
    DELETE /accounts/users/<id>/

    RBAC:
    - OWNER: hamma userni ko'radi va tahrir qiladi
    - PM: faqat DEV/VIEWER userlarni tahrir/o'chirishi mumkin
    - DEV/VIEWER: kira olmaydi
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsOwnerOrPM]

    def perform_update(self, serializer):
        editor: User = self.request.user
        target: User = self.get_object()

        if editor.role == User.Role.PM and target.role in (User.Role.OWNER, User.Role.PM):
            raise PermissionDenied("PM OWNER yoki boshqa PM ni tahrir qila olmaydi.")

        # role/email read-only, faqat name o'zgaradi
        serializer.save()

    def perform_destroy(self, instance):
        editor: User = self.request.user
        if editor.role == User.Role.PM and instance.role in (User.Role.OWNER, User.Role.PM):
            raise PermissionDenied("PM OWNER yoki boshqa PM ni o'chira olmaydi.")
        instance.delete()
