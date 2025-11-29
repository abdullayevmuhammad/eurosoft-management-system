from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Project(models.Model):
	class Status(models.TextChoices):
		STARTED = 'STARTED', 'Started'
		COMPLETED = 'COMPLETED', 'Completed'
		ON_HOLD = 'ON_HOLD', 'On Hold'

	title = models.CharField(max_length=255)
	start_date = models.DateField(null=True, blank=True)
	end_date = models.DateField(null=True, blank=True)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.STARTED)
	pm = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_projects')

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.title


class Sprint(models.Model):
	class Status(models.TextChoices):
		OPEN = 'OPEN', 'Open'
		IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
		COMPLETED = 'COMPLETED', 'Completed'

	project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sprints')
	name = models.CharField(max_length=100)
	start_date = models.DateField()
	duration_days = models.PositiveIntegerField(default=7)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"{self.project.title} - {self.name}"


class Task(models.Model):
	class Status(models.TextChoices):
		TO_DO = 'TO_DO', 'To Do'
		IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
		QA_TESTING = 'QA_TESTING', 'QA Testing'
		PM_REVIEW = 'PM_REVIEW', 'PM Review'
		COMPLETED = 'COMPLETED', 'Completed'
		ON_HOLD = 'ON_HOLD', 'On Hold'

	sprint = models.ForeignKey(Sprint, on_delete=models.CASCADE, related_name='tasks')
	title = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	assignee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
	start_date = models.DateField(null=True, blank=True)
	due_date = models.DateField(null=True, blank=True)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.TO_DO)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.title
