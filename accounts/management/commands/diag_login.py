from __future__ import annotations

from django.contrib.auth import authenticate, get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Diagnose why a user can/can't login (checks existence, is_active, password, authenticate())."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)
        parser.add_argument("--password", required=True)

    def handle(self, *args, **options):
        email = options["email"]
        password = options["password"]

        User = get_user_model()
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            self.stdout.write("User: NOT FOUND")
            return

        self.stdout.write(f"User: FOUND id={user.pk} email={user.email}")
        self.stdout.write(f"is_active={user.is_active} is_staff={user.is_staff} is_superuser={user.is_superuser}")
        self.stdout.write(f"check_password={user.check_password(password)}")

        authed = authenticate(email=email, password=password)
        self.stdout.write(f"authenticate(email=..., password=...): {'OK' if authed else 'FAILED'}")

