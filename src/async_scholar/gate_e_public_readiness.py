from __future__ import annotations

from typing import NoReturn

GATE_E_PUBLIC_READINESS_ERROR = "gate e public readiness could not be built"

_STATUS_SATISFACTORY = "satisfactory"
_STATUS_MISSING = "missing"
_STATUS_BLOCKING = "blocking"
_ALLOWED_STATUSES = {_STATUS_SATISFACTORY, _STATUS_MISSING, _STATUS_BLOCKING}
_REVIEW_STATUS_KEYS = (
    "public_docs_boundary_review_status",
    "secret_and_private_data_review_status",
    "generated_artifact_review_status",
    "ignored_file_review_status",
    "push_merge_release_plan_review_status",
)
_REVIEW_ITEMS_BY_STATUS_KEY = {
    "public_docs_boundary_review_status": "public_docs_boundary_review",
    "secret_and_private_data_review_status": "secret_and_private_data_review",
    "generated_artifact_review_status": "generated_artifact_review",
    "ignored_file_review_status": "ignored_file_review",
    "push_merge_release_plan_review_status": "push_merge_release_plan_review",
}
_FALSE_FLAG_KEYS = (
    "public_release_approved",
    "push_approved",
    "merge_approved",
    "public_github_approval_claimed",
    "publish_performed",
    "push_performed",
    "merge_performed",
    "browser_or_server_launched",
    "browser_automation_performed",
    "play" + "wright_or_in_app_browser_performed",
    "screenshot_trace_video_download_performed",
    "auth_profile_accessed",
    "cookie_accessed",
    "private_data_read",
    "audio_capture_performed",
    "hardware_access_performed",
    "loopback_capture_performed",
    "live_delivery_performed",
    "scheduler_background_execution_performed",
    "deletion_or_export_performed",
    "dependency_change_performed",
    "autonomous_participation_performed",
    "academic_answer_behavior_performed",
    "product_promise_alpha_scope_broadened",
)


def build_gate_e_public_readiness_preflight(
    *,
    public_docs_boundary_review_status: str = _STATUS_MISSING,
    secret_and_private_data_review_status: str = _STATUS_MISSING,
    generated_artifact_review_status: str = _STATUS_MISSING,
    ignored_file_review_status: str = _STATUS_MISSING,
    push_merge_release_plan_review_status: str = _STATUS_MISSING,
) -> dict[str, object]:
    try:
        statuses = _review_statuses(
            public_docs_boundary_review_status=public_docs_boundary_review_status,
            secret_and_private_data_review_status=(
                secret_and_private_data_review_status
            ),
            generated_artifact_review_status=generated_artifact_review_status,
            ignored_file_review_status=ignored_file_review_status,
            push_merge_release_plan_review_status=(
                push_merge_release_plan_review_status
            ),
        )
        expected = _expected_payload(statuses)
        return _safe_payload(_build_payload(statuses), expected)
    except Exception:
        raise ValueError(GATE_E_PUBLIC_READINESS_ERROR) from None


def _review_statuses(**statuses: str) -> dict[str, str]:
    if tuple(statuses) != _REVIEW_STATUS_KEYS:
        _fail()
    if any(status not in _ALLOWED_STATUSES for status in statuses.values()):
        _fail()
    return dict(statuses)


def _build_payload(statuses: dict[str, str]) -> dict[str, object]:
    return _expected_payload(statuses)


def _expected_payload(statuses: dict[str, str]) -> dict[str, object]:
    missing_review_items = [
        _REVIEW_ITEMS_BY_STATUS_KEY[key]
        for key in _REVIEW_STATUS_KEYS
        if statuses[key] == _STATUS_MISSING
    ]
    missing_review_items.append("human_gate_e_approval")
    blocking_review_items = [
        _REVIEW_ITEMS_BY_STATUS_KEY[key]
        for key in _REVIEW_STATUS_KEYS
        if statuses[key] == _STATUS_BLOCKING
    ]
    ready_for_human_gate_e_review = (
        len(missing_review_items) == 1 and not blocking_review_items
    )
    reason = (
        "human_gate_e_approval_required"
        if ready_for_human_gate_e_review
        else "required_gate_e_preflight_items_missing_or_blocking"
    )
    payload: dict[str, object] = {
        "preflight_kind": "gate_e_public_readiness",
        "mode": "dry_run_report_only",
        "gate_d_scope_status": "narrow_local_fixture_to_reviewer_pass_recorded",
        "gate_e_status": "human_approval_required",
        "decision": "blocked",
        "reason": reason,
        "ready_for_human_gate_e_review": ready_for_human_gate_e_review,
        "human_gate_e_approval_required": True,
        "human_gate_e_approval_status": _STATUS_MISSING,
        **statuses,
        "missing_review_items": missing_review_items,
        "missing_review_item_count": len(missing_review_items),
        "blocking_review_items": blocking_review_items,
        "blocking_review_item_count": len(blocking_review_items),
        "satisfactory_review_item_count": sum(
            status == _STATUS_SATISFACTORY for status in statuses.values()
        ),
    }
    for key in _FALSE_FLAG_KEYS:
        payload[key] = False
    return payload


def _safe_payload(
    payload: object,
    expected: dict[str, object],
) -> dict[str, object]:
    if type(payload) is not dict:
        _fail()
    if payload != expected or list(payload) != list(expected):
        _fail()
    return payload


def _fail() -> NoReturn:
    raise ValueError(GATE_E_PUBLIC_READINESS_ERROR)


__all__ = [
    "GATE_E_PUBLIC_READINESS_ERROR",
    "build_gate_e_public_readiness_preflight",
]
