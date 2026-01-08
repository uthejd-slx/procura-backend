from __future__ import annotations

import logging

from django.conf import settings

from core.graph_mailer import GraphMailerConfigError, GraphMailerError, send_html_email

from .models import Notification


logger = logging.getLogger(__name__)

def notify_user(
    *,
    recipient,
    title: str,
    body: str = "",
    link: str = "",
    level: str = Notification.Level.INFO,
    send_email: bool | None = None,
) -> Notification:
    """
    Create an in-app notification, and optionally send an email.

    Email sending is best-effort and never blocks the request.
    """

    notification = Notification.objects.create(
        recipient=recipient,
        title=str(title)[:200],
        body=str(body or ""),
        link=str(link or "")[:500],
        level=level,
    )

    if send_email is None:
        send_email = getattr(settings, "NOTIFICATIONS_SEND_EMAIL", False)
        if send_email:
            profile = getattr(recipient, "profile", None)
            if profile is not None and not getattr(profile, "notifications_email_enabled", False):
                send_email = False

    if send_email:
        try:
            subject = title
            html = f"""
            <p>{body}</p>
            {"<p><a href='" + link + "'>Open</a></p>" if link else ""}
            """
            send_html_email(to_email=recipient.email, subject=subject, html_body=html)
        except (GraphMailerConfigError, GraphMailerError) as exc:
            logger.warning("Failed to send notification email: %s", exc)
        except Exception:
            logger.exception("Unexpected error sending notification email")

    return notification
