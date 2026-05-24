"""Synthetic local policy gate smoke summary."""

from __future__ import annotations

from typing import Literal, TypedDict

from async_scholar.alerts import build_alert_notification_payload
from async_scholar.session_window_confirmation_response import (
    build_session_window_confirmation_response_summary,
)
from async_scholar.session_window_start_authorization import (
    build_session_window_start_authorization_summary,
    session_window_start_authorization_safe_summary,
)

POLICY_GATE_SMOKE_ERROR = "policy gate smoke could not be built"

PolicyGateTestStatus = Literal["satisfactory"]


class LocalPolicyGateSmokeResult(TypedDict):
    academic_answer_generated: bool
    alert_requires_confirmation: bool
    declined_confirmation_blocks_authorization: bool
    gate_d_pass_claimed: bool
    live_delivery_performed: bool
    malformed_authorization_rejected: bool
    malformed_confirmation_rejected: bool
    participation_action_performed: bool
    policy_gate_tests_status: PolicyGateTestStatus
    product_promise_alpha_pass_claimed: bool
    smoke_kind: str
    start_authorization_status: str
    start_block_reason: str


def build_local_policy_gate_smoke() -> LocalPolicyGateSmokeResult:
    """Build fixed local policy evidence without executing an action."""

    try:
        alert_payload = build_alert_notification_payload("attendance_prompt")
        declined_response = build_session_window_confirmation_response_summary(
            _required_confirmation_preflight(),
            "declined",
        )
        authorization = build_session_window_start_authorization_summary(
            declined_response
        )

        alert_requires_confirmation = (
            alert_payload["requires_confirmation"] is True
            and alert_payload["severity"] == "urgent"
        )
        declined_blocks = (
            authorization["status"] == "blocked"
            and authorization["authorized"] is False
            and authorization["authorized_start_count"] == 0
            and authorization["blocked_start_count"] == 1
            and authorization["block_reason"] == "confirmation_declined"
            and authorization["courses"] == []
        )
        malformed_confirmation_rejected = _malformed_confirmation_is_rejected()
        malformed_authorization_rejected = _malformed_authorization_is_rejected(
            authorization
        )

        if not (
            alert_requires_confirmation
            and declined_blocks
            and malformed_confirmation_rejected
            and malformed_authorization_rejected
        ):
            raise ValueError(POLICY_GATE_SMOKE_ERROR)

        return {
            "academic_answer_generated": False,
            "alert_requires_confirmation": True,
            "declined_confirmation_blocks_authorization": True,
            "gate_d_pass_claimed": False,
            "live_delivery_performed": False,
            "malformed_authorization_rejected": True,
            "malformed_confirmation_rejected": True,
            "participation_action_performed": False,
            "policy_gate_tests_status": "satisfactory",
            "product_promise_alpha_pass_claimed": False,
            "smoke_kind": "local_policy_gate",
            "start_authorization_status": "blocked",
            "start_block_reason": "confirmation_declined",
        }
    except (KeyError, RuntimeError, TypeError, ValueError):
        raise ValueError(POLICY_GATE_SMOKE_ERROR) from None


def _required_confirmation_preflight() -> dict[str, object]:
    return {
        "status": "required",
        "session_id": "policy-gate-smoke-session",
        "source_kind": "file",
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 1,
        "due_count": 1,
        "ready_to_start": True,
        "confirmation_required": True,
        "confirmation_status": "required",
        "blocked_execution_count": 1,
        "courses": [
            {
                "course_id": "policy101",
                "selected_class_time_index": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "due": True,
                "minutes_until_start": 0,
                "stop_after_minutes": 60,
                "enabled": True,
                "requires_confirmation": True,
            }
        ],
    }


def _malformed_confirmation_is_rejected() -> bool:
    malformed = {
        **_required_confirmation_preflight(),
        "confirmation_required": False,
    }
    try:
        build_session_window_confirmation_response_summary(malformed, "declined")
    except ValueError:
        return True
    return False


def _malformed_authorization_is_rejected(
    authorization: dict[str, object],
) -> bool:
    malformed = {**authorization, "authorized": True}
    try:
        session_window_start_authorization_safe_summary(malformed)
    except ValueError:
        return True
    return False


__all__ = [
    "POLICY_GATE_SMOKE_ERROR",
    "LocalPolicyGateSmokeResult",
    "build_local_policy_gate_smoke",
]
