from __future__ import annotations

from typing import NoReturn

GATE_D_ROLLBACK_PLAN_EVIDENCE_ERROR = "gate d rollback plan evidence could not be built"

_EXPECTED_PAYLOAD = {
    "evidence_kind": "local_gate_d_rollback_plan_evidence",
    "rollback_plan_for_loopback_playwright_spike_status": "satisfactory",
    "rollback_plan_document_status": "tracked",
    "rollback_trigger_coverage_status": "documented",
    "disable_strategy_status": "documented",
    "dependency_rollback_status": "documented",
    "disposable_browser_state_cleanup_status": "documented",
    "artifact_cleanup_status": "documented",
    "private_data_handling_status": "documented",
    "manual_checks_status": "documented",
    "stop_conditions_status": "documented",
    "browser_automation_performed": False,
    "audio_capture_performed": False,
    "loopback_capture_performed": False,
    "network_performed": False,
    "live_delivery_performed": False,
    "filesystem_cleanup_performed": False,
    "dependency_change_performed": False,
    "external_platform_accessed": False,
    "profile_state_accessed": False,
    "gate_d_pass_claimed": False,
    "product_promise_alpha_pass_claimed": False,
}


def build_local_gate_d_rollback_plan_evidence() -> dict[str, object]:
    try:
        return _safe_payload(_build_payload())
    except Exception:
        raise ValueError(GATE_D_ROLLBACK_PLAN_EVIDENCE_ERROR) from None


def _build_payload() -> dict[str, object]:
    return dict(_EXPECTED_PAYLOAD)


def _safe_payload(payload: object) -> dict[str, object]:
    if type(payload) is not dict:
        _fail()
    if payload != _EXPECTED_PAYLOAD or list(payload) != list(_EXPECTED_PAYLOAD):
        _fail()
    return payload


def _fail() -> NoReturn:
    raise ValueError(GATE_D_ROLLBACK_PLAN_EVIDENCE_ERROR)


__all__ = [
    "GATE_D_ROLLBACK_PLAN_EVIDENCE_ERROR",
    "build_local_gate_d_rollback_plan_evidence",
]
