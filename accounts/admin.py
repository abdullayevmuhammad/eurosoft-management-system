from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from audit.models import AuditLog
from audit.utils import write_audit
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ['email']
    list_display = ['email', 'name', 'role', 'is_staff', 'is_active', 'id']
    list_filter = ['role', 'is_staff', 'is_active']
    search_fields = ['email', 'name']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'role')}),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        ('Important dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'role', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )
	
    filter_horizontal = ['groups', 'user_permissions']

    # Soft-delete bo'lgan userlarni ham ko‘rsatish
    def get_queryset(self, request):
        return User.all_objects.all()

    # --- HARD DELETE ---
    def delete_model(self, request, obj):
        write_audit(
            action=AuditLog.Action.HARD_DELETE,
            instance=obj,
            user=request.user,
            changes={'deleted': {'old': False, 'new': True}},
            request=request,
        )
        obj.hard_delete()

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            write_audit(
                action=AuditLog.Action.HARD_DELETE,
                instance=obj,
                user=request.user,
                changes={'deleted': {'old': False, 'new': True}},
                request=request,
            )
            obj.hard_delete()
