from rest_framework.routers import DefaultRouter

from .views import ProjectViewSet, SprintViewSet, TaskViewSet

router = DefaultRouter()
router.register('projects', ProjectViewSet, basename='project')
router.register('sprints', SprintViewSet, basename='sprint')
router.register('tasks', TaskViewSet, basename='task')

urlpatterns = router.urls
