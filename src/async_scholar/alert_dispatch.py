"""Dependency-free alert dispatch boundary."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Literal, NotRequired, TypedDict

from async_scholar.alerts import (
    AlertNotificationPayload,
    AlertSeverity,
    build_alert_notification_payload,
)
from async_scholar.schemas import LectureEvent

AlertDispatchStatus = Literal["sent", "skipped", "failed"]
AlertDispatchErrorKind = Literal[
    "missing_dispatcher",
    "provider_error",
    "unsupported_provider",
]
AlertProviderDispatcher = Callable[[AlertNotificationPayload], object]


class AlertDispatchResult(TypedDict):
    """Sanitized per-provider dispatch result."""

    provider: str
    severity: AlertSeverity
    status: AlertDispatchStatus
    requires_confirmation: bool
    error_kind: NotRequired[AlertDispatchErrorKind]


_ALLOWED_ERROR_KINDS: frozenset[AlertDispatchErrorKind] = frozenset(
    {"missing_dispatcher", "provider_error", "unsupported_provider"}
)


def dispatch_alert(
    event: LectureEvent,
    provider_names: Sequence[str],
    dispatchers: Mapping[str, AlertProviderDispatcher],
) -> list[AlertDispatchResult]:
    """Dispatch an alert through injected providers and sanitize results."""

    payload = build_alert_notification_payload(event.event_type)
    severity = payload["severity"]

    results: list[AlertDispatchResult] = []
    for provider in provider_names:
        dispatcher = dispatchers.get(provider)
        if dispatcher is None:
            results.append(
                _build_result(
                    provider=provider,
                    severity=severity,
                    status="skipped",
                    error_kind="missing_dispatcher",
                )
            )
            continue

        try:
            provider_result = dispatcher(payload)
        except Exception:
            results.append(
                _build_result(
                    provider=provider,
                    severity=severity,
                    status="failed",
                    error_kind="provider_error",
                )
            )
            continue

        results.append(
            _normalize_provider_result(
                provider=provider,
                severity=severity,
                provider_result=provider_result,
            )
        )

    return results


def _normalize_provider_result(
    *,
    provider: str,
    severity: AlertSeverity,
    provider_result: object,
) -> AlertDispatchResult:
    if not isinstance(provider_result, Mapping):
        return _build_result(provider=provider, severity=severity, status="sent")

    status = provider_result.get("status", "sent")
    error_kind = _normalize_error_kind(provider_result.get("error_kind"))

    if status == "sent":
        return _build_result(provider=provider, severity=severity, status="sent")
    if status == "skipped":
        return _build_result(
            provider=provider,
            severity=severity,
            status="skipped",
            error_kind=error_kind,
        )
    if status == "failed":
        return _build_result(
            provider=provider,
            severity=severity,
            status="failed",
            error_kind=error_kind or "provider_error",
        )
    if status == "unsupported":
        return _build_result(
            provider=provider,
            severity=severity,
            status="skipped",
            error_kind="unsupported_provider",
        )

    return _build_result(
        provider=provider,
        severity=severity,
        status="failed",
        error_kind="unsupported_provider",
    )


def _normalize_error_kind(error_kind: object) -> AlertDispatchErrorKind | None:
    if isinstance(error_kind, str) and error_kind in _ALLOWED_ERROR_KINDS:
        return error_kind
    return None


def _build_result(
    *,
    provider: str,
    severity: AlertSeverity,
    status: AlertDispatchStatus,
    error_kind: AlertDispatchErrorKind | None = None,
) -> AlertDispatchResult:
    result: AlertDispatchResult = {
        "provider": provider,
        "severity": severity,
        "status": status,
        "requires_confirmation": True,
    }
    if error_kind is not None:
        result["error_kind"] = error_kind
    return result
