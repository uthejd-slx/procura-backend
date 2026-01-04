from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass

import requests
from django.conf import settings
from django.core.cache import cache


class GraphMailerConfigError(RuntimeError):
    pass


class GraphMailerError(RuntimeError):
    pass


@dataclass(frozen=True)
class GraphMailerHttpError(GraphMailerError):
    status_code: int | None
    message: str

    def __str__(self) -> str:  # pragma: no cover
        if self.status_code is None:
            return self.message
        return f"HTTP {self.status_code}: {self.message}"


@dataclass(frozen=True)
class _Token:
    access_token: str
    expires_at: float


_RETRYABLE_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}

logger = logging.getLogger("core.graph_mailer")


def _session() -> requests.Session:
    sess = getattr(_session, "_sess", None)
    if sess is None:
        sess = requests.Session()
        _session._sess = sess  # type: ignore[attr-defined]
    return sess


def _parse_error_text(resp: requests.Response) -> str:
    text = resp.text or ""
    try:
        payload = resp.json()
    except Exception:
        return text[:500] or f"HTTP {resp.status_code}"

    if isinstance(payload, dict):
        if "error" in payload and isinstance(payload["error"], dict):
            err = payload["error"]
            code = err.get("code")
            message = err.get("message")
            if code and message:
                return f"{code}: {message}"
            if message:
                return str(message)[:500]
        if "error" in payload and "error_description" in payload:
            return f"{payload.get('error')}: {payload.get('error_description')}"[:500]

    return text[:500] or f"HTTP {resp.status_code}"


def _request_with_retry(method: str, url: str, **kwargs) -> requests.Response:
    max_retries = int(getattr(settings, "GRAPH_MAX_RETRIES", 3))
    backoff = float(getattr(settings, "GRAPH_RETRY_BACKOFF_SECONDS", 1.0))
    timeout = int(getattr(settings, "GRAPH_TIMEOUT_SECONDS", 30))
    kwargs.setdefault("timeout", timeout)

    last_exc: Exception | None = None
    for attempt in range(max_retries):
        try:
            logger.debug("HTTP %s %s attempt=%s timeout=%ss", method, url, attempt + 1, timeout)
            resp = _session().request(method, url, **kwargs)
            if resp.status_code in _RETRYABLE_STATUS_CODES and attempt < max_retries - 1:
                retry_after = resp.headers.get("Retry-After")
                sleep_for = None
                if retry_after:
                    try:
                        sleep_for = float(retry_after)
                    except Exception:
                        sleep_for = None
                logger.warning(
                    "HTTP %s %s retryable status=%s retry_after=%s attempt=%s/%s",
                    method,
                    url,
                    resp.status_code,
                    retry_after,
                    attempt + 1,
                    max_retries,
                )
                time.sleep(sleep_for if sleep_for is not None else backoff * (2**attempt))
                continue
            return resp
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < max_retries - 1:
                logger.warning(
                    "HTTP %s %s request error attempt=%s/%s: %s",
                    method,
                    url,
                    attempt + 1,
                    max_retries,
                    exc,
                )
                time.sleep(backoff * (2**attempt))
                continue
            raise

    raise last_exc or RuntimeError("Request failed")


def _require_settings() -> None:
    missing = [
        name
        for name in ("GRAPH_TENANT_ID", "GRAPH_CLIENT_ID", "GRAPH_CLIENT_SECRET", "GRAPH_SENDER")
        if not getattr(settings, name, "")
    ]
    if missing:
        raise GraphMailerConfigError(f"Missing Microsoft Graph settings: {', '.join(missing)}")


def _get_access_token() -> str:
    cached: _Token | None = cache.get("graph:access_token")
    if cached and cached.expires_at > time.time() + 30:
        logger.debug("Using cached Graph access token (expires_at=%s)", cached.expires_at)
        return cached.access_token

    _require_settings()
    logger.info(
        "Requesting Graph access token tenant=%s client_id=%s",
        settings.GRAPH_TENANT_ID,
        settings.GRAPH_CLIENT_ID,
    )
    url = f"https://login.microsoftonline.com/{settings.GRAPH_TENANT_ID}/oauth2/v2.0/token"
    data = {
        "client_id": settings.GRAPH_CLIENT_ID,
        "client_secret": settings.GRAPH_CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "https://graph.microsoft.com/.default",
    }
    try:
        resp = _request_with_retry("POST", url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        if resp.status_code >= 400:
            logger.error("Token request failed status=%s body=%s", resp.status_code, _parse_error_text(resp))
            raise GraphMailerHttpError(resp.status_code, _parse_error_text(resp))
    except requests.RequestException as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        body = getattr(getattr(exc, "response", None), "text", "") or ""
        logger.error("Token request exception status=%s error=%s", status, (body[:500] or str(exc)))
        raise GraphMailerHttpError(status, (body[:500] or str(exc))) from exc
    payload = resp.json()
    token = _Token(
        access_token=payload["access_token"],
        expires_at=time.time() + int(payload.get("expires_in", 3599)),
    )
    cache.set("graph:access_token", token, timeout=max(1, int(payload.get("expires_in", 3599)) - 30))
    logger.info("Graph access token obtained expires_in=%ss", int(payload.get("expires_in", 3599)))
    return token.access_token


def send_html_email(*, to_email: str, subject: str, html_body: str) -> None:
    token = _get_access_token()
    url = f"https://graph.microsoft.com/v1.0/users/{settings.GRAPH_SENDER}/sendMail"
    client_request_id = str(uuid.uuid4())
    payload = {
        "message": {
            "subject": subject,
            "body": {"contentType": "HTML", "content": html_body},
            "toRecipients": [{"emailAddress": {"address": to_email}}],
        },
        "saveToSentItems": bool(getattr(settings, "GRAPH_SAVE_TO_SENT_ITEMS", False)),
    }
    logger.info(
        "Sending Graph email sender=%s to=%s subject=%s client_request_id=%s",
        settings.GRAPH_SENDER,
        to_email,
        subject,
        client_request_id,
    )
    try:
        resp = _request_with_retry(
            "POST",
            url,
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "client-request-id": client_request_id,
                "return-client-request-id": "true",
            },
        )
        if resp.status_code >= 400:
            logger.error(
                "sendMail failed status=%s request_id=%s client_request_id=%s body=%s",
                resp.status_code,
                resp.headers.get("request-id"),
                resp.headers.get("client-request-id"),
                _parse_error_text(resp),
            )
            raise GraphMailerHttpError(resp.status_code, _parse_error_text(resp))
        logger.info(
            "sendMail success status=%s request_id=%s client_request_id=%s",
            resp.status_code,
            resp.headers.get("request-id"),
            resp.headers.get("client-request-id"),
        )
    except requests.RequestException as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        body = getattr(getattr(exc, "response", None), "text", "") or ""
        logger.error(
            "sendMail exception status=%s client_request_id=%s error=%s",
            status,
            client_request_id,
            (body[:500] or str(exc)),
        )
        raise GraphMailerHttpError(status, (body[:500] or str(exc))) from exc
