from __future__ import annotations

from typing import NoReturn

GATE_D_LOCAL_EVIDENCE_BUNDLE_ERROR = "gate d local evidence bundle could not be built"

_BUNDLE_KIND = "local_gate_d_smoke_evidence_bundle"
_STATUS_SATISFACTORY = "satisfactory"
_STATUS_MISSING = "missing"
_READY_FALSE = False
_READINESS_DECISION = "blocked"
_READINESS_REASON = "required_gate_d_readiness_evidence_missing_or_blocking"
_GAP_DECISION = "gaps_present"
_GAP_REASON = "required_gate_d_evidence_gaps_present"
_MISSING_EVIDENCE = [
    "mic_diagnostics_after_reboot",
    "security_review",
    "rollback_plan_for_loopback_playwright_spike",
    "signal_quality_evidence",
    "scheduler_lifecycle_evidence",
    "product_judgment_evidence",
]
_FIXED_STATUSES = {
    "mic_diagnostics_after_reboot": _STATUS_MISSING,
    "security_review": _STATUS_MISSING,
    "rollback_plan_for_loopback_playwright_spike": _STATUS_MISSING,
    "signal_quality_evidence": _STATUS_MISSING,
    "scheduler_lifecycle_evidence": _STATUS_MISSING,
    "product_judgment_evidence": _STATUS_MISSING,
}
_READINESS_KEYS = (
    "readiness_kind",
    "mic_diagnostics_after_reboot_status",
    "alert_routing_status",
    "security_review_status",
    "policy_gate_tests_status",
    "rollback_plan_for_loopback_playwright_spike_status",
    "signal_quality_evidence_status",
    "scheduler_lifecycle_evidence_status",
    "delivery_path_evidence_status",
    "monitoring_boundary_evidence_status",
    "product_judgment_evidence_status",
    "ready_for_gate_review",
    "decision",
    "reason",
)
_GAP_KEYS = (
    "summary_kind",
    "mic_diagnostics_after_reboot_status",
    "alert_routing_status",
    "security_review_status",
    "policy_gate_tests_status",
    "rollback_plan_for_loopback_playwright_spike_status",
    "signal_quality_evidence_status",
    "scheduler_lifecycle_evidence_status",
    "delivery_path_evidence_status",
    "monitoring_boundary_evidence_status",
    "product_judgment_evidence_status",
    "missing_evidence",
    "missing_evidence_count",
    "blocking_evidence",
    "blocking_evidence_count",
    "satisfactory_evidence_count",
    "decision",
    "reason",
)


def build_local_gate_d_smoke_evidence_bundle() -> dict[str, object]:
    try:
        from async_scholar.alert_routing_smoke import build_local_alert_routing_smoke
        from async_scholar.delivery_path_smoke import build_local_delivery_path_smoke
        from async_scholar.gate_d_readiness import (
            build_gate_d_evidence_gap_summary,
            build_gate_d_readiness_report,
        )
        from async_scholar.monitoring_boundary_smoke import (
            build_local_monitoring_boundary_smoke,
        )
        from async_scholar.policy_gate_smoke import build_local_policy_gate_smoke

        alert_routing_status = _alert_routing_status(
            build_local_alert_routing_smoke("attendance_prompt")
        )
        policy_gate_tests_status = _policy_gate_tests_status(
            build_local_policy_gate_smoke()
        )
        delivery_path_evidence_status = _delivery_path_evidence_status(
            build_local_delivery_path_smoke()
        )
        monitoring_boundary_evidence_status = _monitoring_boundary_evidence_status(
            build_local_monitoring_boundary_smoke()
        )
        statuses = {
            **_FIXED_STATUSES,
            "alert_routing": alert_routing_status,
            "policy_gate_tests": policy_gate_tests_status,
            "delivery_path_evidence": delivery_path_evidence_status,
            "monitoring_boundary_evidence": monitoring_boundary_evidence_status,
        }
        readiness_report = build_gate_d_readiness_report(**statuses)
        gap_summary = build_gate_d_evidence_gap_summary(**statuses)
        payload = _bundle_from_reports(readiness_report, gap_summary)
        return _safe_bundle(payload)
    except Exception:
        raise ValueError(GATE_D_LOCAL_EVIDENCE_BUNDLE_ERROR) from None


