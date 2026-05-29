from __future__ import annotations

from typing import NoReturn

GATE_D_PRODUCT_JUDGMENT_EVIDENCE_ERROR = (
    "gate d product judgment evidence could not be built"
)

_EXPECTED_PAYLOAD = {
    "evidence_kind": "local_gate_d_product_judgment_evidence",
    "product_judgment_evidence_status": "blocking",
    "manual_product_judgment_required_status": "required",
    "manual_product_judgment_recorded": False,
    "metadata_only_evidence_status": "documented",
    "no_gate_d_pass_claim_status": "documented",
    "no_product_promise_alpha_pass_claim_status": "documented",
    "no_real_online_monitoring_claim_status": "documented",
    "no_live_delivery_claim_status": "documented",
    "no_transcript_usefulness_claim_status": "documented",
    "no_local_microphone_quality_claim_status": "documented",
    "file_io_performed": False,
    "artifact_read": False,
    "artifact_created": False,
    "download_performed": False,
    "audio_capture_performed": False,
    "recording_performed": False,
    "vad_execution_performed": False,
    "stt_execution_performed": False,
    "model_loaded": False,
    "subprocess_performed": False,
    "network_performed": False,
    "browser_automation_performed": False,
    "auth_profile_accessed": False,
    "cookie_accessed": False,
    "private_data_read": False,
    "scheduler_execution_performed": False,
    "live_delivery_performed": False,
    "cleanup_or_deletion_performed": False,
    "export_performed": False,
    "dependency_change_performed": False,
    "real_online_monitoring_claimed": False,
    "live_alert_delivery_claimed": False,
    "transcript_usefulness_claimed": False,
    "local_microphone_quality_claimed": False,
    "gate_d_pass_claimed": False,
    "product_promise_alpha_pass_claimed": False,
    "autonomous_participation_performed": False,
    "academic_answer_behavior_performed": False,
}


def build_local_gate_d_product_judgment_evidence() -> dict[str, object]:
    try:
        return _safe_payload(_build_payload())
    except Exception:
        raise ValueError(GATE_D_PRODUCT_JUDGMENT_EVIDENCE_ERROR) from None


def _build_payload() -> dict[str, object]:
    return dict(_EXPECTED_PAYLOAD)


def _safe_payload(payload: object) -> dict[str, object]:
    if type(payload) is not dict:
        _fail()
    if payload != _EXPECTED_PAYLOAD or list(payload) != list(_EXPECTED_PAYLOAD):
        _fail()
    return payload


def _fail() -> NoReturn:
    raise ValueError(GATE_D_PRODUCT_JUDGMENT_EVIDENCE_ERROR)


__all__ = [
    "GATE_D_PRODUCT_JUDGMENT_EVIDENCE_ERROR",
    "build_local_gate_d_product_judgment_evidence",
]
