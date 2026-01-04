from __future__ import annotations

import time

from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.stdout.write("Waiting for database...")
        for _ in range(60):
            try:
                connections["default"].cursor()
                self.stdout.write(self.style.SUCCESS("Database is available."))
                return
            except OperationalError:
                time.sleep(1)
        raise OperationalError("Database not available after 60 seconds")

