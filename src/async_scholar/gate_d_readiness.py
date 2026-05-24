from __future__ import annotations

from typing import NoReturn

GATE_D_READINESS_ERROR = "gate d readiness could not be built"

GateDReadinessReport = dict[str, object]

_READINESS_KIND = "gate_d_readiness"
_STATUSES = frozenset(("satisfactory", "blocking", "missing"))
_READY_DECISION = "ready_for_gate_review"
_BLOCKED_DECISION = "blocked"
_READY_REASON = "all_required_gate_d_readiness_evidence_satisfactory"
_BLOCKED_REASON = "required_gate_d_readiness_evidence_missing_or_blocking"
_TEXT_MAX_LENGTH = 96
_REPORT_KEYS = (
    "readiness_kind",
    "mic_diagnostics_after_reboot_status",
    "alert_routing_status",
    "security_review_status",
    "policy_gate_tests_status",
    "rollback_plan_for_loopback_playwright_spike_status",
    "ready_for_gate_review",
    "decision",
    "reason",
)


def build_gate_d_readiness_report(
    *,
    mic_diagnostics_after_reboot: object,
    alert_routing: object,
    security_review: object,
    policy_gate_tests: object,
    rollback_plan_for_loopback_playwright_spike: object,
) -> GateDReadinessReport:
    try:
        statuses = {
            "mic_diagnostics_after_reboot_status": _status(
                mic_diagnostics_after_reboot
            ),
            "alert_routing_status": _status(alert_routing),
            "security_review_status": _status(security_review),
            "policy_gate_tests_status": _status(policy_gate_tests),
            "rollback_plan_for_loopback_playwright_spike_status": _status(
                rollback_plan_for_loopback_playwright_spike
            ),
        }
        ready = all(status == "satisfactory" for status in statuses.values())
        payload: dict[str, object] = {
            "readiness_kind": _READINESS_KIND,
            **statuses,
            "ready_for_gate_review": ready,
            "decision": _READY_DECISION if ready else _BLOCKED_DECISION,
            "reason": _READY_REASON if ready else _BLOCKED_REASON,
        }
        return _readiness_safe_summary(payload)
    except (KeyError, TypeError, ValueError):
        raise ValueError(GATE_D_READINESS_ERROR) from None


def _readiness_safe_summary(payload: dict[str, object]) -> dict[str, object]:
    if type(payload) is not dict or tuple(payload) != _REPORT_KEYS:
        _fail()
    report = {
        "readiness_kind": _exact_text(payload["readiness_kind"], _READINESS_KIND),
        "mic_diagnostics_after_reboot_status": _status(
            payload["mic_diagnostics_after_reboot_status"]
        ),
        "alert_routing_status": _status(payload["alert_routing_status"]),
        "security_review_status": _status(payload["security_review_status"]),
        "policy_gate_tests_status": _status(payload["policy_gate_tests_status"]),
        "rollback_plan_for_loopback_playwright_spike_status": _status(
            payload["rollback_plan_for_loopback_playwright_spike_status"]
        ),
        "ready_for_gate_review": _bool_value(payload["ready_for_gate_review"]),
        "decision": _decision(payload["decision"]),
        "reason": _reason(payload["reason"]),
    }
    statuses = (
        report["mic_diagnostics_after_reboot_status"],
        report["alert_routing_status"],
        report["security_review_status"],
        report["policy_gate_tests_status"],
        report["rollback_plan_for_loopback_playwright_spike_status"],
    )
    ready = all(status == "satisfactory" for status in statuses)
    if report["ready_for_gate_review"] is not ready:
        _fail()
    if ready:
        if report["decision"] != _READY_DECISION or report["reason"] != _READY_REASON:
            _fail()
    elif report["decision"] != _BLOCKED_DECISION or report["reason"] != _BLOCKED_REASON:
        _fail()
    return report


def _status(value: object) -> str:
    status = _required_text(value)
    if status not in _STATUSES:
        _fail()
    return status


def _decision(value: object) -> str:
    decision = _required_text(value)
    if decision not in {_READY_DECISION, _BLOCKED_DECISION}:
        _fail()
    return decision


def _reason(value: object) -> str:
    reason = _required_text(value)
    if reason not in {_READY_REASON, _BLOCKED_REASON}:
        _fail()
    return reason


def _exact_text(value: object, expected: str) -> str:
    text = _required_text(value)
    if text != expected:
        _fail()
    return text


def _required_text(value: object) -> str:
    if not isinstance(value, str):
        _fail()
    if (
        not value
        or value.strip() != value
        or len(value) > _TEXT_MAX_LENGTH
        or _has_control_character(value)
        or _has_forbidden_path_or_uri_shape(value)
    ):
        _fail()
    return value


def _bool_value(value: object) -> bool:
    if not isinstance(value, bool):
        _fail()
    return value


def _has_control_character(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _has_forbidden_path_or_uri_shape(value: str) -> bool:
    normalized_value = value.replace("/", "\\")
    lower_value = value.lower()
    return (
        "://" in lower_value
        or lower_value.startswith("file:")
        or normalized_value.startswith("\\\\")
        or "\\" in value
        or "/" in value
        or ":" in value
        or any(part == ".." for part in value.replace("\\", "/").split("/"))
    )


def _fail() -> NoReturn:
    raise ValueError(GATE_D_READINESS_ERROR)
