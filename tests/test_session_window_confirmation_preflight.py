from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from async_scholar.scheduled_start import ScheduledStartClock
from async_scholar.session_window_confirmation_preflight import (
    STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_ERROR,
    build_session_window_confirmation_preflight_summary,
    session_window_confirmation_preflight_safe_summary,
)


def _stored_courses() -> dict[str, object]:
    return {
        "course_count": 2,
        "courses": [
            {
                "course_id": "math101",
                "class_times": [
                    {
                        "selected_class_time_index": 0,
                        "scheduled_day_of_week": "monday",
                        "scheduled_local_start_time": "09:00",
                        "stop_after_minutes": 60,
                    }
                ],
            },
            {
                "course_id": "cs101",
                "class_times": [
                    {
                        "selected_class_time_index": 1,
                        "scheduled_day_of_week": "monday",
                        "scheduled_local_start_time": "09:00",
                        "stop_after_minutes": 75,
                    },
                    {
                        "selected_class_time_index": 0,
                        "scheduled_day_of_week": "monday",
                        "scheduled_local_start_time": "09:00",
                        "stop_after_minutes": 90,
                    },
                ],
            },
        ],
    }


def test_build_session_window_confirmation_preflight_summary_due_required_sorted(
    tmp_path: Path,
) -> None:
    session_dir = tmp_path / "session-001"
    session_dir.mkdir()
    (session_dir / "events.jsonl").write_text(
        "private event token secret auth profile payload",
        encoding="utf-8",
    )

    summary = build_session_window_confirmation_preflight_summary(
        _stored_courses(),
        tmp_path,
        "session-001",
        "file",
        ScheduledStartClock(day_of_week="monday", local_time="09:00"),
    )

    assert summary == {
        "blocked_execution_count": 3,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "confirmation_required": True,
        "confirmation_status": "required",
        "course_count": 2,
        "courses": [
            {
                "course_id": "cs101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "requires_confirmation": True,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
                "stop_after_minutes": 90,
            },
            {
                "course_id": "cs101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "requires_confirmation": True,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 1,
                "stop_after_minutes": 75,
            },
            {
                "course_id": "math101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "requires_confirmation": True,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
                "stop_after_minutes": 60,
            },
        ],
        "due_count": 3,
        "ready_to_start": True,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "required",
    }
    _assert_confirmation_summary_is_safe(summary)


def test_build_session_window_confirmation_preflight_summary_waiting_and_disabled(
    tmp_path: Path,
) -> None:
    (tmp_path / "session-001").mkdir()

    waiting = build_session_window_confirmation_preflight_summary(
        _stored_courses(),
        tmp_path,
        "session-001",
        "mic",
        ScheduledStartClock(day_of_week="tuesday", local_time="09:00"),
    )
    disabled = build_session_window_confirmation_preflight_summary(
        _stored_courses(),
        tmp_path,
        "session-001",
        "file",
        ScheduledStartClock(day_of_week="monday", local_time="09:00"),
        enabled=False,
    )

    assert waiting == {
        "blocked_execution_count": 0,
        "clock_day_of_week": "tuesday",
        "clock_local_time": "09:00",
        "confirmation_required": False,
        "confirmation_status": "not_required",
        "course_count": 2,
        "courses": [],
        "due_count": 0,
        "ready_to_start": False,
        "session_id": "session-001",
        "source_kind": "mic",
        "status": "not_required",
    }
    assert disabled == {
        "blocked_execution_count": 0,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "confirmation_required": False,
        "confirmation_status": "disabled",
        "course_count": 2,
        "courses": [],
        "due_count": 0,
        "ready_to_start": False,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "disabled",
    }
    _assert_confirmation_summary_is_safe(waiting)
    _assert_confirmation_summary_is_safe(disabled)


