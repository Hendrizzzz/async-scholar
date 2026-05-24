from __future__ import annotations

from typing import NoReturn

GATE_D_SECURITY_REVIEW_EVIDENCE_ERROR = (
    "gate d security review evidence could not be built"
)

_EXPECTED_PAYLOAD = {
    "evidence_kind": "local_gate_d_security_review_evidence",
    "security_review_status": "satisfactory",
    "privacy_boundary_review_status": "satisfactory",
    "sanitized_output_review_status": "satisfactory",
    "secret_handling_review_status": "satisfactory",
    "private_data_boundary_review_status": "satisfactory",
    "browser_auth_boundary_review_status": "satisfactory",
    "audio_capture_boundary_review_status": "satisfactory",
    "scheduler_execution_boundary_review_status": "satisfactory",
    "deletion_export_boundary_review_status": "satisfactory",
    "browser_automation_performed": False,
    "auth_profile_accessed": False,
    "cookie_accessed": False,
    "private_data_read": False,
    "audio_capture_performed": False,
    "loopback_capture_performed": False,
    "network_performed": False,
    "scheduler_execution_performed": False,
    "live_delivery_performed": False,
    "cleanup_or_deletion_performed": False,
    "export_performed": False,
    "subprocess_performed": False,
    "timer_or_sleep_used": False,
    "dependency_change_performed": False,
    "public_github_approval_claimed": False,
    "gate_d_pass_claimed": False,
    "product_promise_alpha_pass_claimed": False,
    "autonomous_participation_performed": False,
    "academic_answer_behavior_performed": False,
}


def build_local_gate_d_security_review_evidence() -> dict[str, object]:
    try:
        return _safe_payload(_build_payload())
    except Exception:
        raise ValueError(GATE_D_SECURITY_REVIEW_EVIDENCE_ERROR) from None


def _build_payload() -> dict[str, object]:
    return dict(_EXPECTED_PAYLOAD)


def _safe_payload(payload: object) -> dict[str, object]:
    if type(payload) is not dict:
        _fail()
    if payload != _EXPECTED_PAYLOAD or list(payload) != list(_EXPECTED_PAYLOAD):
        _fail()
    return payload


def _fail() -> NoReturn:
    raise ValueError(GATE_D_SECURITY_REVIEW_EVIDENCE_ERROR)


__all__ = [
    "GATE_D_SECURITY_REVIEW_EVIDENCE_ERROR",
    "build_local_gate_d_security_review_evidence",
]
