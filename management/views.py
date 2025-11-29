from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsOwnerOrPM
from .models import Project, Sprint, Task
from .serializers import ProjectSerializer, SprintSerializer, TaskSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrPM()]
        return super().get_permissions()

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'PM':
            serializer.save(pm=user)
        else:
            assigned_pm = serializer.validated_data.get('pm') or user
            serializer.save(pm=assigned_pm)


class SprintViewSet(viewsets.ModelViewSet):
    queryset = Sprint.objects.all()
    serializer_class = SprintSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrPM()]
        return super().get_permissions()

    def get_queryset(self):
        return Sprint.objects.annotate(task_count=Count('tasks')).select_related('project')

    def perform_create(self, serializer):
        self._ensure_owner_or_pm()
        serializer.save()

    def perform_update(self, serializer):
        self._ensure_owner_or_pm()
        previous_status = serializer.instance.status
        sprint = serializer.save()
        if previous_status != Sprint.Status.COMPLETED and sprint.status == Sprint.Status.COMPLETED:
            self._create_next_sprint(sprint)

    def perform_destroy(self, instance):
        self._ensure_owner_or_pm()
        instance.delete()

    def _ensure_owner_or_pm(self):
        if self.request.user.role not in ['OWNER', 'PM']:
            raise PermissionDenied('Only Owners or PMs can manage sprints.')

    def _create_next_sprint(self, completed_sprint):
        project = completed_sprint.project
        start_date = completed_sprint.start_date or timezone.now().date()
        next_start_date = start_date + timedelta(days=completed_sprint.duration_days + 1)
        next_number = project.sprints.count() + 1
        Sprint.objects.create(
            project=project,
            name=f'Sprint {next_number}',
            start_date=next_start_date,
            duration_days=7,
            status=Sprint.Status.OPEN,
        )


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.all()
        if user.role in ['OWNER', 'PM']:
            return queryset
        return queryset.filter(assignee=user)

    def perform_create(self, serializer):
        self._require_owner_or_pm()
        serializer.save()

    def perform_update(self, serializer):
        self._require_owner_or_pm()
        serializer.save()

    def perform_destroy(self, instance):
        self._require_owner_or_pm()
        instance.delete()

    def _require_owner_or_pm(self):
        if self.request.user.role not in ['OWNER', 'PM']:
            raise PermissionDenied('Only Owners or PMs can modify tasks via this endpoint.')

    @action(detail=False, methods=['get'], url_path='my-tasks')
    def my_tasks(self, request):
        queryset = self.get_queryset().filter(assignee=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='change-status')
    def change_status(self, request, pk=None):
        task = self.get_object()
        new_status = request.data.get('status')
        if not new_status:
            raise ValidationError({'status': 'This field is required.'})

        valid_statuses = [choice[0] for choice in Task.Status.choices]
        if new_status not in valid_statuses:
            raise ValidationError({'status': 'Invalid status value.'})

        user = request.user
        if user.role == 'DEV':
            if task.assignee_id != user.id:
                raise PermissionDenied('Developers can only update their own tasks.')
            allowed_statuses = {
                Task.Status.TO_DO: Task.Status.IN_PROGRESS,
                Task.Status.IN_PROGRESS: Task.Status.QA_TESTING,
                Task.Status.QA_TESTING: Task.Status.PM_REVIEW,
            }
            next_allowed = allowed_statuses.get(task.status)
            if next_allowed != new_status:
                raise ValidationError('Invalid status transition for developer.')
        elif user.role not in ['OWNER', 'PM']:
            raise PermissionDenied('You are not allowed to change status for this task.')

        task.status = new_status
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)
