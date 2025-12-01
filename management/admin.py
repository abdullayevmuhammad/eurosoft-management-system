from django.contrib import admin

from .models import Project, Sprint, Task


class SprintInline(admin.TabularInline):
	model = Sprint
	extra = 1

class TaskInline(admin.TabularInline):
	model = Task
	extra = 1

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
	list_display = ['title', 'pm', 'status', 'start_date', 'end_date']
	list_filter = ['status']
	search_fields = ['title', 'pm__email']
	inlines = [SprintInline]


@admin.register(Sprint)
class SprintAdmin(admin.ModelAdmin):
	list_display = ['name', 'project', 'status', 'start_date', 'duration_days']
	list_filter = ['status', 'project']
	search_fields = ['name', 'project__title']
	inlines = [TaskInline]

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
	list_display = ['title', 'sprint', 'status', 'due_date']
	list_filter = ['status', 'sprint__project']
	search_fields = ['title', 'assignees__email']
