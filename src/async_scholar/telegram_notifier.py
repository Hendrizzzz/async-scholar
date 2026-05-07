"""Telegram alert notification adapter."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from typing import Any, TypedDict
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from .alerts import build_alert_notification_payload

_TELEGRAM_API_BASE = "https://api.telegram.org"
_TELEGRAM_SEND_MESSAGE_PATH = "sendMessage"
_DEFAULT_TIMEOUT_SECONDS = 10.0
_PROVIDER_NAME = "telegram"

__all__ = [
    "TelegramNotificationResult",
    "dispatch_telegram_alert_notification",
    "send_telegram_alert_notification",
]


class TelegramNotificationResult(TypedDict, total=False):
    """Sanitized delivery result for Telegram notifications."""

    ok: bool
    status: str
    provider: str
    severity: str
    title: str
    body: str
    requires_confirmation: bool
    http_status: int
    error_kind: str
    missing_fields: list[str]


def dispatch_telegram_alert_notification(
    event_type: str,
    *,
    bot_token: str | None,
    chat_id: str | int | None,
    opener: Callable[..., Any] | None = None,
    timeout: float | None = _DEFAULT_TIMEOUT_SECONDS,
) -> TelegramNotificationResult:
    """Send a Telegram alert message using a sanitized payload."""

    return send_telegram_alert_notification(
        event_type,
        bot_token=bot_token,
        chat_id=chat_id,
        opener=opener,
        timeout=timeout,
    )


def send_telegram_alert_notification(
    event_type: str,
    *,
    bot_token: str | None,
    chat_id: str | int | None,
    opener: Callable[..., Any] | None = None,
    timeout: float | None = _DEFAULT_TIMEOUT_SECONDS,
) -> TelegramNotificationResult:
    """Deliver a Telegram alert notification without leaking private data."""

    payload = build_alert_notification_payload(event_type)
    payload_result = _payload_result_fields(payload)

    missing_fields = _missing_fields(bot_token, chat_id)
    if missing_fields:
        return {
            **payload_result,
            "ok": False,
            "status": "failed",
            "error_kind": "missing_credentials",
            "missing_fields": missing_fields,
        }

    normalized_bot_token = bot_token.strip()
    normalized_chat_id = _normalize_chat_id(chat_id)
    request = _build_request(normalized_bot_token, normalized_chat_id, payload)
    transport = opener or urlopen

    try:
        response = transport(request, timeout=timeout)
    except HTTPError as error:
        _close_response(error)
        return _failure_result(
            payload_result,
            error_kind="http_error",
            http_status=_http_status_from_error(error),
        )
    except URLError as error:
        return _failure_result(
            payload_result,
            error_kind=_url_error_kind(error),
        )
    except TimeoutError:
        return _failure_result(payload_result, error_kind="timeout")
    except OSError:
        return _failure_result(payload_result, error_kind="network_error")

    http_status = _response_status(response)
    _close_response(response)

    if http_status is not None and http_status >= 400:
        return _failure_result(
            payload_result,
            error_kind="http_error",
            http_status=http_status,
        )

    result: TelegramNotificationResult = {
        **payload_result,
        "ok": True,
        "status": "sent",
    }
    if http_status is not None:
        result["http_status"] = http_status
    return result


def _payload_result_fields(payload: dict[str, Any]) -> TelegramNotificationResult:
    return {
        "provider": _PROVIDER_NAME,
        "severity": str(payload["severity"]),
        "title": str(payload["title"]),
        "body": str(payload["body"]),
        "requires_confirmation": bool(payload["requires_confirmation"]),
    }


def _failure_result(
    payload_result: TelegramNotificationResult,
    *,
    error_kind: str,
    http_status: int | None = None,
    missing_fields: list[str] | None = None,
) -> TelegramNotificationResult:
    result: TelegramNotificationResult = {
        **payload_result,
        "ok": False,
        "status": "failed",
        "error_kind": error_kind,
    }
    if http_status is not None:
        result["http_status"] = http_status
    if missing_fields is not None:
        result["missing_fields"] = missing_fields
    return result


def _missing_fields(
    bot_token: str | None,
    chat_id: str | int | None,
) -> list[str]:
    missing: list[str] = []
    if not isinstance(bot_token, str) or not bot_token.strip():
        missing.append("bot_token")
    if chat_id is None or (isinstance(chat_id, str) and not chat_id.strip()):
        missing.append("chat_id")
    return missing


def _normalize_chat_id(chat_id: str | int | None) -> str:
    if isinstance(chat_id, str):
        return chat_id.strip()
    return str(chat_id)


def _build_request(
    bot_token: str,
    chat_id: str,
    payload: dict[str, Any],
) -> Request:
    url = (
        f"{_TELEGRAM_API_BASE}/bot{quote(bot_token, safe=':')}/"
        f"{_TELEGRAM_SEND_MESSAGE_PATH}"
    )
    body_text = f"{payload['severity']} | {payload['title']} | {payload['body']}"
    body = urlencode({"chat_id": chat_id, "text": body_text}).encode("utf-8")
    headers = {"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"}
    return Request(url, data=body, headers=headers, method="POST")


def _response_status(response: Any) -> int | None:
    status = getattr(response, "status", None)
    if isinstance(status, int):
        return status

    code = getattr(response, "code", None)
    if isinstance(code, int):
        return code

    getcode = getattr(response, "getcode", None)
    if callable(getcode):
        code = getcode()
        if isinstance(code, int):
            return code

    return None


def _http_status_from_error(error: HTTPError) -> int | None:
    code = getattr(error, "code", None)
    if isinstance(code, int):
        return code
    return None


def _url_error_kind(error: URLError) -> str:
    reason = getattr(error, "reason", None)
    if isinstance(reason, TimeoutError):
        return "timeout"
    if isinstance(reason, OSError):
        return "network_error"
    return "network_error"


def _close_response(response: Any) -> None:
    close = getattr(response, "close", None)
    if callable(close):
        with suppress(Exception):
            close()
