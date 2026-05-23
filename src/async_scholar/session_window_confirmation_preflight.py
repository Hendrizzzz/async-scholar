"""Read-only stored session-window confirmation preflight composition."""

from __future__ import annotations

from pathlib import Path

from async_scholar.scheduled_start import ScheduledStartClock
from async_scholar.session_window_readiness_preflight import (
    build_session_window_readiness_preflight_summary,
)

STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_ERROR = (
    "stored session window confirmation preflight could not be built"
)

StoredSessionWindowConfirmationPreflightSummary = dict[str, object]

_CONFIRMATION_STATUSES = frozenset(("not_required", "required", "disabled"))
_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_KEYS = (
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "ready_to_start",
    "confirmation_required",
    "confirmation_status",
    "blocked_execution_count",
    "courses",
)
_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_COURSE_KEYS = (
    "course_id",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "stop_after_minutes",
    "enabled",
    "requires_confirmation",
)


def build_session_window_confirmation_preflight_summary(
    stored_courses: dict[str, object],
    archive_root: str | Path,
    session_id: str,
    source_kind: str,
    clock: ScheduledStartClock,
    *,
    enabled: bool = True,
) -> StoredSessionWindowConfirmationPreflightSummary:
    """Build the narrow human-confirmation boundary for due session windows."""

    try:
        readiness_summary = build_session_window_readiness_preflight_summary(
            stored_courses,
            archive_root,
            session_id,
            source_kind,
            clock,
            enabled=enabled,
        )
        if not enabled:
            return session_window_confirmation_preflight_safe_summary(
                {
                    "status": "disabled",
                    "session_id": readiness_summary["session_id"],
                    "source_kind": readiness_summary["source_kind"],
                    "clock_day_of_week": readiness_summary["clock_day_of_week"],
                    "clock_local_time": readiness_summary["clock_local_time"],
                    "course_count": readiness_summary["course_count"],
                    "due_count": 0,
                    "ready_to_start": False,
                    "confirmation_required": False,
                    "confirmation_status": "disabled",
                    "blocked_execution_count": 0,
                    "courses": [],
                }
            )

        ready_to_start = _bool_value(readiness_summary["ready_to_start"])
        due_count = _non_negative_int(readiness_summary["due_count"])
        confirmation_required = ready_to_start and due_count > 0
        confirmation_status = "required" if confirmation_required else "not_required"
        courses = readiness_summary["courses"]
        if not isinstance(courses, list):
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_ERROR)
        confirmation_courses = [
            {
                **course,
                "requires_confirmation": confirmation_required,
            }
            for course in courses
            if confirmation_required
        ]
        confirmation_courses.sort(
            key=lambda course: (
                str(course["course_id"]),
                int(course["selected_class_time_index"]),
            )
        )
        return session_window_confirmation_preflight_safe_summary(
            {
                "status": confirmation_status,
                "session_id": readiness_summary["session_id"],
                "source_kind": readiness_summary["source_kind"],
                "clock_day_of_week": readiness_summary["clock_day_of_week"],
                "clock_local_time": readiness_summary["clock_local_time"],
                "course_count": readiness_summary["course_count"],
                "due_count": due_count,
                "ready_to_start": ready_to_start,
                "confirmation_required": confirmation_required,
                "confirmation_status": confirmation_status,
                "blocked_execution_count": (due_count if confirmation_required else 0),
                "courses": confirmation_courses,
            }
        )
    except (KeyError, TypeError, ValueError):
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_ERROR) from None


def session_window_confirmation_preflight_safe_summary(
    payload: dict[str, object],
) -> StoredSessionWindowConfirmationPreflightSummary:
    """Return only the Ticket 146 allowlisted JSON-safe fields."""

    try:
        courses = payload["courses"]
        if not isinstance(courses, list):
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_ERROR)
        safe_payload = {
            key: payload[key] for key in _SESSION_WINDOW_CONFIRMATION_PREFLIGHT_KEYS
        }
        if safe_payload["status"] != safe_payload["confirmation_status"]:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_ERROR)
        if safe_payload["confirmation_status"] not in _CONFIRMATION_STATUSES:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_ERROR)
        safe_payload["due_count"] = _non_negative_int(safe_payload["due_count"])
        safe_payload["blocked_execution_count"] = _non_negative_int(
            safe_payload["blocked_execution_count"]
        )
        safe_payload["ready_to_start"] = _bool_value(safe_payload["ready_to_start"])
        safe_payload["confirmation_required"] = _bool_value(
            safe_payload["confirmation_required"]
        )
        if not safe_payload["confirmation_required"]:
            if safe_payload["blocked_execution_count"] != 0:
                raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_ERROR)
            if courses:
                raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_ERROR)
        elif safe_payload["blocked_execution_count"] != safe_payload["due_count"]:
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_ERROR)
        safe_payload["courses"] = [_course_safe_summary(course) for course in courses]
        if safe_payload["confirmation_required"] and any(
            not course["requires_confirmation"] for course in safe_payload["courses"]
        ):
            raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_ERROR)
        return safe_payload
    except (KeyError, TypeError, ValueError):
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_ERROR) from None


def _course_safe_summary(payload: dict[str, object]) -> dict[str, object]:
    safe_course = {
        key: payload[key] for key in _SESSION_WINDOW_CONFIRMATION_PREFLIGHT_COURSE_KEYS
    }
    safe_course["requires_confirmation"] = _bool_value(
        safe_course["requires_confirmation"]
    )
    return safe_course


def _bool_value(value: object) -> bool:
    if not isinstance(value, bool):
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_ERROR)
    return value


def _non_negative_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_ERROR)
    return value