def test_session_window_confirmation_preflight_safe_summary_strips_private_fields() -> (
    None
):
    safe = session_window_confirmation_preflight_safe_summary(
        {
            "status": "required",
            "session_id": "session-001",
            "source_kind": "file",
            "clock_day_of_week": "monday",
            "clock_local_time": "09:00",
            "course_count": 1,
            "due_count": 1,
            "ready_to_start": True,
            "confirmation_required": True,
            "confirmation_status": "required",
            "blocked_execution_count": 1,
            "alert_preview_count": 1,
            "archive_existing_count": 1,
            "archive_missing_count": 6,
            "archive_total_existing_size_bytes": 2,
            "session_dir": "session-001",
            "artifacts": [{"filename": "events.jsonl", "size_bytes": 2}],
            "courses": [
                {
                    "course_id": "cs101",
                    "selected_class_time_index": 0,
                    "scheduled_day_of_week": "monday",
                    "scheduled_local_start_time": "09:00",
                    "due": True,
                    "minutes_until_start": 0,
                    "stop_after_minutes": 75,
                    "enabled": True,
                    "requires_confirmation": True,
                    "title": "Confidential Systems",
                    "meeting_url": "https://meet.example.edu/token-secret",
                    "alert_preview": {
                        "alert_kind": "participation_check",
                        "delivery": "none",
                        "requires_confirmation": True,
                    },
                }
            ],
        }
    )

    assert set(safe) == {
        "blocked_execution_count",
        "clock_day_of_week",
        "clock_local_time",
        "confirmation_required",
        "confirmation_status",
        "course_count",
        "courses",
        "due_count",
        "ready_to_start",
        "session_id",
        "source_kind",
        "status",
    }
    assert set(safe["courses"][0]) == {
        "course_id",
        "due",
        "enabled",
        "minutes_until_start",
        "requires_confirmation",
        "scheduled_day_of_week",
        "scheduled_local_start_time",
        "selected_class_time_index",
        "stop_after_minutes",
    }
    _assert_confirmation_summary_is_safe(safe)


@pytest.mark.parametrize(
    "payload_update",
    [
        {"status": "due"},
        {"confirmation_status": "waiting"},
        {"blocked_execution_count": 0},
        {"confirmation_required": False},
    ],
)
def test_session_window_confirmation_preflight_safe_summary_requires_fixed_policy(
    payload_update: dict[str, object],
) -> None:
    payload: dict[str, object] = {
        "status": "required",
        "session_id": "session-001",
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
                "course_id": "cs101",
                "selected_class_time_index": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "due": True,
                "minutes_until_start": 0,
                "stop_after_minutes": 75,
                "enabled": True,
                "requires_confirmation": True,
            }
        ],
    }
    payload.update(payload_update)

    with pytest.raises(ValueError) as exc_info:
        session_window_confirmation_preflight_safe_summary(payload)

    assert str(exc_info.value) == STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_ERROR


@pytest.mark.parametrize(
    ("stored_courses", "archive_root", "session_id", "source_kind"),
    [
        ({}, ".", "session-001", "file"),
        (_stored_courses(), ".", "../private", "file"),
        (_stored_courses(), ".", "session-001", "browser"),
    ],
)
def test_build_session_window_confirmation_preflight_summary_sanitizes_bad_inputs(
    stored_courses: dict[str, object],
    archive_root: str,
    session_id: str,
    source_kind: str,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_session_window_confirmation_preflight_summary(
            stored_courses,
            archive_root,
            session_id,
            source_kind,
            ScheduledStartClock(day_of_week="monday", local_time="09:00"),
        )

    assert str(exc_info.value) == STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_ERROR


def test_session_window_confirmation_preflight_source_has_no_execution_surfaces() -> (
    None
):
    import async_scholar.session_window_confirmation_preflight as preflight

    source = Path(preflight.__file__).read_text(encoding="utf-8").lower()
    assert "list_course_schedule_session_window_inputs" not in source
    assert "build_session_window_readiness_preflight_summary" in source
    assert "alert_preview_count" not in source
    assert "archive_existing_count" not in source
    assert "archive_missing_count" not in source
    assert "archive_total_existing_size_bytes" not in source
    for forbidden_fragment in (
        "sqlite",
        "connect(",
        "open(",
        "read_text",
        "write_text",
        "datetime",
        "now(",
        "sleep",
        "timer",
        "threading",
        "asyncio",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "telegram",
        "desktop_notifier",
        "notification_title",
        "notification_body",
        "execute_archive",
        "execute_archive_delete",
        "execute_archive_export",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
    ):
        assert forbidden_fragment not in source

    helper_source = inspect.getsource(
        preflight.build_session_window_confirmation_preflight_summary
    )
    assert "build_session_window_readiness_preflight_summary" in helper_source


def _assert_confirmation_summary_is_safe(payload: dict[str, object]) -> None:
    combined_output = repr(payload).lower()
    for forbidden_fragment in (
        "alert_preview",
        "archive_",
        "title",
        "meeting",
        "meet.example",
        "timezone",
        "confidential",
        "instructor",
        "token",
        "secret",
        "auth",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "browser",
        "notification",
        "target",
        "body",
        "session_dir",
        "artifacts",
        "filename",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
        "runtime.jsonl",
        "benchmark-report.json",
        "path",
        "sqlite",
        "traceback",
        "live delivery",
        "live-delivery",
        "live_delivery",
        "scheduler execution",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined_output
