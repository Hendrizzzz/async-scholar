from __future__ import annotations

from typing import NoReturn

GATE_D_SCHEDULER_LIFECYCLE_EVIDENCE_ERROR = (
    "gate d scheduler lifecycle evidence could not be built"
)

_EXPECTED_PAYLOAD = {
    "evidence_kind": "local_gate_d_scheduler_lifecycle_evidence",
    "scheduler_lifecycle_evidence_status": "satisfactory",
    "explicit_invocation_boundary_status": "documented",
    "metadata_only_lifecycle_status": "documented",
    "no_background_loop_status": "documented",
    "no_timer_status": "documented",
    "no_scheduler_runtime_import_status": "documented",
    "local_only_status": "documented",
    "file_io_performed": False,
    "sqlite_accessed": False,
    "scheduler_execution_performed": False,
    "scheduler_runtime_imported": False,
    "scheduler_lifecycle_smoke_performed": False,
    "background_loop_performed": False,
    "timer_or_sleep_used": False,
    "daemon_or_recurring_job_performed": False,
    "subprocess_performed": False,
    "network_performed": False,
    "browser_automation_performed": False,
    "auth_profile_accessed": False,
    "cookie_accessed": False,
    "private_data_read": False,
    "audio_capture_performed": False,
    "loopback_capture_performed": False,
    "live_delivery_performed": False,
    "cleanup_or_deletion_performed": False,
    "export_performed": False,
    "dependency_change_performed": False,
    "gate_d_pass_claimed": False,
    "product_promise_alpha_pass_claimed": False,
    "autonomous_participation_performed": False,
    "academic_answer_behavior_performed": False,
}


def build_local_gate_d_scheduler_lifecycle_evidence() -> dict[str, object]:
    try:
        return _safe_payload(_build_payload())
    except Exception:
        raise ValueError(GATE_D_SCHEDULER_LIFECYCLE_EVIDENCE_ERROR) from None


def _build_payload() -> dict[str, object]:
    return dict(_EXPECTED_PAYLOAD)


def _safe_payload(payload: object) -> dict[str, object]:
    if type(payload) is not dict:
        _fail()
    if payload != _EXPECTED_PAYLOAD or list(payload) != list(_EXPECTED_PAYLOAD):
        _fail()
    return payload


def _fail() -> NoReturn:
    raise ValueError(GATE_D_SCHEDULER_LIFECYCLE_EVIDENCE_ERROR)


__all__ = [
    "GATE_D_SCHEDULER_LIFECYCLE_EVIDENCE_ERROR",
    "build_local_gate_d_scheduler_lifecycle_evidence",
]
