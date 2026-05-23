from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from async_scholar.scheduled_start import ScheduledStartClock
from async_scholar.session_window_archive_preflight import (
    STORED_SESSION_WINDOW_ARCHIVE_PREFLIGHT_ERROR,
    build_session_window_archive_preflight_summary,
    session_window_archive_preflight_safe_summary,
)


def _stored_courses() -> dict[str, object]:
    return {
        "course_count": 1,
        "courses": [
            {
                "course_id": "cs101",
                "class_times": [
                    {
                        "selected_class_time_index": 0,
                        "scheduled_day_of_week": "monday",
                        "scheduled_local_start_time": "09:00",
                        "stop_after_minutes": 75,
                    }
                ],
            }
        ],
    }


def test_build_session_window_archive_preflight_summary_due_partial(
    tmp_path: Path,
) -> None:
    session_dir = tmp_path / "session-001"
    session_dir.mkdir()
    (session_dir / "events.jsonl").write_text("private token payload", encoding="utf-8")
    (session_dir / "reviewer.md").write_text(
        "private reviewer payload", encoding="utf-8"
    )

    summary = build_session_window_archive_preflight_summary(
        _stored_courses(),
        tmp_path,
        "session-001",
        "file",
        ScheduledStartClock(day_of_week="monday", local_time="09:00"),
    )

    assert summary == {
        "archive_existing_count": 2,
        "archive_missing_count": 5,
        "archive_recovery_status": "partial",
        "archive_total_existing_size_bytes": len(b"private token payload")
        + len(b"private reviewer payload"),
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 1,
        "courses": [
            {
                "course_id": "cs101",
                "due": True,
                "enabled": True,
                "minutes_until_start": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "selected_class_time_index": 0,
                "stop_after_minutes": 75,
            }
        ],
        "due_count": 1,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "due",
    }
    _assert_preflight_summary_is_safe(summary)


def test_build_session_window_archive_preflight_summary_disabled_empty_complete(
    tmp_path: Path,
) -> None:
    session_dir = tmp_path / "session-001"
    session_dir.mkdir()
    for filename in (
        "transcript.jsonl",
        "transcript.md",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
        "runtime.jsonl",
        "benchmark-report.json",
    ):
        (session_dir / filename).write_text("{}", encoding="utf-8")

    summary = build_session_window_archive_preflight_summary(
        _stored_courses(),
        tmp_path,
        "session-001",
        "mic",
        ScheduledStartClock(day_of_week="monday", local_time="09:00"),
        enabled=False,
    )

    assert summary["status"] == "disabled"
    assert summary["due_count"] == 0
    assert summary["courses"] == []
    assert summary["archive_existing_count"] == 7
    assert summary["archive_missing_count"] == 0
    assert summary["archive_recovery_status"] == "complete"


def test_session_window_archive_preflight_safe_summary_strips_private_fields() -> None:
    safe = session_window_archive_preflight_safe_summary(
        {
            "status": "due",
            "session_id": "session-001",
            "source_kind": "file",
            "clock_day_of_week": "monday",
            "clock_local_time": "09:00",
            "course_count": 1,
            "due_count": 1,
            "archive_recovery_status": "partial",
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
                    "title": "Confidential Systems",
                    "meeting_url": "https://meet.example.edu/token-secret",
                }
            ],
        }
    )

    assert set(safe) == {
        "archive_existing_count",
        "archive_missing_count",
        "archive_recovery_status",
        "archive_total_existing_size_bytes",
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
        "course_id",
        "due",
        "enabled",
        "minutes_until_start",
        "scheduled_day_of_week",
        "scheduled_local_start_time",
        "selected_class_time_index",
        "stop_after_minutes",
    }
    _assert_preflight_summary_is_safe(safe)


@pytest.mark.parametrize(
    ("stored_courses", "archive_root", "session_id", "source_kind"),
    [
        ({}, ".", "session-001", "file"),
        (_stored_courses(), ".", "../private", "file"),
        (_stored_courses(), ".", "session-001", "browser"),
    ],
)
def test_build_session_window_archive_preflight_summary_sanitizes_bad_inputs(
    stored_courses: dict[str, object],
    archive_root: str,
    session_id: str,
    source_kind: str,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_session_window_archive_preflight_summary(
            stored_courses,
            archive_root,
            session_id,
            source_kind,
            ScheduledStartClock(day_of_week="monday", local_time="09:00"),
        )

    assert str(exc_info.value) == STORED_SESSION_WINDOW_ARCHIVE_PREFLIGHT_ERROR


def test_session_window_archive_preflight_source_has_no_execution_surfaces() -> None:
    import async_scholar.session_window_archive_preflight as preflight

    source = Path(preflight.__file__).read_text(encoding="utf-8").lower()
    assert "list_course_schedule_session_window_inputs" not in source
    assert "build_stored_session_window_plan_summary" in source
    assert "build_archive_export_preflight_summary_from_root" in source
    assert "archive_export_preflight_summary_safe_summary" in source
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
        preflight.build_session_window_archive_preflight_summary
    )
    assert "build_stored_session_window_plan_summary" in helper_source


def _assert_preflight_summary_is_safe(payload: dict[str, object]) -> None:
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
        "transcript.jsonl",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
        "runtime.jsonl",
        "benchmark-report.json",
        "session_dir",
        "artifacts",
        "filename",
        "path",
        "sqlite",
        "traceback",
    ):
        assert forbidden_fragment not in combined_output
