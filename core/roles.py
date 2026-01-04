from __future__ import annotations

from typing import Iterable


def user_roles(user) -> set[str]:
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    roles: set[str] = set()
    if getattr(user, "is_superuser", False):
        roles.add("admin")
    profile = getattr(user, "profile", None)
    profile_roles: Iterable[str] = []
    if profile is not None and getattr(profile, "roles", None):
        profile_roles = profile.roles
    roles |= {str(r).lower() for r in profile_roles}
    return roles


def has_role(user, role: str) -> bool:
    """
    Role check where `admin` implies all roles.
    """
    role = role.lower()
    if role == "employee":
        return True
    roles = user_roles(user)
    return role in roles or "admin" in roles


def has_role_strict(user, role: str) -> bool:
    """
    Role check where `admin` does NOT imply other roles.
    """
    role = role.lower()
    if role == "employee":
        return True
    roles = user_roles(user)
    return role in roles
