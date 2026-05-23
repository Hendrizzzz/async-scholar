from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from async_scholar.scheduled_start import ScheduledStartClock
from async_scholar.session_window_alert_preview import (
    STORED_SESSION_WINDOW_ALERT_PREVIEW_ERROR,
    build_session_window_alert_preview_summary,
    session_window_alert_preview_safe_summary,
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


def test_build_session_window_alert_preview_summary_due_only_sorted() -> None:
    summary = build_session_window_alert_preview_summary(
        _stored_courses(),
        "session-001",
        "file",
        ScheduledStartClock(day_of_week="monday", local_time="09:00"),
    )

    assert summary == {
        "alert_preview_count": 3,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 2,
        "courses": [
            {
                "alert_preview": {
                    "alert_kind": "participation_check",
                    "delivery": "none",
                    "requires_confirmation": True,
                },
                "course_id": "cs101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
                "stop_after_minutes": 90,
            },
            {
                "alert_preview": {
                    "alert_kind": "participation_check",
                    "delivery": "none",
                    "requires_confirmation": True,
                },
                "course_id": "cs101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 1,
                "stop_after_minutes": 75,
            },
            {
                "alert_preview": {
                    "alert_kind": "participation_check",
                    "delivery": "none",
                    "requires_confirmation": True,
                },
                "course_id": "math101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
                "stop_after_minutes": 60,
            },
        ],
        "due_count": 3,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "due",
    }
    _assert_alert_preview_summary_is_safe(summary)


def test_build_session_window_alert_preview_summary_waiting_and_disabled() -> None:
    waiting = build_session_window_alert_preview_summary(
        _stored_courses(),
        "session-001",
        "mic",
        ScheduledStartClock(day_of_week="tuesday", local_time="09:00"),
    )
    disabled = build_session_window_alert_preview_summary(
        _stored_courses(),
        "session-001",
        "file",
        ScheduledStartClock(day_of_week="monday", local_time="09:00"),
        enabled=False,
    )

    assert waiting["status"] == "waiting"
    assert waiting["due_count"] == 0
    assert waiting["alert_preview_count"] == 0
    assert waiting["courses"] == []
    assert disabled == {
        "alert_preview_count": 0,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 2,
        "courses": [],
        "due_count": 0,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "disabled",
    }
    _assert_alert_preview_summary_is_safe(waiting)
    _assert_alert_preview_summary_is_safe(disabled)


def test_session_window_alert_preview_safe_summary_strips_private_fields() -> None:
    safe = session_window_alert_preview_safe_summary(
        {
            "status": "due",
            "session_id": "session-001",
            "source_kind": "file",
            "clock_day_of_week": "monday",
            "clock_local_time": "09:00",
            "course_count": 1,
            "due_count": 1,
            "alert_preview_count": 1,
            "notification_title": "Private title",
            "notification_body": "Secret answer",
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
                    "title": "Confidential Systems",
                    "meeting_url": "https://meet.example.edu/token-secret",
                    "alert_preview": {
                        "alert_kind": "participation_check",
                        "delivery": "none",
                        "requires_confirmation": True,
                        "target": "private-device-token",
                        "body": "notification payload",
                    },
                }
            ],
        }
    )

    assert set(safe) == {
        "alert_preview_count",
        "clock_day_of_week",
        "clock_local_time",
        "course_count",
        "courses",
        "due_count",
        "session_id",
        "source_kind",
        "status",
    }
    assert set(safe["courses"][0]) == {
        "alert_preview",
        "course_id",
        "due",
        "enabled",
        "minutes_until_start",
        "scheduled_day_of_week",
        "scheduled_local_start_time",
        "selected_class_time_index",
        "stop_after_minutes",
    }
    assert set(safe["courses"][0]["alert_preview"]) == {
        "alert_kind",
        "delivery",
        "requires_confirmation",
    }
    _assert_alert_preview_summary_is_safe(safe)


def test_session_window_alert_preview_safe_summary_requires_fixed_metadata() -> None:
    with pytest.raises(ValueError) as exc_info:
        session_window_alert_preview_safe_summary(
            {
                "status": "due",
                "session_id": "session-001",
                "source_kind": "file",
                "clock_day_of_week": "monday",
                "clock_local_time": "09:00",
                "course_count": 1,
                "due_count": 1,
                "alert_preview_count": 1,
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
                        "alert_preview": {
                            "alert_kind": "private-token",
                            "delivery": "none",
                            "requires_confirmation": True,
                        },
                    }
                ],
            }
        )

    assert str(exc_info.value) == STORED_SESSION_WINDOW_ALERT_PREVIEW_ERROR


@pytest.mark.parametrize(
    ("stored_courses", "source_kind"),
    [
        ({}, "file"),
        ({"course_count": 1, "courses": []}, "file"),
        (_stored_courses(), "browser"),
    ],
)
def test_build_session_window_alert_preview_summary_sanitizes_bad_inputs(
    stored_courses: dict[str, object],
    source_kind: str,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_session_window_alert_preview_summary(
            stored_courses,
            "session-001",
            source_kind,
            ScheduledStartClock(day_of_week="monday", local_time="09:00"),
        )

    assert str(exc_info.value) == STORED_SESSION_WINDOW_ALERT_PREVIEW_ERROR


def test_session_window_alert_preview_source_has_no_execution_surfaces() -> None:
    import async_scholar.session_window_alert_preview as alert_preview

    source = Path(alert_preview.__file__).read_text(encoding="utf-8").lower()
    assert "list_course_schedule_session_window_inputs" not in source
    assert "build_stored_session_window_plan_summary" in source
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
        alert_preview.build_session_window_alert_preview_summary
    )
    assert "build_stored_session_window_plan_summary" in helper_source


def _assert_alert_preview_summary_is_safe(payload: dict[str, object]) -> None:
    combined_output = repr(payload).lower()
    for forbidden_fragment in (
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
        "path",
        "sqlite",
        "traceback",
    ):
        assert forbidden_fragment not in combined_output
