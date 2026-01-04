from __future__ import annotations

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _
from django.utils.encoding import force_bytes
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from core.graph_mailer import GraphMailerConfigError, GraphMailerError, send_html_email

from .permissions import IsAdminRole
from .serializers import (
    CustomTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserAdminUpdateSerializer,
    UserListSerializer,
    UserSerializer,
)
from .tokens import activation_token_generator


User = get_user_model()
logger = logging.getLogger(__name__)


def _build_url(path: str, *, query: dict[str, str]) -> str:
    base = settings.BACKEND_BASE_URL
    url = f"{base}{path}"
    if not query:
        return url
    parts = [f"{k}={v}" for k, v in query.items()]
    return f"{url}?{'&'.join(parts)}"


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        print(request.data)
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = activation_token_generator.make_token(user)
        if settings.FRONTEND_BASE_URL:
            activation_link = f"{settings.FRONTEND_BASE_URL}/activate?uid={uid}&token={token}"
        else:
            activation_link = _build_url("/api/auth/activate/", query={"uid": uid, "token": token})

        subject = "Activate your account"
        html = f"""
        <p>Welcome!</p>
        <p>Activate your account by clicking the link below:</p>
        <p><a href="{activation_link}">Activate account</a></p>
        """
        debug_payload: dict[str, str] = {}
        mail_sent = True
        try:
            send_html_email(to_email=user.email, subject=subject, html_body=html)
        except (GraphMailerConfigError, GraphMailerError) as exc:
            mail_sent = False
            if settings.DEBUG:
                debug_payload = {"activation_link": activation_link, "mail_error": str(exc)}
            else:
                logger.warning("Activation email failed for user_id=%s email=%s error=%s", user.id, user.email, exc)

        return Response(
            {
                "user": UserSerializer(user).data,
                "detail": _("Registration successful. Check email to activate."),
                "mail_sent": mail_sent,
                **debug_payload,
            },
            status=status.HTTP_201_CREATED,
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]


class ActivateUserView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        uid = request.query_params.get("uid", "")
        token = request.query_params.get("token", "")
        return self._activate(uid=uid, token=token)

    def post(self, request):
        uid = request.data.get("uid", "")
        token = request.data.get("token", "")
        return self._activate(uid=uid, token=token)

    def _activate(self, *, uid: str, token: str):
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except Exception:
            return Response({"detail": _("Invalid activation link.")}, status=status.HTTP_400_BAD_REQUEST)

        if activation_token_generator.check_token(user, token):
            user.is_active = True
            user.save(update_fields=["is_active"])
            return Response({"detail": _("Account activated.")}, status=status.HTTP_200_OK)
        return Response({"detail": _("Invalid activation link.")}, status=status.HTTP_400_BAD_REQUEST)


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UsersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = User.objects.all().order_by("email")
        return Response(UserListSerializer(qs, many=True).data, status=status.HTTP_200_OK)


class UserAdminUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def patch(self, request, user_id: int):
        user = User.objects.filter(id=user_id).select_related("profile").first()
        if not user:
            return Response({"detail": _("User not found.")}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserAdminUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        if "is_active" in payload:
            user.is_active = payload["is_active"]
            user.save(update_fields=["is_active"])

        if "roles" in payload:
            profile = getattr(user, "profile", None)
            if profile is None:
                return Response({"detail": _("Profile missing for user.")}, status=status.HTTP_400_BAD_REQUEST)
            profile.roles = payload["roles"]
            profile.save(update_fields=["roles"])

        user.refresh_from_db()
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.filter(email__iexact=email).first()

        debug_payload: dict[str, str] = {}
        if user and user.is_active:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            if settings.FRONTEND_BASE_URL:
                reset_link = f"{settings.FRONTEND_BASE_URL}/reset-password/confirm?uid={uid}&token={token}"
            else:
                reset_link = _build_url("/api/auth/password-reset/confirm/", query={"uid": uid, "token": token})

            subject = "Password reset"
            html = f"""
            <p>Reset your password using the link below:</p>
            <p><a href="{reset_link}">Reset password</a></p>
            """
            try:
                send_html_email(to_email=user.email, subject=subject, html_body=html)
            except (GraphMailerConfigError, GraphMailerError) as exc:
                if settings.DEBUG:
                    debug_payload = {"reset_link": reset_link, "mail_error": str(exc)}
                else:
                    debug_payload = {}

        return Response(
            {"detail": _("If the email exists, a reset link has been sent."), **debug_payload},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        uid = request.query_params.get("uid", "")
        token = request.query_params.get("token", "")
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except Exception:
            return Response({"detail": _("Invalid reset link.")}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"detail": _("Invalid reset link.")}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": _("Reset link is valid."), "uid": uid, "token": token}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except Exception:
            return Response({"detail": _("Invalid reset link.")}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"detail": _("Invalid reset link.")}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=["password"])
        return Response({"detail": _("Password updated.")}, status=status.HTTP_200_OK)
