from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import AuditLog
from .serializers import AuditLogSerializer
from accounts.permissions import IsOwner

class AuditLogListAPIView(generics.ListAPIView):

    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        qs = AuditLog.objects.select_related("user")

        action = self.request.GET.get("action")
        model = self.request.GET.get("model")
        user_id = self.request.GET.get("user_id")

        if action:
            qs = qs.filter(action=action)
        if model:
            qs = qs.filter(model=model)
        if user_id:
            qs = qs.filter(user_id=user_id)

        return qs.order_by("-created_at")

    @swagger_auto_schema(
        tags=["Audit"],
        operation_summary="Audit loglar ro'yxati (faqat OWNER)",
        manual_parameters=[
            openapi.Parameter(
                "action",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Action: CREATE / UPDATE / SOFT_DELETE / HARD_DELETE"
            ),
            openapi.Parameter(
                "model",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description='Masalan: "management.Project"'
            ),
            openapi.Parameter(
                "user_id",
                openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="Logni qilgan user ID"
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()  # 👈 MUHIM!
        serializer = AuditLogSerializer(queryset, many=True)
        return Response(serializer.data)
