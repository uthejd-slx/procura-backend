from __future__ import annotations

from django.urls import path

from .views import (
    ActivateUserView,
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RegisterView,
    UserAdminUpdateView,
    UsersView,
)

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", CustomTokenObtainPairView.as_view(), name="auth-login"),
    path("auth/token/refresh/", CustomTokenRefreshView.as_view(), name="token-refresh"),
    path("auth/activate/", ActivateUserView.as_view(), name="auth-activate"),
    path("auth/password-reset/", PasswordResetRequestView.as_view(), name="auth-password-reset"),
    path("auth/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="auth-password-reset-confirm"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("users/", UsersView.as_view(), name="users"),
    path("admin/users/<int:user_id>/", UserAdminUpdateView.as_view(), name="admin-user-update"),
]
