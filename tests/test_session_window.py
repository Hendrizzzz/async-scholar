from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from async_scholar.scheduled_start import ScheduledStartClock
from async_scholar.session_window import (
    STORED_SESSION_WINDOW_PLAN_ERROR,
    build_stored_session_window_plan_summary,
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
                        "selected_class_time_index": 0,
                        "scheduled_day_of_week": "monday",
                        "scheduled_local_start_time": "09:00",
                        "stop_after_minutes": 90,
                    },
                    {
                        "selected_class_time_index": 1,
                        "scheduled_day_of_week": "monday",
                        "scheduled_local_start_time": "09:00",
                        "stop_after_minutes": 75,
                    },
                ],
            },
        ],
    }


def test_build_stored_session_window_plan_summary_due_only_sorted() -> None:
    summary = build_stored_session_window_plan_summary(
        _stored_courses(),
        ScheduledStartClock(day_of_week="monday", local_time="09:00"),
        "session-001",
        "file",
    )

    assert summary == {
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 2,
        "courses": [
            {
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


def test_build_stored_session_window_plan_summary_waiting_and_disabled() -> None:
    waiting = build_stored_session_window_plan_summary(
        _stored_courses(),
        ScheduledStartClock(day_of_week="tuesday", local_time="09:00"),
        "session-001",
        "mic",
    )
    disabled = build_stored_session_window_plan_summary(
        _stored_courses(),
        ScheduledStartClock(day_of_week="monday", local_time="09:00"),
        "session-001",
        "file",
        enabled=False,
    )

    assert waiting["status"] == "waiting"
    assert waiting["due_count"] == 0
    assert waiting["courses"] == []
    assert disabled == {
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 2,
        "courses": [],
        "due_count": 0,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "disabled",
    }


@pytest.mark.parametrize(
    ("stored_courses", "source_kind"),
    [
        ({}, "file"),
        ({"course_count": 1, "courses": []}, "file"),
        (
            {
                "course_count": 1,
                "courses": [
                    {
                        "course_id": "cs101",
                        "class_times": [
                            {
                                "selected_class_time_index": 0,
                                "scheduled_day_of_week": "monday",
                                "scheduled_local_start_time": "09:00",
                                "stop_after_minutes": -1,
                            }
                        ],
                    }
                ],
            },
            "file",
        ),
        (_stored_courses(), "browser"),
    ],
)
def test_build_stored_session_window_plan_summary_sanitizes_bad_inputs(
    stored_courses: dict[str, object],
    source_kind: str,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_stored_session_window_plan_summary(
            stored_courses,
            ScheduledStartClock(day_of_week="monday", local_time="09:00"),
            "session-001",
            source_kind,
        )

    assert str(exc_info.value) == STORED_SESSION_WINDOW_PLAN_ERROR


def test_session_window_source_has_no_execution_or_io_surfaces() -> None:
    import async_scholar.session_window as session_window

    source = Path(session_window.__file__).read_text(encoding="utf-8").lower()
    assert "scheduled_start" in source
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
        "archive_export",
        "archive_delete",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
    ):
        assert forbidden_fragment not in source

    helper_source = inspect.getsource(
        session_window.build_stored_session_window_plan_summary
    )
    assert "build_scheduled_start_due_list_summary" in helper_source
