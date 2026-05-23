"""Read-only stored session-window archive preflight composition."""

from __future__ import annotations

from pathlib import Path

from async_scholar.archive_export import (
    archive_export_preflight_summary_safe_summary,
    build_archive_export_preflight_summary_from_root,
)
from async_scholar.scheduled_start import ScheduledStartClock
from async_scholar.session_window import build_stored_session_window_plan_summary

STORED_SESSION_WINDOW_ARCHIVE_PREFLIGHT_ERROR = (
    "stored session window archive preflight could not be built"
)

StoredSessionWindowArchivePreflightSummary = dict[str, object]

_SESSION_WINDOW_ARCHIVE_PREFLIGHT_KEYS = (
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "archive_recovery_status",
    "archive_existing_count",
    "archive_missing_count",
    "archive_total_existing_size_bytes",
    "courses",
)
_SESSION_WINDOW_ARCHIVE_PREFLIGHT_COURSE_KEYS = (
    "course_id",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "stop_after_minutes",
    "enabled",
)


def build_session_window_archive_preflight_summary(
    stored_courses: dict[str, object],
    archive_root: str | Path,
    session_id: str,
    source_kind: str,
    clock: ScheduledStartClock,
    *,
    enabled: bool = True,
) -> StoredSessionWindowArchivePreflightSummary:
    """Combine a stored session-window plan with safe archive counts."""

    try:
        window_summary = build_stored_session_window_plan_summary(
            stored_courses,
            clock,
            session_id,
            source_kind,
            enabled=enabled,
        )
        safe_archive_root = _validate_existing_archive_root(archive_root)
        archive_summary = archive_export_preflight_summary_safe_summary(
            build_archive_export_preflight_summary_from_root(
                safe_archive_root,
                session_id,
            )
        )
        return session_window_archive_preflight_safe_summary(
            {
                **window_summary,
                "archive_recovery_status": _archive_recovery_status_from_counts(
                    _non_negative_int(archive_summary["existing_count"]),
                    _non_negative_int(archive_summary["missing_count"]),
                ),
                "archive_existing_count": archive_summary["existing_count"],
                "archive_missing_count": archive_summary["missing_count"],
                "archive_total_existing_size_bytes": archive_summary[
                    "total_existing_size_bytes"
                ],
            }
        )
    except (KeyError, TypeError, ValueError):
        raise ValueError(STORED_SESSION_WINDOW_ARCHIVE_PREFLIGHT_ERROR) from None


def session_window_archive_preflight_safe_summary(
    payload: dict[str, object],
) -> StoredSessionWindowArchivePreflightSummary:
    """Return only the Ticket 143 allowlisted JSON-safe fields."""

    try:
        courses = payload["courses"]
        if not isinstance(courses, list):
            raise ValueError(STORED_SESSION_WINDOW_ARCHIVE_PREFLIGHT_ERROR)
        safe_payload = {
            key: payload[key] for key in _SESSION_WINDOW_ARCHIVE_PREFLIGHT_KEYS
        }
        safe_payload["courses"] = [_course_safe_summary(course) for course in courses]
        return safe_payload
    except (KeyError, TypeError, ValueError):
        raise ValueError(STORED_SESSION_WINDOW_ARCHIVE_PREFLIGHT_ERROR) from None


def _course_safe_summary(payload: dict[str, object]) -> dict[str, object]:
    return {key: payload[key] for key in _SESSION_WINDOW_ARCHIVE_PREFLIGHT_COURSE_KEYS}


def _archive_recovery_status_from_counts(
    existing_count: int,
    missing_count: int,
) -> str:
    if existing_count == 0:
        return "empty"
    if missing_count == 0:
        return "complete"
    return "partial"


def _non_negative_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(STORED_SESSION_WINDOW_ARCHIVE_PREFLIGHT_ERROR)
    return value


def _validate_existing_archive_root(archive_root: str | Path) -> Path:
    if not isinstance(archive_root, (str, Path)):
        raise ValueError(STORED_SESSION_WINDOW_ARCHIVE_PREFLIGHT_ERROR)
    archive_root_text = str(archive_root)
    if archive_root_text != archive_root_text.strip() or not archive_root_text:
        raise ValueError(STORED_SESSION_WINDOW_ARCHIVE_PREFLIGHT_ERROR)
    if any(
        ord(character) < 32 or ord(character) == 127 for character in archive_root_text
    ):
        raise ValueError(STORED_SESSION_WINDOW_ARCHIVE_PREFLIGHT_ERROR)
    lowered_text = archive_root_text.lower()
    normalized_text = "".join(
        "\\" if character == "/" else character for character in archive_root_text
    )
    if (
        normalized_text.startswith("\\\\")
        or lowered_text.startswith("file:")
        or "://" in lowered_text
    ):
        raise ValueError(STORED_SESSION_WINDOW_ARCHIVE_PREFLIGHT_ERROR)
    candidate = Path(archive_root)
    if not candidate.exists() or not candidate.is_dir() or candidate.is_symlink():
        raise ValueError(STORED_SESSION_WINDOW_ARCHIVE_PREFLIGHT_ERROR)
    return candidate
