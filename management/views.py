from datetime import timedelta

from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator

from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg.utils import swagger_auto_schema

from accounts.models import User
from accounts.permissions import IsOwnerOrPM, IsNotViewer
from audit.utils import write_audit
from audit.models import AuditLog

from .models import Project, Sprint, Task
from .serializers import (
    ProjectSerializer,
    SprintSerializer,
    TaskSerializer,
    TaskStatusUpdateSerializer
)

from rest_framework.parsers import MultiPartParser, FormParser


@method_decorator(name='get', decorator=swagger_auto_schema(tags=['Projects']))
@method_decorator(name='post', decorator=swagger_auto_schema(tags=['Projects']))
class ProjectListCreateAPIView(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsOwnerOrPM()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        pm = serializer.validated_data.get("pm")

        if user.role == User.Role.PM and pm is None:
            instance = serializer.save(pm=user)
        else:
            instance = serializer.save()

        write_audit(
            action=AuditLog.Action.CREATE,
            instance=instance,
            user=user,
            request=self.request
        )
        return instance


@method_decorator(name='get', decorator=swagger_auto_schema(tags=['Projects']))
@method_decorator(name='put', decorator=swagger_auto_schema(tags=['Projects']))
@method_decorator(name='patch', decorator=swagger_auto_schema(tags=['Projects']))
@method_decorator(name='delete', decorator=swagger_auto_schema(tags=['Projects']))
class ProjectDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_permissions(self):
        if self.request.method in ("PATCH", "PUT", "DELETE"):
            return [IsOwnerOrPM()]
        return [IsAuthenticated()]

    def perform_update(self, serializer):
        instance = serializer.save()

        write_audit(
            action=AuditLog.Action.UPDATE,
            instance=instance,
            user=self.request.user,
            changes=self.request.data,
            request=self.request
        )
        return instance

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])

        write_audit(
            action=AuditLog.Action.SOFT_DELETE,
            instance=instance,
            user=self.request.user,
            changes={"deleted": True},
            request=self.request
        )


@method_decorator(name='get', decorator=swagger_auto_schema(tags=['Sprints']))
@method_decorator(name='post', decorator=swagger_auto_schema(tags=['Sprints']))
class SprintListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = SprintSerializer

    def get_queryset(self):
        return (
            Sprint.objects.annotate(task_count=Count("tasks")).select_related("project")
        )

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsOwnerOrPM()]
        return [IsAuthenticated(), IsNotViewer()]

    def perform_create(self, serializer):
        instance = serializer.save()
        write_audit(
            action=AuditLog.Action.CREATE,
            instance=instance,
            user=self.request.user,
            request=self.request
        )
        return instance


@method_decorator(name='get', decorator=swagger_auto_schema(tags=['Sprints']))
@method_decorator(name='put', decorator=swagger_auto_schema(tags=['Sprints']))
@method_decorator(name='patch', decorator=swagger_auto_schema(tags=['Sprints']))
@method_decorator(name='delete', decorator=swagger_auto_schema(tags=['Sprints']))
class SprintDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SprintSerializer

    def get_queryset(self):
        return (
            Sprint.objects.annotate(task_count=Count("tasks")).select_related("project")
        )

    def get_permissions(self):
        if self.request.method in ("PATCH", "PUT", "DELETE"):
            return [IsOwnerOrPM()]
        return [IsAuthenticated(), IsNotViewer()]

    def perform_update(self, serializer):
        sprint = serializer.save()


        write_audit(
            action=AuditLog.Action.UPDATE,
            instance=sprint,
            user=self.request.user,
            changes=self.request.data,
            request=self.request,
        )

        return sprint

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])

        write_audit(
            action=AuditLog.Action.SOFT_DELETE,
            instance=instance,
            user=self.request.user,
            changes={"deleted": True},
            request=self.request
        )


