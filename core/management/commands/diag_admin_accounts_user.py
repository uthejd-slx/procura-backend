from __future__ import annotations

import os
import sys
import traceback

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.test import Client


class Command(BaseCommand):
    help = "Diagnose /admin/accounts/user/ errors (module paths, admin class, and a test request)."

    def handle(self, *args, **options):
        self.stdout.write("Python: " + sys.version.replace("\n", " "))
        self.stdout.write("CWD: " + os.getcwd())
        self.stdout.write("sys.path[0:5]:\n" + "\n".join(sys.path[:5]))

        try:
            import accounts  # noqa: F401
            import accounts.admin as accounts_admin

            self.stdout.write(f"accounts module: {getattr(sys.modules['accounts'], '__file__', None)}")
            self.stdout.write(f"accounts.admin module: {getattr(accounts_admin, '__file__', None)}")
            self.stdout.write(f"accounts.admin.UserAdmin mro: {accounts_admin.UserAdmin.__mro__}")
        except Exception:
            self.stdout.write("Failed to import accounts/admin:")
            self.stdout.write(traceback.format_exc())

        User = get_user_model()
        email = "diag-admin@example.com"
        User.objects.filter(email=email).delete()
        User.objects.create_superuser(email=email, password="Passw0rd!!", is_active=True)

        client = Client()
        ok = client.login(email=email, password="Passw0rd!!")
        self.stdout.write(f"client.login: {ok}")

        try:
            resp = client.get("/admin/accounts/user/", HTTP_HOST="localhost")
            self.stdout.write(f"GET /admin/accounts/user/ status: {resp.status_code}")
            if resp.status_code != 200:
                self.stdout.write(resp.content[:2000].decode("utf-8", errors="replace"))
        except Exception:
            self.stdout.write("Exception during GET /admin/accounts/user/:")
            self.stdout.write(traceback.format_exc())

