from __future__ import annotations

import logging

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def exception_handler(exc, context):
    """
    Ensure API errors return a consistent payload with optional debug details.
    """

    response = drf_exception_handler(exc, context)
    include_debug = bool(getattr(settings, "API_DEBUG_ERRORS", False) or settings.DEBUG)

    if response is not None:
        if include_debug:
            if isinstance(response.data, dict):
                response.data.setdefault("error", str(exc))
                response.data.setdefault("error_type", exc.__class__.__name__)
            else:
                response.data = {
                    "detail": response.data,
                    "error": str(exc),
                    "error_type": exc.__class__.__name__,
                }
        return response

    logger.exception("Unhandled API exception", exc_info=exc)
    payload = {"detail": "Internal server error."}
    if include_debug:
        payload["error"] = str(exc)
        payload["error_type"] = exc.__class__.__name__
    return Response(payload, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
