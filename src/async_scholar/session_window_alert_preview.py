"""Metadata-only stored session-window alert preview composition."""

from __future__ import annotations

from async_scholar.scheduled_start import ScheduledStartClock
from async_scholar.session_window import build_stored_session_window_plan_summary

STORED_SESSION_WINDOW_ALERT_PREVIEW_ERROR = (
    "stored session window alert preview could not be built"
)

StoredSessionWindowAlertPreviewSummary = dict[str, object]

_ALERT_PREVIEW = {
    "alert_kind": "participation_check",
    "delivery": "none",
    "requires_confirmation": True,
}
_SESSION_WINDOW_ALERT_PREVIEW_KEYS = (
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "alert_preview_count",
    "courses",
)
_SESSION_WINDOW_ALERT_PREVIEW_COURSE_KEYS = (
    "course_id",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "stop_after_minutes",
    "enabled",
    "alert_preview",
)
_ALERT_PREVIEW_KEYS = (
    "alert_kind",
    "delivery",
    "requires_confirmation",
)


def build_session_window_alert_preview_summary(
    stored_courses: dict[str, object],
    session_id: str,
    source_kind: str,
    clock: ScheduledStartClock,
    *,
    enabled: bool = True,
) -> StoredSessionWindowAlertPreviewSummary:
    """Attach fixed non-delivery alert metadata to due stored session windows."""

    try:
        window_summary = build_stored_session_window_plan_summary(
            stored_courses,
            clock,
            session_id,
            source_kind,
            enabled=enabled,
        )
        if not enabled:
            return session_window_alert_preview_safe_summary(
                {
                    **window_summary,
                    "due_count": 0,
                    "alert_preview_count": 0,
                    "courses": [],
                    "status": "disabled",
                }
            )
        courses = window_summary["courses"]
        if not isinstance(courses, list):
            raise ValueError(STORED_SESSION_WINDOW_ALERT_PREVIEW_ERROR)
        preview_courses = [
            {
                **course,
                "alert_preview": dict(_ALERT_PREVIEW),
            }
            for course in courses
        ]
        preview_courses.sort(
            key=lambda course: (
                str(course["course_id"]),
                int(course["selected_class_time_index"]),
            )
        )
        return session_window_alert_preview_safe_summary(
            {
                **window_summary,
                "due_count": len(preview_courses),
                "alert_preview_count": len(preview_courses),
                "courses": preview_courses,
            }
        )
    except (KeyError, TypeError, ValueError):
        raise ValueError(STORED_SESSION_WINDOW_ALERT_PREVIEW_ERROR) from None


def session_window_alert_preview_safe_summary(
    payload: dict[str, object],
) -> StoredSessionWindowAlertPreviewSummary:
    """Return only the Ticket 144 allowlisted JSON-safe fields."""

    try:
        courses = payload["courses"]
        if not isinstance(courses, list):
            raise ValueError(STORED_SESSION_WINDOW_ALERT_PREVIEW_ERROR)
        safe_payload = {key: payload[key] for key in _SESSION_WINDOW_ALERT_PREVIEW_KEYS}
        safe_payload["courses"] = [_course_safe_summary(course) for course in courses]
        return safe_payload
    except (KeyError, TypeError, ValueError):
        raise ValueError(STORED_SESSION_WINDOW_ALERT_PREVIEW_ERROR) from None


def _course_safe_summary(payload: dict[str, object]) -> dict[str, object]:
    safe_course = {
        key: payload[key] for key in _SESSION_WINDOW_ALERT_PREVIEW_COURSE_KEYS
    }
    alert_preview = safe_course["alert_preview"]
    if not isinstance(alert_preview, dict):
        raise ValueError(STORED_SESSION_WINDOW_ALERT_PREVIEW_ERROR)
    safe_course["alert_preview"] = {
        key: alert_preview[key] for key in _ALERT_PREVIEW_KEYS
    }
    if safe_course["alert_preview"] != _ALERT_PREVIEW:
        raise ValueError(STORED_SESSION_WINDOW_ALERT_PREVIEW_ERROR)
    return safe_course