@method_decorator(name='get', decorator=swagger_auto_schema(tags=['Tasks']))
@method_decorator(name='post', decorator=swagger_auto_schema(tags=['Tasks']))
class TaskListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    parser_classes = [MultiPartParser, FormParser]
    def get_queryset(self):
        user = self.request.user
        qs = Task.objects.select_related("sprint", "sprint__project").prefetch_related("assignees")

        if user.role in (User.Role.OWNER, User.Role.PM):
            return qs
        return qs.filter(assignees=user)

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsOwnerOrPM()]
        return [IsAuthenticated(), IsNotViewer()]

    def perform_create(self, serializer):
        instance = serializer.save()

        write_audit(
            action=AuditLog.Action.CREATE,
            instance=instance,
            user=self.request.user,
            request=self.request
        )
        return instance


@method_decorator(name='get', decorator=swagger_auto_schema(tags=['Tasks']))
@method_decorator(name='put', decorator=swagger_auto_schema(tags=['Tasks']))
@method_decorator(name='patch', decorator=swagger_auto_schema(tags=['Tasks']))
@method_decorator(name='delete', decorator=swagger_auto_schema(tags=['Tasks']))
class TaskDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    queryset = Task.objects.select_related("sprint", "sprint__project").prefetch_related("assignees")
    parser_classes = [MultiPartParser, FormParser]
    def get_permissions(self):
        if self.request.method in ("PATCH", "PUT", "DELETE"):
            return [IsOwnerOrPM()]
        return [IsAuthenticated(), IsNotViewer()]

    def get_object(self):
        obj = super().get_object()
        user = self.request.user

        if user.role == User.Role.DEV and not obj.assignees.filter(id=user.id).exists():
            raise PermissionDenied("You cannot access tasks not assigned to you.")

        return obj

    def perform_update(self, serializer):
        instance = serializer.save()

        write_audit(
            action=AuditLog.Action.UPDATE,
            instance=instance,
            user=self.request.user,
            changes=self.request.data,
            request=self.request
        )
        return instance

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])

        write_audit(
            action=AuditLog.Action.SOFT_DELETE,
            instance=instance,
            user=self.request.user,
            changes={"deleted": True},
            request=self.request
        )



@method_decorator(name='get', decorator=swagger_auto_schema(tags=['Tasks']))
class MyTasksAPIView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated, IsNotViewer]

    def get_queryset(self):
        return (
            Task.objects
            .filter(assignees=self.request.user)
            .select_related("sprint", "sprint__project")
            .prefetch_related("assignees")
        )



class TaskStatusUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsNotViewer]

    @swagger_auto_schema(
        request_body=TaskStatusUpdateSerializer,
        responses={200: TaskSerializer()},
        tags=['Tasks']
    )
    def patch(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        user = request.user
        new_status = request.data.get("status")
        old_status = task.status

        if not new_status:
            raise ValidationError({"status": "This field is required."})

        if user.role == User.Role.DEV:
            if not task.assignees.filter(id=user.id).exists():
                raise PermissionDenied("You can only change status of your own tasks.")

            allowed = {
                Task.Status.TO_DO,
                Task.Status.IN_PROGRESS,
                Task.Status.QA_TESTING,
                Task.Status.PM_REVIEW,
            }
            if new_status not in allowed:
                raise ValidationError({"status": "Developer cannot set this status."})

            if old_status == Task.Status.TO_DO and new_status != Task.Status.IN_PROGRESS:
                raise ValidationError({"status": "From TO_DO only IN_PROGRESS is allowed."})

            if old_status == Task.Status.IN_PROGRESS and new_status != Task.Status.QA_TESTING:
                raise ValidationError({"status": "From IN_PROGRESS only QA_TESTING is allowed."})

            if old_status == Task.Status.QA_TESTING and new_status != Task.Status.PM_REVIEW:
                raise ValidationError({"status": "From QA_TESTING only PM_REVIEW is allowed."})

            if old_status == Task.Status.PM_REVIEW:
                raise ValidationError({"status": "Developer cannot change status from PM_REVIEW."})

        elif user.role in (User.Role.PM, User.Role.OWNER):
            if new_status not in Task.Status.values:
                raise ValidationError({"status": "Invalid status value."})

        else:
            raise PermissionDenied("You are not allowed to change task status.")

        task.status = new_status
        task.save(update_fields=["status", "updated_at"])

        write_audit(
            action=AuditLog.Action.UPDATE,
            instance=task,
            user=request.user,
            changes={"status": {"old": old_status, "new": new_status}},
            request=request
        )

        serializer = TaskSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)
