from __future__ import annotations

from typing import NoReturn

GATE_D_HANDOFF_PACKET_ERROR = "gate d handoff packet could not be built"

_STATUS_SATISFACTORY = "satisfactory"
_STATUS_BLOCKING = "blocking"
_BLOCKING_EVIDENCE = [
    "product_judgment_evidence",
]
_MISSING_EVIDENCE: list[str] = []

_EXPECTED_BUNDLE_PAYLOAD = {
    "bundle_kind": "local_gate_d_smoke_evidence_bundle",
    "mic_diagnostics_after_reboot_status": _STATUS_SATISFACTORY,
    "alert_routing_status": _STATUS_SATISFACTORY,
    "security_review_status": _STATUS_SATISFACTORY,
    "policy_gate_tests_status": _STATUS_SATISFACTORY,
    "rollback_plan_for_loopback_playwright_spike_status": _STATUS_SATISFACTORY,
    "signal_quality_evidence_status": _STATUS_SATISFACTORY,
    "scheduler_lifecycle_evidence_status": _STATUS_SATISFACTORY,
    "delivery_path_evidence_status": _STATUS_SATISFACTORY,
    "monitoring_boundary_evidence_status": _STATUS_SATISFACTORY,
    "product_judgment_evidence_status": _STATUS_BLOCKING,
    "missing_evidence": _MISSING_EVIDENCE,
    "missing_evidence_count": 0,
    "blocking_evidence": _BLOCKING_EVIDENCE,
    "blocking_evidence_count": 1,
    "satisfactory_evidence_count": 9,
    "ready_for_gate_review": False,
    "readiness_decision": "blocked",
    "readiness_reason": "required_gate_d_readiness_evidence_missing_or_blocking",
    "gap_decision": "gaps_present",
    "gap_reason": "required_gate_d_evidence_gaps_present",
    "live_delivery_performed": False,
    "real_online_monitoring_performed": False,
    "browser_automation_performed": False,
    "audio_capture_performed": False,
    "scheduler_execution_performed": False,
    "gate_d_pass_claimed": False,
    "product_promise_alpha_pass_claimed": False,
}

