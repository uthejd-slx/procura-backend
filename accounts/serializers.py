from __future__ import annotations

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, password_validation
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from core.roles import user_roles

User = get_user_model()


def _normalize_and_validate_email(value: str) -> str:
    value = (value or "").strip()
    if "@" not in value or value.count("@") != 1:
        raise serializers.ValidationError(_("Enter a valid email address."))

    local, domain = value.split("@", 1)
    if not local or not domain:
        raise serializers.ValidationError(_("Enter a valid email address."))

    if "." not in domain and not getattr(settings, "ALLOW_NON_TLD_EMAILS", False):
        raise serializers.ValidationError(_("Enter a valid email address (e.g. name@domain.com)."))

    return User.objects.normalize_email(value)


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "is_active", "roles")
        read_only_fields = ("id", "is_active", "roles")

    def get_roles(self, obj):
        return sorted(user_roles(obj))


class UserListSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "is_active", "roles")
        read_only_fields = fields

    def get_roles(self, obj):
        return sorted(user_roles(obj))


class UserAdminUpdateSerializer(serializers.Serializer):
    is_active = serializers.BooleanField(required=False)
    roles = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)

    def validate_roles(self, value):
        normalized = []
        for r in value:
            r = str(r).strip().lower()
            if not r:
                continue
            normalized.append(r)
        allowed = {"employee", "approver", "procurement", "admin"}
        unknown = sorted(set(normalized) - allowed)
        if unknown:
            raise serializers.ValidationError(_(f"Unknown role(s): {', '.join(unknown)}"))
        # We don't store "employee" explicitly; it's implicit.
        normalized = [r for r in normalized if r != "employee"]
        return sorted(set(normalized))


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "email", "password", "first_name", "last_name")
        read_only_fields = ("id",)

    def validate_email(self, value: str) -> str:
        return _normalize_and_validate_email(value)

    def validate_password(self, value: str) -> str:
        password_validation.validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, is_active=False, **validated_data)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = attrs.get("email") or attrs.get(getattr(User, "USERNAME_FIELD", "email")) or attrs.get("username")
        password = attrs.get("password")
        if not email or password is None:
            raise AuthenticationFailed(_("No active account found with the given credentials"), code="no_active_account")

        email = _normalize_and_validate_email(email)
        user = User.objects.filter(email__iexact=email).first()
        if not user or not user.is_active or not user.check_password(password):
            raise AuthenticationFailed(_("No active account found with the given credentials"), code="no_active_account")

        refresh = self.get_token(user)
        data = {"refresh": str(refresh), "access": str(refresh.access_token)}
        data["user"] = UserSerializer(user).data
        return data


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.CharField()

    def validate_email(self, value: str) -> str:
        return _normalize_and_validate_email(value)


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value: str) -> str:
        password_validation.validate_password(value)
        return value


class LoginCheckSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value: str) -> str:
        return _normalize_and_validate_email(value)

    def validate(self, attrs):
        user = authenticate(email=attrs["email"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError(_("Invalid credentials."), code="authorization")
        if not user.is_active:
            raise serializers.ValidationError(_("Account is not activated."), code="authorization")
        attrs["user"] = user
        return attrs
