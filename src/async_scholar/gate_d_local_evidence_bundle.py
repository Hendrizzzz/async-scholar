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
    "product_judgment_evidence",
]
_FIXED_STATUSES = {
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
        from async_scholar.gate_d_mic_diagnostics_after_reboot_evidence import (
            build_local_gate_d_mic_diagnostics_after_reboot_evidence,
        )
        from async_scholar.gate_d_readiness import (
            build_gate_d_evidence_gap_summary,
            build_gate_d_readiness_report,
        )
        from async_scholar.gate_d_rollback_plan_evidence import (
            build_local_gate_d_rollback_plan_evidence,
        )
        from async_scholar.gate_d_scheduler_lifecycle_evidence import (
            build_local_gate_d_scheduler_lifecycle_evidence,
        )
        from async_scholar.gate_d_security_review_evidence import (
            build_local_gate_d_security_review_evidence,
        )
        from async_scholar.gate_d_signal_quality_evidence import (
            build_local_gate_d_signal_quality_evidence,
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
        mic_diagnostics_after_reboot_status = _mic_diagnostics_after_reboot_status(
            build_local_gate_d_mic_diagnostics_after_reboot_evidence()
        )
        signal_quality_evidence_status = _signal_quality_evidence_status(
            build_local_gate_d_signal_quality_evidence()
        )
        rollback_plan_status = _rollback_plan_status(
            build_local_gate_d_rollback_plan_evidence()
        )
        security_review_status = _security_review_status(
            build_local_gate_d_security_review_evidence()
        )
        scheduler_lifecycle_status = _scheduler_lifecycle_evidence_status(
            build_local_gate_d_scheduler_lifecycle_evidence()
        )
        statuses = {
            **_FIXED_STATUSES,
            "mic_diagnostics_after_reboot": mic_diagnostics_after_reboot_status,
            "alert_routing": alert_routing_status,
            "security_review": security_review_status,
            "policy_gate_tests": policy_gate_tests_status,
            "rollback_plan_for_loopback_playwright_spike": rollback_plan_status,
            "signal_quality_evidence": signal_quality_evidence_status,
            "scheduler_lifecycle_evidence": scheduler_lifecycle_status,
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


def _mic_diagnostics_after_reboot_status(payload: object) -> str:
    if type(payload) is not dict:
        _fail()
    if (
        payload.get("evidence_kind")
        != "local_gate_d_mic_diagnostics_after_reboot_evidence"
        or payload.get("mic_diagnostics_after_reboot_status") != _STATUS_SATISFACTORY
        or payload.get("file_io_performed") is not False
        or payload.get("artifact_read") is not False
        or payload.get("artifact_created") is not False
        or payload.get("device_name_exposed") is not False
        or payload.get("private_path_exposed") is not False
        or payload.get("transcript_text_exposed") is not False
        or payload.get("audio_capture_performed") is not False
        or payload.get("recording_performed") is not False
        or payload.get("vad_performed") is not False
        or payload.get("stt_performed") is not False
        or payload.get("signal_quality_claimed") is not False
        or payload.get("transcript_usefulness_claimed") is not False
        or payload.get("network_performed") is not False
        or payload.get("browser_automation_performed") is not False
        or payload.get("auth_profile_accessed") is not False
        or payload.get("cookie_accessed") is not False
        or payload.get("private_data_read") is not False
        or payload.get("scheduler_execution_performed") is not False
        or payload.get("live_delivery_performed") is not False
        or payload.get("cleanup_or_deletion_performed") is not False
        or payload.get("export_performed") is not False
        or payload.get("dependency_change_performed") is not False
        or payload.get("gate_d_pass_claimed") is not False
        or payload.get("product_promise_alpha_pass_claimed") is not False
        or payload.get("autonomous_participation_performed") is not False
        or payload.get("academic_answer_behavior_performed") is not False
    ):
        _fail()
    return _STATUS_SATISFACTORY


def _signal_quality_evidence_status(payload: object) -> str:
    if type(payload) is not dict:
        _fail()
    if (
        payload.get("evidence_kind")
        != "local_gate_d_public_open_signal_quality_evidence"
        or payload.get("signal_quality_evidence_status") != _STATUS_SATISFACTORY
        or payload.get("ticket_126_public_open_evidence_status") != "documented"
        or payload.get("metadata_only_evidence_status") != "documented"
        or payload.get("public_open_evidence_status") != "documented"
        or payload.get("public_open_sample_rate_hz") != 16000
        or payload.get("public_open_duration_seconds") != 68.370375
        or payload.get("public_open_vad_segment_count") != 32
        or payload.get("public_open_stt_segment_count") != 16
        or payload.get("public_open_elapsed_seconds") != 4.515231
        or payload.get("public_open_real_time_factor") != 0.066041
        or payload.get("artifact_presence_checks_passed") is not True
        or payload.get("no_local_microphone_quality_claim_status") != "documented"
        or payload.get("no_transcript_usefulness_claim_status") != "documented"
        or payload.get("no_real_online_monitoring_claim_status") != "documented"
        or payload.get("no_live_delivery_claim_status") != "documented"
        or payload.get("file_io_performed") is not False
        or payload.get("artifact_read") is not False
        or payload.get("artifact_created") is not False
        or payload.get("download_performed") is not False
        or payload.get("audio_capture_performed") is not False
        or payload.get("recording_performed") is not False
        or payload.get("vad_execution_performed") is not False
        or payload.get("stt_execution_performed") is not False
        or payload.get("model_loaded") is not False
        or payload.get("subprocess_performed") is not False
        or payload.get("network_performed") is not False
        or payload.get("browser_automation_performed") is not False
        or payload.get("auth_profile_accessed") is not False
        or payload.get("cookie_accessed") is not False
        or payload.get("private_data_read") is not False
        or payload.get("hardware_or_device_enumeration_performed") is not False
        or payload.get("scheduler_execution_performed") is not False
        or payload.get("live_delivery_performed") is not False
        or payload.get("cleanup_or_deletion_performed") is not False
        or payload.get("export_performed") is not False
        or payload.get("dependency_change_performed") is not False
        or payload.get("local_microphone_quality_claimed") is not False
        or payload.get("transcript_usefulness_claimed") is not False
        or payload.get("real_online_monitoring_claimed") is not False
        or payload.get("live_alert_delivery_claimed") is not False
        or payload.get("gate_d_pass_claimed") is not False
        or payload.get("product_promise_alpha_pass_claimed") is not False
        or payload.get("autonomous_participation_performed") is not False
        or payload.get("academic_answer_behavior_performed") is not False
    ):
        _fail()
    return _STATUS_SATISFACTORY


def _rollback_plan_status(payload: object) -> str:
    if type(payload) is not dict:
        _fail()
    if (
        payload.get("evidence_kind") != "local_gate_d_rollback_plan_evidence"
        or payload.get("rollback_plan_for_loopback_playwright_spike_status")
        != _STATUS_SATISFACTORY
        or payload.get("browser_automation_performed") is not False
        or payload.get("audio_capture_performed") is not False
        or payload.get("loopback_capture_performed") is not False
        or payload.get("network_performed") is not False
        or payload.get("external_platform_accessed") is not False
        or payload.get("profile_state_accessed") is not False
        or payload.get("gate_d_pass_claimed") is not False
        or payload.get("product_promise_alpha_pass_claimed") is not False
    ):
        _fail()
    return _STATUS_SATISFACTORY


def _security_review_status(payload: object) -> str:
    if type(payload) is not dict:
        _fail()
    if (
        payload.get("evidence_kind") != "local_gate_d_security_review_evidence"
        or payload.get("security_review_status") != _STATUS_SATISFACTORY
        or payload.get("browser_automation_performed") is not False
        or payload.get("auth_profile_accessed") is not False
        or payload.get("cookie_accessed") is not False
        or payload.get("private_data_read") is not False
        or payload.get("audio_capture_performed") is not False
        or payload.get("loopback_capture_performed") is not False
        or payload.get("network_performed") is not False
        or payload.get("scheduler_execution_performed") is not False
        or payload.get("live_delivery_performed") is not False
        or payload.get("cleanup_or_deletion_performed") is not False
        or payload.get("export_performed") is not False
        or payload.get("subprocess_performed") is not False
        or payload.get("timer_or_sleep_used") is not False
        or payload.get("dependency_change_performed") is not False
        or payload.get("public_github_approval_claimed") is not False
        or payload.get("gate_d_pass_claimed") is not False
        or payload.get("product_promise_alpha_pass_claimed") is not False
        or payload.get("autonomous_participation_performed") is not False
        or payload.get("academic_answer_behavior_performed") is not False
    ):
        _fail()
    return _STATUS_SATISFACTORY


def _scheduler_lifecycle_evidence_status(payload: object) -> str:
    if type(payload) is not dict:
        _fail()
    if (
        payload.get("evidence_kind") != "local_gate_d_scheduler_lifecycle_evidence"
        or payload.get("scheduler_lifecycle_evidence_status") != _STATUS_SATISFACTORY
        or payload.get("file_io_performed") is not False
        or payload.get("sqlite_accessed") is not False
        or payload.get("scheduler_execution_performed") is not False
        or payload.get("scheduler_runtime_imported") is not False
        or payload.get("scheduler_lifecycle_smoke_performed") is not False
        or payload.get("background_loop_performed") is not False
        or payload.get("timer_or_sleep_used") is not False
        or payload.get("daemon_or_recurring_job_performed") is not False
        or payload.get("subprocess_performed") is not False
        or payload.get("network_performed") is not False
        or payload.get("browser_automation_performed") is not False
        or payload.get("auth_profile_accessed") is not False
        or payload.get("cookie_accessed") is not False
        or payload.get("private_data_read") is not False
        or payload.get("audio_capture_performed") is not False
        or payload.get("loopback_capture_performed") is not False
        or payload.get("live_delivery_performed") is not False
        or payload.get("cleanup_or_deletion_performed") is not False
        or payload.get("export_performed") is not False
        or payload.get("dependency_change_performed") is not False
        or payload.get("gate_d_pass_claimed") is not False
        or payload.get("product_promise_alpha_pass_claimed") is not False
        or payload.get("autonomous_participation_performed") is not False
        or payload.get("academic_answer_behavior_performed") is not False
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
        or payload["missing_evidence_count"] != 1
        or payload["blocking_evidence"] != []
        or payload["blocking_evidence_count"] != 0
        or payload["satisfactory_evidence_count"] != 9
        or payload["decision"] != _GAP_DECISION
        or payload["reason"] != _GAP_REASON
    ):
        _fail()
    _validate_status_fields(payload)
    return payload


def _validate_status_fields(payload: dict[str, object]) -> None:
    expected = {
        "mic_diagnostics_after_reboot_status": _STATUS_SATISFACTORY,
        "alert_routing_status": _STATUS_SATISFACTORY,
        "security_review_status": _STATUS_SATISFACTORY,
        "policy_gate_tests_status": _STATUS_SATISFACTORY,
        "rollback_plan_for_loopback_playwright_spike_status": _STATUS_SATISFACTORY,
        "signal_quality_evidence_status": _STATUS_SATISFACTORY,
        "scheduler_lifecycle_evidence_status": _STATUS_SATISFACTORY,
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
        "mic_diagnostics_after_reboot_status": _STATUS_SATISFACTORY,
        "alert_routing_status": _STATUS_SATISFACTORY,
        "security_review_status": _STATUS_SATISFACTORY,
        "policy_gate_tests_status": _STATUS_SATISFACTORY,
        "rollback_plan_for_loopback_playwright_spike_status": _STATUS_SATISFACTORY,
        "signal_quality_evidence_status": _STATUS_SATISFACTORY,
        "scheduler_lifecycle_evidence_status": _STATUS_SATISFACTORY,
        "delivery_path_evidence_status": _STATUS_SATISFACTORY,
        "monitoring_boundary_evidence_status": _STATUS_SATISFACTORY,
        "product_judgment_evidence_status": _STATUS_MISSING,
        "missing_evidence": _MISSING_EVIDENCE,
        "missing_evidence_count": 1,
        "blocking_evidence": [],
        "blocking_evidence_count": 0,
        "satisfactory_evidence_count": 9,
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
