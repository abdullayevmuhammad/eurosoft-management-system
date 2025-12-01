# accounts/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import MeView, UserListCreateAPIView, UserDetailAPIView

urlpatterns = [
    # JWT auth
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Current user info
    path('accounts/me/', MeView.as_view(), name='me'),

    # Ichki user boshqaruvi (OWNER, PM)
    path('accounts/users/', UserListCreateAPIView.as_view(), name='user-list-create'),
    path('accounts/users/<int:pk>/', UserDetailAPIView.as_view(), name='user-detail'),
]
