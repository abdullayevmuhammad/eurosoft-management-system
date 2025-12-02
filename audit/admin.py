from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "user", "model", "object_id", "ip_address")
    list_filter = ("action", "model", "user")
    search_fields = ("object_repr", "object_id", "path", "user__email")
    readonly_fields = (
        "user", "action", "model", "object_id", "object_repr",
        "changes", "path", "method", "ip_address", "created_at"
    )

    def has_add_permission(self, request):
        return False  # AuditLog qo‘lda qo‘shilmaydi

    def has_change_permission(self, request, obj=None):
        return False  # AuditLog o‘zgarmaydi
