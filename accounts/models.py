from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone



class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return super().update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()



class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        # default — faqat alive
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def hard_delete(self):
        return self.get_queryset().hard_delete()

    def all_with_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db)


class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()                       # default manager
    all_objects = SoftDeleteQuerySet.as_manager()       # manager for all rows

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def hard_delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)


# ============================
#       User Manager
# ============================

class UserManager(SoftDeleteManager, BaseUserManager):
    """
    SoftDelete + create_user + create_superuser birlashtirilgan manager
    """

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

        return self.create_user(email, password, name=name, **extra_fields)


# ============================
#           User Model
# ============================

class User(AbstractBaseUser, PermissionsMixin, SoftDeleteModel):
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

    all_objects = SoftDeleteQuerySet.as_manager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email} ({self.role})"
