from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from core.graph_mailer import GraphMailerConfigError, GraphMailerError, send_html_email


class Command(BaseCommand):
    help = "Send a test email using Microsoft Graph (client credentials)."

    def add_arguments(self, parser):
        parser.add_argument("--to", required=True, help="Recipient email address")

    def handle(self, *args, **options):
        to_email = options["to"]
        subject = "Procurement Tool - Microsoft Graph test"
        html = "<p>This is a test email sent via Microsoft Graph.</p>"
        try:
            send_html_email(to_email=to_email, subject=subject, html_body=html)
        except (GraphMailerConfigError, GraphMailerError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Sent test email to {to_email}"))

