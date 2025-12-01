from datetime import timedelta

from django.db.models import Count
from django.shortcuts import get_object_or_404

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.models import User
from accounts.permissions import IsOwnerOrPM
from .models import Project, Sprint, Task
from .serializers import ProjectSerializer, SprintSerializer, TaskSerializer



class ProjectListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /management/projects/      -> hamma projectlar (auth userlar uchun)
    POST /management/projects/      -> faqat OWNER/PM create qila oladi
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_permissions(self):
        # Yaratish faqat OWNER yoki PM
        if self.request.method == "POST":
            return [IsOwnerOrPM()]
        # List qilish - login bo'lgan hamma foydalanuvchilarga ruxsat
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        user: User = self.request.user
        pm = serializer.validated_data.get("pm")

        # Agar PM o'zi project yaratayotgan bo'lsa va body'da pm kelmagan bo'lsa,
        # avtomatik o'zini pm qilib qo'yamiz.
        if user.role == User.Role.PM and pm is None:
            serializer.save(pm=user)
        else:
            serializer.save()
        

class ProjectDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /management/projects/<id>/
    PATCH  /management/projects/<id>/
    DELETE /management/projects/<id>/
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_permissions(self):
        # update/delete faqat OWNER/PM
        if self.request.method in ("PATCH", "PUT", "DELETE"):
            return [IsOwnerOrPM()]
        # detail ko'rish - har qanday auth user
        return [IsAuthenticated()]


class SprintListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /management/sprints/       -> sprintlar ro'yxati (task_count bilan)
    POST /management/sprints/       -> faqat OWNER/PM create qila oladi
    """
    serializer_class = SprintSerializer

    def get_queryset(self):
        # har bir sprintga nechta task borligini task_count sifatida qo'shamiz
        return (
            Sprint.objects
            .annotate(task_count=Count("tasks"))
            .select_related("project")
        )

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsOwnerOrPM()]
        return [IsAuthenticated()]


class SprintDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /management/sprints/<id>/
    PATCH  /management/sprints/<id>/   -> statusni COMPLETED qilsak, keyingi sprint auto yaratiladi
    DELETE /management/sprints/<id>/
    """
    serializer_class = SprintSerializer

    def get_queryset(self):
        return (
            Sprint.objects
            .annotate(task_count=Count("tasks"))
            .select_related("project")
        )

    def get_permissions(self):
        if self.request.method in ("PATCH", "PUT", "DELETE"):
            return [IsOwnerOrPM()]
        return [IsAuthenticated()]

    def perform_update(self, serializer):
        sprint: Sprint = self.get_object()
        old_status = sprint.status
        sprint = serializer.save()  # yangilangan qiymatlar shu yerda

        # Agar status endi COMPLETED bo'lsa va oldin COMPLETED bo'lmagan bo'lsa:
        if (
            old_status != Sprint.Status.COMPLETED
            and sprint.status == Sprint.Status.COMPLETED
        ):
            project = sprint.project
            # keyingi sprint start_date: oldingi sprint tugagandan keyin 1 kun
            next_start = sprint.start_date + timedelta(days=sprint.duration_days + 1)

            # nechta sprint borligini hisoblab, nomini auto beramiz
            sprint_count = Sprint.objects.filter(project=project).count()
            next_name = f"Sprint {sprint_count + 1}"

            Sprint.objects.create(
                project=project,
                name=next_name,
                start_date=next_start,
                duration_days=7,
                status=Sprint.Status.OPEN,
            )


class TaskListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /management/tasks/     -> 
        - OWNER/PM: hamma tasklar
        - DEV/VIEWER: faqat o'ziga assign qilingan tasklar
    POST /management/tasks/     -> faqat OWNER/PM create qila oladi
    """
    serializer_class = TaskSerializer

    def get_queryset(self):
        user: User = self.request.user
        qs = (
            Task.objects
            .select_related("sprint", "sprint__project")
            .prefetch_related("assignees")
        )
        if user.role in (User.Role.OWNER, User.Role.PM):
            return qs
        # Developer yoki Viewer - faqat o'z tasklari
        return qs.filter(assignees=user)

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsOwnerOrPM()]
        return [IsAuthenticated()]

class TaskDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /management/tasks/<id>/
    PATCH  /management/tasks/<id>/    -> faqat OWNER/PM (title/desc/dates/assignees/status o'zgartirishi mumkin)
    DELETE /management/tasks/<id>/    -> faqat OWNER/PM
    """
    queryset = (
        Task.objects
        .select_related("sprint", "sprint__project")
        .prefetch_related("assignees")
    )
    serializer_class = TaskSerializer

    def get_permissions(self):
        if self.request.method in ("PATCH", "PUT", "DELETE"):
            return [IsOwnerOrPM()]
        return [IsAuthenticated()]

    def get_object(self):
        obj: Task = super().get_object()
        user: User = self.request.user
        # Developer: faqat o'ziga assign qilingan task detailini ko'ra oladi
        if user.role == User.Role.DEV and not obj.assignees.filter(id=user.id).exists():
            raise PermissionDenied("You cannot access tasks not assigned to you.")
        return obj

class MyTasksAPIView(generics.ListAPIView):
    """
    GET /management/tasks/my/
    -> current user (request.user) ga assign qilingan tasklar ro'yxati
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Task.objects
            .filter(assignees=self.request.user)
            .select_related("sprint", "sprint__project")
            .prefetch_related("assignees")
        )

class TaskStatusUpdateAPIView(APIView):
    """
    PATCH /management/tasks/<id>/change-status/

    Body:
    {
      "status": "IN_PROGRESS"
    }
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        task: Task = get_object_or_404(Task, pk=pk)
        user: User = request.user
        new_status = request.data.get("status")

        if not new_status:
            raise ValidationError({"status": "This field is required."})

        # ==== Developer qoidalari ====
        if user.role == User.Role.DEV:
            # Task shu devga assign qilinganmi?
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

            current = task.status

            if current == Task.Status.TO_DO and new_status != Task.Status.IN_PROGRESS:
                raise ValidationError({"status": "From TO_DO only IN_PROGRESS is allowed."})

            if current == Task.Status.IN_PROGRESS and new_status != Task.Status.QA_TESTING:
                raise ValidationError({"status": "From IN_PROGRESS only QA_TESTING is allowed."})

            if current == Task.Status.QA_TESTING and new_status != Task.Status.PM_REVIEW:
                raise ValidationError({"status": "From QA_TESTING only PM_REVIEW is allowed."})

            if current == Task.Status.PM_REVIEW:
                raise ValidationError({"status": "Developer cannot change status from PM_REVIEW."})

        # ==== PM / OWNER qoidalari ====
        elif user.role in (User.Role.PM, User.Role.OWNER):
            if new_status not in Task.Status.values:
                raise ValidationError({"status": "Invalid status value."})

        # ==== Viewer (va boshqalar) - umuman ruxsat yo'q ====
        else:
            raise PermissionDenied("You are not allowed to change task status.")

        # Hammasi joyida bo'lsa - statusni update qilamiz
        task.status = new_status
        task.save(update_fields=["status", "updated_at"])

        serializer = TaskSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)
