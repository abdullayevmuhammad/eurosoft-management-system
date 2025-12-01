from django.urls import path
from .views import (
    ProjectListCreateAPIView,
    ProjectDetailAPIView,
    SprintListCreateAPIView,
    SprintDetailAPIView,
    TaskListCreateAPIView,
    TaskDetailAPIView,
    MyTasksAPIView,
    TaskStatusUpdateAPIView,
)

urlpatterns = [
    path('projects/', ProjectListCreateAPIView.as_view(), name='project-list-create'),
    path('projects/<int:pk>/', ProjectDetailAPIView.as_view(), name='project-detail'),

    path('sprints/', SprintListCreateAPIView.as_view(), name='sprint-list-create'),
    path('sprints/<int:pk>/', SprintDetailAPIView.as_view(), name='sprint-detail'),

    path('tasks/', TaskListCreateAPIView.as_view(), name='task-list-create'),
    path('tasks/<int:pk>/', TaskDetailAPIView.as_view(), name='task-detail'),
    path('tasks/my/', MyTasksAPIView.as_view(), name='my-tasks'),
    path('tasks/<int:pk>/change-status/', TaskStatusUpdateAPIView.as_view(), name='task-change-status'),
]