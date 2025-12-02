from django.conf import settings
from django.db import models


class AuditLog(models.Model):
	class Action(models.TextChoices):
		CREATE = 'CREATE', 'Create'
		UPDATE = 'UPDATE', 'Update'
		SOFT_DELETE = 'SOFT_DELETE', 'Soft Delete'
		HARD_DELETE = 'HARD_DELETE', 'Hard Delete'

	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name='audit_logs',
	)
	action = models.CharField(max_length=20, choices=Action.choices)
	model = models.CharField(max_length=255)
	object_id = models.CharField(max_length=64)
	object_repr = models.CharField(max_length=255)
	changes = models.JSONField(default=dict, blank=True)
	path = models.CharField(max_length=2048, blank=True)
	method = models.CharField(max_length=16, blank=True)
	ip_address = models.GenericIPAddressField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.action} {self.model}:{self.object_id}"
