# accounts/views.py
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied

from .models import User
from .serializers import UserSerializer, UserCreateSerializer
from .permissions import IsOwnerOrPM
from drf_yasg.utils import swagger_auto_schema

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(responses={200: UserSerializer()})
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=UserSerializer, responses={200: UserSerializer()})
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserListCreateAPIView(generics.ListCreateAPIView):

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

from .serializers import UserPasswordResetSerializer
from drf_yasg.utils import swagger_auto_schema

class UserPasswordResetAPIView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserPasswordResetSerializer
    permission_classes = [IsOwnerOrPM]

    @swagger_auto_schema(request_body=UserPasswordResetSerializer)
    def patch(self, request, pk=None):
        editor: User = request.user
        target: User = self.get_object()

        # PM cheklovlari
        if editor.role == User.Role.PM and target.role in (User.Role.OWNER, User.Role.PM):
            raise PermissionDenied("PM OWNER yoki PM parolini o'zgartira olmaydi.")

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_password = serializer.validated_data["password"]
        target.set_password(new_password)
        target.save(update_fields=["password"])

        return Response({"detail": "Password successfully reset."})