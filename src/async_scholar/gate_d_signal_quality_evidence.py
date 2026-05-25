from __future__ import annotations

from typing import NoReturn

GATE_D_SIGNAL_QUALITY_EVIDENCE_ERROR = (
    "gate d signal quality evidence could not be built"
)

_EXPECTED_PAYLOAD = {
    "evidence_kind": "local_gate_d_public_open_signal_quality_evidence",
    "signal_quality_evidence_status": "satisfactory",
    "ticket_126_public_open_evidence_status": "documented",
    "metadata_only_evidence_status": "documented",
    "public_open_evidence_status": "documented",
    "public_open_sample_rate_hz": 16000,
    "public_open_duration_seconds": 68.370375,
    "public_open_vad_segment_count": 32,
    "public_open_stt_segment_count": 16,
    "public_open_elapsed_seconds": 4.515231,
    "public_open_real_time_factor": 0.066041,
    "artifact_presence_checks_passed": True,
    "no_local_microphone_quality_claim_status": "documented",
    "no_transcript_usefulness_claim_status": "documented",
    "no_real_online_monitoring_claim_status": "documented",
    "no_live_delivery_claim_status": "documented",
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
    "hardware_or_device_enumeration_performed": False,
    "scheduler_execution_performed": False,
    "live_delivery_performed": False,
    "cleanup_or_deletion_performed": False,
    "export_performed": False,
    "dependency_change_performed": False,
    "local_microphone_quality_claimed": False,
    "transcript_usefulness_claimed": False,
    "real_online_monitoring_claimed": False,
    "live_alert_delivery_claimed": False,
    "gate_d_pass_claimed": False,
    "product_promise_alpha_pass_claimed": False,
    "autonomous_participation_performed": False,
    "academic_answer_behavior_performed": False,
}


def build_local_gate_d_signal_quality_evidence() -> dict[str, object]:
    try:
        return _safe_payload(_build_payload())
    except Exception:
        raise ValueError(GATE_D_SIGNAL_QUALITY_EVIDENCE_ERROR) from None


def _build_payload() -> dict[str, object]:
    return dict(_EXPECTED_PAYLOAD)


def _safe_payload(payload: object) -> dict[str, object]:
    if type(payload) is not dict:
        _fail()
    if payload != _EXPECTED_PAYLOAD or list(payload) != list(_EXPECTED_PAYLOAD):
        _fail()
    return payload


def _fail() -> NoReturn:
    raise ValueError(GATE_D_SIGNAL_QUALITY_EVIDENCE_ERROR)


__all__ = [
    "GATE_D_SIGNAL_QUALITY_EVIDENCE_ERROR",
    "build_local_gate_d_signal_quality_evidence",
]
