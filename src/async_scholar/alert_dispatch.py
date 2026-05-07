"""Dependency-free alert dispatch boundary."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Literal, NotRequired, TypedDict, cast

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
    "unsupported_platform",
    "command_failed",
    "command_failure",
    "timeout",
    "os_error",
    "network_error",
    "http_error",
    "missing_credentials",
]
AlertProviderDispatcher = Callable[[AlertNotificationPayload], object]
AlertProviderStatus = AlertDispatchStatus | Literal["unsupported"]
AlertRetryAction = Literal["retry", "manual_check"]


class AlertDispatchResult(TypedDict):
    """Sanitized per-provider dispatch result."""

    provider: str
    severity: AlertSeverity
    status: AlertDispatchStatus
    requires_confirmation: bool
    error_kind: NotRequired[AlertDispatchErrorKind]


class AlertRetryLogDecision(TypedDict):
    """Sanitized JSON-ready retry log decision for an urgent dispatch issue."""

    provider: str
    severity: AlertSeverity
    status: AlertDispatchStatus
    requires_confirmation: bool
    retry_action: AlertRetryAction
    max_attempts: int
    error_kind: NotRequired[AlertDispatchErrorKind]


_ALLOWED_ERROR_KINDS: frozenset[AlertDispatchErrorKind] = frozenset(
    {
        "missing_dispatcher",
        "provider_error",
        "unsupported_provider",
        "unsupported_platform",
        "command_failed",
        "command_failure",
        "timeout",
        "os_error",
        "network_error",
        "http_error",
        "missing_credentials",
    }
)
_ALLOWED_STATUSES: frozenset[AlertProviderStatus] = frozenset(
    {"sent", "skipped", "failed", "unsupported"}
)
_RETRYABLE_ERROR_KINDS: frozenset[AlertDispatchErrorKind] = frozenset(
    {
        "provider_error",
        "timeout",
        "network_error",
        "http_error",
        "command_failed",
        "command_failure",
        "os_error",
    }
)
_URGENT_ALERT_RETRY_MAX_ATTEMPTS = 3
_FIELD_READ_ERROR = object()
_MISSING = object()


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


def build_urgent_alert_retry_log_decisions(
    results: Sequence[AlertDispatchResult],
    *,
    max_attempts: int = _URGENT_ALERT_RETRY_MAX_ATTEMPTS,
) -> list[AlertRetryLogDecision]:
    """Build sanitized retry log decisions without performing retry work."""

    decisions: list[AlertRetryLogDecision] = []
    for result in results:
        if result["severity"] != "urgent" or result["status"] not in {
            "failed",
            "skipped",
        }:
            continue

        error_kind = result.get("error_kind")
        retry_action = _classify_alert_retry_action(error_kind)
        decision: AlertRetryLogDecision = {
            "provider": result["provider"],
            "severity": result["severity"],
            "status": result["status"],
            "requires_confirmation": result["requires_confirmation"],
            "retry_action": retry_action,
            "max_attempts": max_attempts if retry_action == "retry" else 0,
        }
        if error_kind is not None:
            decision["error_kind"] = error_kind
        decisions.append(decision)

    return decisions


def _classify_alert_retry_action(
    error_kind: AlertDispatchErrorKind | None,
) -> AlertRetryAction:
    if error_kind in _RETRYABLE_ERROR_KINDS:
        return "retry"
    return "manual_check"


def _normalize_provider_result(
    *,
    provider: str,
    severity: AlertSeverity,
    provider_result: object,
) -> AlertDispatchResult:
    status_raw = _read_provider_result_field(
        provider_result,
        field_name="status",
        default="sent",
    )
    if status_raw is _FIELD_READ_ERROR:
        return _build_result(
            provider=provider,
            severity=severity,
            status="failed",
            error_kind="provider_error",
        )

    status = _normalize_status(status_raw)
    if status is None:
        return _build_result(
            provider=provider,
            severity=severity,
            status="failed",
            error_kind="provider_error",
        )

    error_kind_raw = _read_provider_result_field(
        provider_result,
        field_name="error_kind",
        default=_MISSING,
    )
    if error_kind_raw is _FIELD_READ_ERROR:
        return _build_result(
            provider=provider,
            severity=severity,
            status="failed",
            error_kind="provider_error",
        )

    error_kind, is_allowed_error_kind = _normalize_error_kind(error_kind_raw)
    if not is_allowed_error_kind:
        return _build_result(
            provider=provider,
            severity=severity,
            status="failed",
            error_kind="provider_error",
        )

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
            error_kind=error_kind or "unsupported_provider",
        )

    return _build_result(
        provider=provider,
        severity=severity,
        status="failed",
        error_kind="provider_error",
    )


def _read_provider_result_field(
    provider_result: object,
    *,
    field_name: str,
    default: object,
) -> object:
    try:
        if isinstance(provider_result, Mapping):
            return provider_result.get(field_name, default)
        return getattr(provider_result, field_name, default)
    except Exception:
        return _FIELD_READ_ERROR


def _normalize_status(status: object) -> AlertProviderStatus | None:
    if isinstance(status, str) and status in _ALLOWED_STATUSES:
        return cast(AlertProviderStatus, status)
    return None


def _normalize_error_kind(
    error_kind: object,
) -> tuple[AlertDispatchErrorKind | None, bool]:
    if error_kind is _MISSING or error_kind is None:
        return None, True
    if isinstance(error_kind, str) and error_kind in _ALLOWED_ERROR_KINDS:
        return cast(AlertDispatchErrorKind, error_kind), True
    return None, False


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
