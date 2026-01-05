from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from core.graph_mailer import GraphMailerConfigError, GraphMailerError, GraphMailerHttpError, send_html_email


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
        except GraphMailerConfigError as exc:
            raise CommandError(
                f"{exc}. Check GRAPH_TENANT_ID/GRAPH_CLIENT_ID/GRAPH_CLIENT_SECRET/GRAPH_SENDER in .env."
            ) from exc
        except GraphMailerHttpError as exc:
            if exc.status_code == 401:
                raise CommandError(
                    "Graph auth failed (401). Verify the client secret VALUE (not secret ID) and tenant/app IDs."
                ) from exc
            if exc.status_code == 403:
                raise CommandError(
                    "Graph access denied (403). Ensure Microsoft Graph application permission Mail.Send is granted "
                    "and admin consent is approved. Also verify GRAPH_SENDER is a valid mailbox in the tenant."
                ) from exc
            raise CommandError(str(exc)) from exc
        except GraphMailerError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Sent test email to {to_email}"))
