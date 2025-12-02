from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "action",
            "model",
            "object_id",
            "object_repr",
            "user",
            "user_email",
            "changes",
            "path",
            "method",
            "ip_address",
            "created_at",
        ]
        read_only_fields = fields
