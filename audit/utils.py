from .models import AuditLog


def write_audit(action, instance, user=None, changes=None, request=None):


    AuditLog.objects.create(
        user=user,
        action=action,
        model=f"{instance._meta.app_label}.{instance.__class__.__name__}",
        object_id=str(instance.pk),
        object_repr=str(instance),
        changes=changes or {},
        path=request.path if request else "",
        method=request.method if request else "",
        ip_address=request.META.get("REMOTE_ADDR") if request else None,
    )
