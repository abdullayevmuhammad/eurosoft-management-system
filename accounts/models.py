from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class UserManager(BaseUserManager):
	def create_user(self, email, password=None, name='', role='DEV', **extra_fields):
		if not email:
			raise ValueError('Email is required')
		email = self.normalize_email(email)
		user = self.model(email=email, name=name, role=role, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_superuser(self, email, password=None, name='Owner', **extra_fields):
		extra_fields.setdefault('is_staff', True)
		extra_fields.setdefault('is_superuser', True)
		extra_fields.setdefault('role', User.Role.OWNER)

		if extra_fields.get('is_staff') is not True:
			raise ValueError('Superuser must have is_staff=True.')
		if extra_fields.get('is_superuser') is not True:
			raise ValueError('Superuser must have is_superuser=True.')

		return self.create_user(email, password, name=name, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
	class Role(models.TextChoices):
		OWNER = 'OWNER', 'Owner'
		PM = 'PM', 'Project Manager'
		DEV = 'DEV', 'Developer'
		VIEWER = 'VIEWER', 'Viewer'

	email = models.EmailField(unique=True)
	name = models.CharField(max_length=150, blank=True)
	role = models.CharField(max_length=20, choices=Role.choices, default=Role.DEV)

	is_active = models.BooleanField(default=True)
	is_staff = models.BooleanField(default=False)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	objects = UserManager()

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = []

	def __str__(self):
		return f"{self.email} ({self.role})"