def _alert_routing_status(payload: object) -> str:
    if type(payload) is not dict:
        _fail()
    if (
        payload.get("smoke_kind") != "local_alert_routing"
        or payload.get("event_type_known") is not True
        or payload.get("requires_confirmation") is not True
        or payload.get("status") != "sent"
        or payload.get("decision") != "delivered"
    ):
        _fail()
    return _STATUS_SATISFACTORY


def _policy_gate_tests_status(payload: object) -> str:
    if type(payload) is not dict:
        _fail()
    if (
        payload.get("smoke_kind") != "local_policy_gate"
        or payload.get("policy_gate_tests_status") != _STATUS_SATISFACTORY
        or payload.get("declined_confirmation_blocks_authorization") is not True
    ):
        _fail()
    return _STATUS_SATISFACTORY


def _delivery_path_evidence_status(payload: object) -> str:
    if type(payload) is not dict:
        _fail()
    if (
        payload.get("smoke_kind") != "local_delivery_path"
        or payload.get("delivery_path_evidence_status") != _STATUS_SATISFACTORY
        or payload.get("live_delivery_performed") is not False
        or payload.get("network_performed") is not False
    ):
        _fail()
    return _STATUS_SATISFACTORY


def _monitoring_boundary_evidence_status(payload: object) -> str:
    if type(payload) is not dict:
        _fail()
    if (
        payload.get("smoke_kind") != "local_monitoring_boundary"
        or payload.get("monitoring_boundary_evidence_status") != _STATUS_SATISFACTORY
        or payload.get("real_online_monitoring_performed") is not False
        or payload.get("browser_automation_performed") is not False
        or payload.get("audio_capture_performed") is not False
    ):
        _fail()
    return _STATUS_SATISFACTORY


def _bundle_from_reports(
    readiness_report: object,
    gap_summary: object,
) -> dict[str, object]:
    readiness = _safe_readiness_report(readiness_report)
    gaps = _safe_gap_summary(gap_summary)
    return {
        "bundle_kind": _BUNDLE_KIND,
        "mic_diagnostics_after_reboot_status": readiness[
            "mic_diagnostics_after_reboot_status"
        ],
        "alert_routing_status": readiness["alert_routing_status"],
        "security_review_status": readiness["security_review_status"],
        "policy_gate_tests_status": readiness["policy_gate_tests_status"],
        "rollback_plan_for_loopback_playwright_spike_status": readiness[
            "rollback_plan_for_loopback_playwright_spike_status"
        ],
        "signal_quality_evidence_status": readiness["signal_quality_evidence_status"],
        "scheduler_lifecycle_evidence_status": readiness[
            "scheduler_lifecycle_evidence_status"
        ],
        "delivery_path_evidence_status": readiness["delivery_path_evidence_status"],
        "monitoring_boundary_evidence_status": readiness[
            "monitoring_boundary_evidence_status"
        ],
        "product_judgment_evidence_status": readiness[
            "product_judgment_evidence_status"
        ],
        "missing_evidence": gaps["missing_evidence"],
        "missing_evidence_count": gaps["missing_evidence_count"],
        "blocking_evidence": gaps["blocking_evidence"],
        "blocking_evidence_count": gaps["blocking_evidence_count"],
        "satisfactory_evidence_count": gaps["satisfactory_evidence_count"],
        "ready_for_gate_review": readiness["ready_for_gate_review"],
        "readiness_decision": readiness["decision"],
        "readiness_reason": readiness["reason"],
        "gap_decision": gaps["decision"],
        "gap_reason": gaps["reason"],
        "live_delivery_performed": False,
        "real_online_monitoring_performed": False,
        "browser_automation_performed": False,
        "audio_capture_performed": False,
        "scheduler_execution_performed": False,
        "gate_d_pass_claimed": False,
        "product_promise_alpha_pass_claimed": False,
    }


