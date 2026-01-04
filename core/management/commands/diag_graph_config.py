from __future__ import annotations

import hashlib
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


def _hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


_GUID_RE = re.compile(r"^[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$")


class Command(BaseCommand):
    help = "Print sanitized Microsoft Graph configuration as seen by Django settings."

    def handle(self, *args, **options):
        base_dir = Path(getattr(settings, "BASE_DIR", Path.cwd()))
        env_path = base_dir / ".env"

        secret = getattr(settings, "GRAPH_CLIENT_SECRET", "") or ""
        sender = getattr(settings, "GRAPH_SENDER", "") or ""
        tenant = getattr(settings, "GRAPH_TENANT_ID", "") or ""
        client_id = getattr(settings, "GRAPH_CLIENT_ID", "") or ""

        self.stdout.write(f"backend/.env exists: {env_path.exists()} ({env_path})")
        self.stdout.write(f"GRAPH_TENANT_ID: {tenant}")
        self.stdout.write(f"GRAPH_CLIENT_ID: {client_id}")
        self.stdout.write(f"GRAPH_SENDER: {sender}")

        if not secret:
            self.stdout.write("GRAPH_CLIENT_SECRET: <EMPTY>")
        else:
            self.stdout.write(f"GRAPH_CLIENT_SECRET: <SET> len={len(secret)} sha256_12={_hash_secret(secret)}")
            self.stdout.write(f"GRAPH_CLIENT_SECRET looks_like_guid: {bool(_GUID_RE.match(secret))}")
            self.stdout.write(f"GRAPH_CLIENT_SECRET has_whitespace: {any(ch.isspace() for ch in secret)}")
            self.stdout.write(f"GRAPH_CLIENT_SECRET contains_hash: {'#' in secret}")

        self.stdout.write(f"GRAPH_TIMEOUT_SECONDS: {getattr(settings, 'GRAPH_TIMEOUT_SECONDS', None)}")
        self.stdout.write(f"GRAPH_MAX_RETRIES: {getattr(settings, 'GRAPH_MAX_RETRIES', None)}")
        self.stdout.write(f"GRAPH_RETRY_BACKOFF_SECONDS: {getattr(settings, 'GRAPH_RETRY_BACKOFF_SECONDS', None)}")
