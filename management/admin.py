from django.contrib import admin

from audit.models import AuditLog
from audit.utils import write_audit

from .models import Project, Sprint, Task


class SprintInline(admin.TabularInline):
    model = Sprint
    extra = 1


class TaskInline(admin.TabularInline):
    model = Task
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'pm', 'status', 'start_date', 'end_date', 'is_deleted', 'deleted_at']
    list_filter = ['status', 'is_deleted']
    search_fields = ['title', 'pm__email']
    inlines = [SprintInline]

    def get_queryset(self, request):
        # admin panelda soft-delete bo'lgan Project-lar ham ko'rinsin
        return Project.all_objects.all()

    def delete_model(self, request, obj):
        # Audit log
        write_audit(
            action=AuditLog.Action.HARD_DELETE,
            instance=obj,
            user=request.user,
            changes={'deleted': {'old': obj.is_deleted, 'new': True}},
            request=request,
        )
        # Haqiqiy o'chirish
        obj.hard_delete()

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            write_audit(
                action=AuditLog.Action.HARD_DELETE,
                instance=obj,
                user=request.user,
                changes={'deleted': {'old': obj.is_deleted, 'new': True}},
                request=request,
            )
            obj.hard_delete()


@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'status', 'start_date', 'duration_days', 'is_deleted', 'deleted_at']
    list_filter = ['status', 'project', 'is_deleted']
    search_fields = ['name', 'project__title']
    inlines = [TaskInline]

    def get_queryset(self, request):
        return Sprint.all_objects.all()

    def delete_model(self, request, obj):
        write_audit(
            action=AuditLog.Action.HARD_DELETE,
            instance=obj,
            user=request.user,
            changes={'deleted': {'old': obj.is_deleted, 'new': True}},
            request=request,
        )
        obj.hard_delete()

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            write_audit(
                action=AuditLog.Action.HARD_DELETE,
                instance=obj,
                user=request.user,
                changes={'deleted': {'old': obj.is_deleted, 'new': True}},
                request=request,
            )
            obj.hard_delete()


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'sprint', 'status', 'due_date', 'is_deleted', 'deleted_at']
    list_filter = ['status', 'sprint__project', 'is_deleted']
    search_fields = ['title', 'assignees__email']

    def get_queryset(self, request):
        return Task.all_objects.all()

    def delete_model(self, request, obj):
        write_audit(
            action=AuditLog.Action.HARD_DELETE,
            instance=obj,
            user=request.user,
            changes={'deleted': {'old': obj.is_deleted, 'new': True}},
            request=request,
        )
        obj.hard_delete()

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            write_audit(
                action=AuditLog.Action.HARD_DELETE,
                instance=obj,
                user=request.user,
                changes={'deleted': {'old': obj.is_deleted, 'new': True}},
                request=request,
            )
            obj.hard_delete()
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" height="60" />', obj.image.url)
        return "No Image"

    image_preview.short_description = "Image"