_EXPECTED_PRODUCT_JUDGMENT_PACKET = {
    "packet_kind": "local_gate_d_product_judgment_review_packet",
    "product_judgment_packet_status": "ready_for_manual_review",
    "manual_product_judgment_required": True,
    "manual_product_judgment_recorded": False,
    "product_judgment_evidence_status": _STATUS_BLOCKING,
    "review_packet_scope_status": "metadata_only",
    "recommended_manual_review_action": "review_product_promise_alpha_manually",
    "review_requires_human_product_judgment": True,
    "review_can_be_completed_by_ai": False,
    "local_gate_d_bundle_expected_blocking_evidence": _BLOCKING_EVIDENCE,
    "local_gate_d_bundle_expected_missing_evidence": _MISSING_EVIDENCE,
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

_EXPECTED_HANDOFF_PAYLOAD = {
    "packet_kind": "local_gate_d_handoff_packet",
    "handoff_packet_status": "ready_for_manual_review",
    "handoff_packet_scope_status": "metadata_only",
    "local_gate_d_bundle_status": "blocked",
    "product_judgment_packet_status": "ready_for_manual_review",
    "manual_product_judgment_required": True,
    "manual_product_judgment_recorded": False,
    "review_requires_human_product_judgment": True,
    "review_can_be_completed_by_ai": False,
    "ready_for_gate_review": False,
    "readiness_decision": "blocked",
    "readiness_reason": "required_gate_d_readiness_evidence_missing_or_blocking",
    "gap_decision": "gaps_present",
    "gap_reason": "required_gate_d_evidence_gaps_present",
    "missing_evidence": _MISSING_EVIDENCE,
    "missing_evidence_count": 0,
    "blocking_evidence": _BLOCKING_EVIDENCE,
    "blocking_evidence_count": 1,
    "satisfactory_evidence_count": 9,
    "product_judgment_evidence_status": _STATUS_BLOCKING,
    "gate_d_pass_claimed": False,
    "product_promise_alpha_pass_claimed": False,
    "real_online_monitoring_performed": False,
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


def build_local_gate_d_handoff_packet() -> dict[str, object]:
    try:
        bundle = _safe_bundle_payload(_build_bundle_payload())
        product_packet = _safe_product_judgment_packet_payload(
            _build_product_judgment_packet_payload()
        )
        return _safe_handoff_payload(_build_handoff_payload(bundle, product_packet))
    except Exception:
        raise ValueError(GATE_D_HANDOFF_PACKET_ERROR) from None


def _build_bundle_payload() -> dict[str, object]:
    from async_scholar.gate_d_local_evidence_bundle import (
        build_local_gate_d_smoke_evidence_bundle,
    )

    return build_local_gate_d_smoke_evidence_bundle()


def _build_product_judgment_packet_payload() -> dict[str, object]:
    from async_scholar.gate_d_product_judgment_packet import (
        build_local_gate_d_product_judgment_packet,
    )

    return build_local_gate_d_product_judgment_packet()


def _build_handoff_payload(
    bundle: dict[str, object],
    product_packet: dict[str, object],
) -> dict[str, object]:
    return {
        "packet_kind": "local_gate_d_handoff_packet",
        "handoff_packet_status": "ready_for_manual_review",
        "handoff_packet_scope_status": "metadata_only",
        "local_gate_d_bundle_status": "blocked",
        "product_judgment_packet_status": product_packet[
            "product_judgment_packet_status"
        ],
        "manual_product_judgment_required": product_packet[
            "manual_product_judgment_required"
        ],
        "manual_product_judgment_recorded": product_packet[
            "manual_product_judgment_recorded"
        ],
        "review_requires_human_product_judgment": product_packet[
            "review_requires_human_product_judgment"
        ],
        "review_can_be_completed_by_ai": product_packet[
            "review_can_be_completed_by_ai"
        ],
        "ready_for_gate_review": bundle["ready_for_gate_review"],
        "readiness_decision": bundle["readiness_decision"],
        "readiness_reason": bundle["readiness_reason"],
        "gap_decision": bundle["gap_decision"],
        "gap_reason": bundle["gap_reason"],
        "missing_evidence": list(_list_value(bundle, "missing_evidence")),
        "missing_evidence_count": bundle["missing_evidence_count"],
        "blocking_evidence": list(_list_value(bundle, "blocking_evidence")),
        "blocking_evidence_count": bundle["blocking_evidence_count"],
        "satisfactory_evidence_count": bundle["satisfactory_evidence_count"],
        "product_judgment_evidence_status": bundle["product_judgment_evidence_status"],
        "gate_d_pass_claimed": bundle["gate_d_pass_claimed"],
        "product_promise_alpha_pass_claimed": bundle[
            "product_promise_alpha_pass_claimed"
        ],
        "real_online_monitoring_performed": bundle["real_online_monitoring_performed"],
        "browser_automation_performed": bundle["browser_automation_performed"],
        "auth_profile_accessed": product_packet["auth_profile_accessed"],
        "cookie_accessed": product_packet["cookie_accessed"],
        "private_data_read": product_packet["private_data_read"],
        "audio_capture_performed": bundle["audio_capture_performed"],
        "recording_performed": product_packet["recording_performed"],
        "vad_execution_performed": product_packet["vad_execution_performed"],
        "stt_execution_performed": product_packet["stt_execution_performed"],
        "model_loaded": product_packet["model_loaded"],
        "scheduler_execution_performed": bundle["scheduler_execution_performed"],
        "live_delivery_performed": bundle["live_delivery_performed"],
        "cleanup_or_deletion_performed": product_packet[
            "cleanup_or_deletion_performed"
        ],
        "export_performed": product_packet["export_performed"],
        "dependency_change_performed": product_packet["dependency_change_performed"],
        "online_monitoring_approved": product_packet["online_monitoring_approved"],
        "transcript_usefulness_claimed": product_packet[
            "transcript_usefulness_claimed"
        ],
        "local_microphone_quality_claimed": product_packet[
            "local_microphone_quality_claimed"
        ],
        "live_alert_delivery_claimed": product_packet["live_alert_delivery_claimed"],
        "browser_readiness_claimed": product_packet["browser_readiness_claimed"],
        "scheduler_execution_claimed": product_packet["scheduler_execution_claimed"],
        "participation_approval_claimed": product_packet[
            "participation_approval_claimed"
        ],
        "autonomous_participation_performed": product_packet[
            "autonomous_participation_performed"
        ],
        "academic_answer_behavior_performed": product_packet[
            "academic_answer_behavior_performed"
        ],
    }


def _list_value(payload: dict[str, object], key: str) -> list[str]:
    value = payload[key]
    if type(value) is not list or any(type(item) is not str for item in value):
        _fail()
    return value


def _safe_bundle_payload(payload: object) -> dict[str, object]:
    if (
        type(payload) is not dict
        or payload != _EXPECTED_BUNDLE_PAYLOAD
        or list(payload) != list(_EXPECTED_BUNDLE_PAYLOAD)
    ):
        _fail()
    return payload


def _safe_product_judgment_packet_payload(payload: object) -> dict[str, object]:
    if (
        type(payload) is not dict
        or payload != _EXPECTED_PRODUCT_JUDGMENT_PACKET
        or list(payload) != list(_EXPECTED_PRODUCT_JUDGMENT_PACKET)
    ):
        _fail()
    return payload


def _safe_handoff_payload(payload: object) -> dict[str, object]:
    if (
        type(payload) is not dict
        or payload != _EXPECTED_HANDOFF_PAYLOAD
        or list(payload) != list(_EXPECTED_HANDOFF_PAYLOAD)
    ):
        _fail()
    return payload


def _fail() -> NoReturn:
    raise ValueError(GATE_D_HANDOFF_PACKET_ERROR)


__all__ = [
    "GATE_D_HANDOFF_PACKET_ERROR",
    "build_local_gate_d_handoff_packet",
]