def _safe_readiness_report(payload: object) -> dict[str, object]:
    if type(payload) is not dict or tuple(payload) != _READINESS_KEYS:
        _fail()
    if (
        payload["readiness_kind"] != "gate_d_readiness"
        or payload["ready_for_gate_review"] is not _READY_FALSE
        or payload["decision"] != _READINESS_DECISION
        or payload["reason"] != _READINESS_REASON
    ):
        _fail()
    _validate_status_fields(payload)
    return payload


def _safe_gap_summary(payload: object) -> dict[str, object]:
    if type(payload) is not dict or tuple(payload) != _GAP_KEYS:
        _fail()
    if (
        payload["summary_kind"] != "gate_d_evidence_gap_summary"
        or payload["missing_evidence"] != _MISSING_EVIDENCE
        or payload["missing_evidence_count"] != 6
        or payload["blocking_evidence"] != []
        or payload["blocking_evidence_count"] != 0
        or payload["satisfactory_evidence_count"] != 4
        or payload["decision"] != _GAP_DECISION
        or payload["reason"] != _GAP_REASON
    ):
        _fail()
    _validate_status_fields(payload)
    return payload


def _validate_status_fields(payload: dict[str, object]) -> None:
    expected = {
        "mic_diagnostics_after_reboot_status": _STATUS_MISSING,
        "alert_routing_status": _STATUS_SATISFACTORY,
        "security_review_status": _STATUS_MISSING,
        "policy_gate_tests_status": _STATUS_SATISFACTORY,
        "rollback_plan_for_loopback_playwright_spike_status": _STATUS_MISSING,
        "signal_quality_evidence_status": _STATUS_MISSING,
        "scheduler_lifecycle_evidence_status": _STATUS_MISSING,
        "delivery_path_evidence_status": _STATUS_SATISFACTORY,
        "monitoring_boundary_evidence_status": _STATUS_SATISFACTORY,
        "product_judgment_evidence_status": _STATUS_MISSING,
    }
    for key, value in expected.items():
        if payload[key] != value:
            _fail()


def _safe_bundle(payload: object) -> dict[str, object]:
    if type(payload) is not dict:
        _fail()
    expected = {
        "bundle_kind": _BUNDLE_KIND,
        "mic_diagnostics_after_reboot_status": _STATUS_MISSING,
        "alert_routing_status": _STATUS_SATISFACTORY,
        "security_review_status": _STATUS_MISSING,
        "policy_gate_tests_status": _STATUS_SATISFACTORY,
        "rollback_plan_for_loopback_playwright_spike_status": _STATUS_MISSING,
        "signal_quality_evidence_status": _STATUS_MISSING,
        "scheduler_lifecycle_evidence_status": _STATUS_MISSING,
        "delivery_path_evidence_status": _STATUS_SATISFACTORY,
        "monitoring_boundary_evidence_status": _STATUS_SATISFACTORY,
        "product_judgment_evidence_status": _STATUS_MISSING,
        "missing_evidence": _MISSING_EVIDENCE,
        "missing_evidence_count": 6,
        "blocking_evidence": [],
        "blocking_evidence_count": 0,
        "satisfactory_evidence_count": 4,
        "ready_for_gate_review": False,
        "readiness_decision": _READINESS_DECISION,
        "readiness_reason": _READINESS_REASON,
        "gap_decision": _GAP_DECISION,
        "gap_reason": _GAP_REASON,
        "live_delivery_performed": False,
        "real_online_monitoring_performed": False,
        "browser_automation_performed": False,
        "audio_capture_performed": False,
        "scheduler_execution_performed": False,
        "gate_d_pass_claimed": False,
        "product_promise_alpha_pass_claimed": False,
    }
    if payload != expected or list(payload) != list(expected):
        _fail()
    return payload


def _fail() -> NoReturn:
    raise ValueError(GATE_D_LOCAL_EVIDENCE_BUNDLE_ERROR)


__all__ = [
    "GATE_D_LOCAL_EVIDENCE_BUNDLE_ERROR",
    "build_local_gate_d_smoke_evidence_bundle",
]
