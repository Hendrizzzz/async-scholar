"""Local in-process alert routing smoke helper."""

from __future__ import annotations

from typing import Literal, TypedDict

from async_scholar.alert_dispatch import AlertProviderDispatcher, dispatch_alert
from async_scholar.alerts import AlertSeverity, build_alert_notification_payload
from async_scholar.schemas import LectureEvent

LOCAL_ALERT_ROUTING_SMOKE_ERROR = "local alert routing smoke could not be built"

_LOCAL_PROVIDER = "local_console"
_SMOKE_KIND = "local_alert_routing"
_GENERIC_EVENT_TITLE = "Lecture alert: Lecture event"

LocalAlertRoutingSmokeDecision = Literal["delivered", "disabled", "failed", "skipped"]


class LocalAlertRoutingSmokeResult(TypedDict):
    smoke_kind: str
    provider: str
    event_type_known: bool
    severity: AlertSeverity
    status: str
    requires_confirmation: bool
    delivery_performed: bool
    error_kind: str
    decision: LocalAlertRoutingSmokeDecision
    reason: str


def build_local_alert_routing_smoke(
    event_type: str,
    *,
    disabled: bool = False,
    dispatcher: AlertProviderDispatcher | None = None,
) -> LocalAlertRoutingSmokeResult:
    """Route one fixed local alert through the injected dispatch boundary."""

    safe_event_type = _validate_event_type(event_type)
    payload = build_alert_notification_payload(safe_event_type)
    event_type_known = payload["title"] != _GENERIC_EVENT_TITLE

    if disabled:
        return _build_result(
            event_type_known=event_type_known,
            severity=payload["severity"],
            status="skipped",
            requires_confirmation=payload["requires_confirmation"],
            delivery_performed=False,
            error_kind="none",
            decision="disabled",
            reason="local_alert_routing_smoke_disabled",
        )

    dispatch_results = dispatch_alert(
        LectureEvent(
            event_id="local-alert-routing-smoke-event",
            session_id="local-alert-routing-smoke-session",
            event_type=safe_event_type,
            detected_at_seconds=0,
            source_segment_ids=("local-alert-routing-smoke-source",),
            message="Local alert routing smoke.",
        ),
        provider_names=(_LOCAL_PROVIDER,),
        dispatchers={_LOCAL_PROVIDER: dispatcher or _local_console_dispatcher},
    )
    if len(dispatch_results) != 1:
        raise ValueError(LOCAL_ALERT_ROUTING_SMOKE_ERROR)

    dispatch_result = dispatch_results[0]
    status = dispatch_result["status"]
    error_kind = dispatch_result.get("error_kind", "none")
    if status == "sent":
        decision: LocalAlertRoutingSmokeDecision = "delivered"
        reason = "local_console_dispatch_succeeded"
        delivery_performed = True
    elif status == "failed":
        decision = "failed"
        reason = "local_console_dispatch_failed"
        delivery_performed = False
    else:
        decision = "skipped"
        reason = "local_console_dispatch_skipped"
        delivery_performed = False

    return _build_result(
        event_type_known=event_type_known,
        severity=dispatch_result["severity"],
        status=status,
        requires_confirmation=dispatch_result["requires_confirmation"],
        delivery_performed=delivery_performed,
        error_kind=error_kind,
        decision=decision,
        reason=reason,
    )


def _local_console_dispatcher(payload: object) -> dict[str, str]:
    return {"status": "sent"}


def _validate_event_type(event_type: str) -> str:
    if not isinstance(event_type, str):
        raise ValueError(LOCAL_ALERT_ROUTING_SMOKE_ERROR)

    safe_event_type = event_type.strip()
    if not safe_event_type or any(
        _is_control_character(char) for char in safe_event_type
    ):
        raise ValueError(LOCAL_ALERT_ROUTING_SMOKE_ERROR)
    return safe_event_type


def _is_control_character(char: str) -> bool:
    return ord(char) < 32 or ord(char) == 127


def _build_result(
    *,
    event_type_known: bool,
    severity: AlertSeverity,
    status: str,
    requires_confirmation: bool,
    delivery_performed: bool,
    error_kind: str,
    decision: LocalAlertRoutingSmokeDecision,
    reason: str,
) -> LocalAlertRoutingSmokeResult:
    return {
        "decision": decision,
        "delivery_performed": delivery_performed,
        "error_kind": error_kind,
        "event_type_known": event_type_known,
        "provider": _LOCAL_PROVIDER,
        "reason": reason,
        "requires_confirmation": requires_confirmation,
        "severity": severity,
        "smoke_kind": _SMOKE_KIND,
        "status": status,
    }


__all__ = [
    "LOCAL_ALERT_ROUTING_SMOKE_ERROR",
    "LocalAlertRoutingSmokeResult",
    "build_local_alert_routing_smoke",
]
