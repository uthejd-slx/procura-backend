from __future__ import annotations

from django.http import JsonResponse


def health(_request):
    return JsonResponse({"status": "ok"})

