from django.contrib import admin

from .models import Project, Sprint, Task


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
	list_display = ['title', 'pm', 'status', 'start_date', 'end_date']
	list_filter = ['status']
	search_fields = ['title', 'pm__email']


@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
	list_display = ['name', 'project', 'status', 'start_date', 'duration_days']
	list_filter = ['status', 'project']
	search_fields = ['name', 'project__title']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
	list_display = ['title', 'sprint', 'assignee', 'status', 'due_date']
	list_filter = ['status', 'sprint__project']
	search_fields = ['title', 'assignee__email']
