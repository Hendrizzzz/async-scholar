from __future__ import annotations

from typing import NoReturn

GATE_D_PRODUCT_JUDGMENT_PACKET_ERROR = (
    "gate d product judgment packet could not be built"
)

_EXPECTED_PAYLOAD = {
    "packet_kind": "local_gate_d_product_judgment_review_packet",
    "product_judgment_packet_status": "ready_for_manual_review",
    "manual_product_judgment_required": True,
    "manual_product_judgment_recorded": False,
    "product_judgment_evidence_status": "blocking",
    "review_packet_scope_status": "metadata_only",
    "recommended_manual_review_action": "review_product_promise_alpha_manually",
    "review_requires_human_product_judgment": True,
    "review_can_be_completed_by_ai": False,
    "local_gate_d_bundle_expected_blocking_evidence": [
        "product_judgment_evidence",
    ],
    "local_gate_d_bundle_expected_missing_evidence": [],
    "local_gate_d_bundle_expected_ready_for_gate_review": False,
    "no_gate_d_pass_claim_status": "documented",
    "no_product_promise_alpha_pass_claim_status": "documented",
    "no_online_monitoring_approval_status": "documented",
    "no_transcript_usefulness_claim_status": "documented",
    "no_local_microphone_quality_claim_status": "documented",
    "no_live_alert_delivery_claim_status": "documented",
    "no_browser_readiness_claim_status": "documented",
    "no_scheduler_execution_claim_status": "documented",
    "no_participation_approval_claim_status": "documented",
    "file_io_performed": False,
    "artifact_read": False,
    "artifact_created": False,
    "network_performed": False,
    "subprocess_performed": False,
    "browser_automation_performed": False,
    "auth_profile_accessed": False,
    "cookie_accessed": False,
    "private_data_read": False,
    "audio_capture_performed": False,
    "recording_performed": False,
    "vad_execution_performed": False,
    "stt_execution_performed": False,
    "model_loaded": False,
    "scheduler_execution_performed": False,
    "live_delivery_performed": False,
    "cleanup_or_deletion_performed": False,
    "export_performed": False,
    "dependency_change_performed": False,
    "gate_d_pass_claimed": False,
    "product_promise_alpha_pass_claimed": False,
    "online_monitoring_approved": False,
    "transcript_usefulness_claimed": False,
    "local_microphone_quality_claimed": False,
    "live_alert_delivery_claimed": False,
    "browser_readiness_claimed": False,
    "scheduler_execution_claimed": False,
    "participation_approval_claimed": False,
    "autonomous_participation_performed": False,
    "academic_answer_behavior_performed": False,
}


def build_local_gate_d_product_judgment_packet() -> dict[str, object]:
    try:
        return _safe_payload(_build_payload())
    except Exception:
        raise ValueError(GATE_D_PRODUCT_JUDGMENT_PACKET_ERROR) from None


def _build_payload() -> dict[str, object]:
    return {
        key: list(value) if isinstance(value, list) else value
        for key, value in _EXPECTED_PAYLOAD.items()
    }


def _safe_payload(payload: object) -> dict[str, object]:
    if type(payload) is not dict:
        _fail()
    if payload != _EXPECTED_PAYLOAD or list(payload) != list(_EXPECTED_PAYLOAD):
        _fail()
    return payload


def _fail() -> NoReturn:
    raise ValueError(GATE_D_PRODUCT_JUDGMENT_PACKET_ERROR)


__all__ = [
    "GATE_D_PRODUCT_JUDGMENT_PACKET_ERROR",
    "build_local_gate_d_product_judgment_packet",
]
