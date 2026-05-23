from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from async_scholar.session_window_start_authorization import (
    STORED_SESSION_WINDOW_START_AUTHORIZATION_ERROR,
    build_session_window_start_authorization_summary,
    session_window_start_authorization_safe_summary,
)


def _confirmed_response() -> dict[str, object]:
    return {
        "status": "confirmed",
        "session_id": "session-001",
        "source_kind": "file",
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 2,
        "due_count": 3,
        "ready_to_start": True,
        "confirmation_required": True,
        "confirmation_status": "required",
        "confirmation_response": "confirmed",
        "confirmation_verified": True,
        "confirmed_start_count": 3,
        "blocked_execution_count": 0,
        "courses": [
            {
                "course_id": "math101",
                "selected_class_time_index": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "due": True,
                "minutes_until_start": 0,
                "stop_after_minutes": 60,
                "enabled": True,
                "requires_confirmation": True,
                "confirmation_response": "confirmed",
            },
            {
                "course_id": "cs101",
                "selected_class_time_index": 1,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "due": True,
                "minutes_until_start": 0,
                "stop_after_minutes": 75,
                "enabled": True,
                "requires_confirmation": True,
                "confirmation_response": "confirmed",
            },
            {
                "course_id": "cs101",
                "selected_class_time_index": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "due": True,
                "minutes_until_start": 0,
                "stop_after_minutes": 90,
                "enabled": True,
                "requires_confirmation": True,
                "confirmation_response": "confirmed",
            },
        ],
    }


def _declined_response() -> dict[str, object]:
    payload = _confirmed_response()
    payload.update(
        {
            "status": "declined",
            "confirmation_response": "declined",
            "confirmation_verified": False,
            "confirmed_start_count": 0,
            "blocked_execution_count": 3,
        }
    )
    courses = payload["courses"]
    assert isinstance(courses, list)
    payload["courses"] = [
        {**course, "confirmation_response": "declined"} for course in courses
    ]
    return payload


def _not_required_response() -> dict[str, object]:
    return {
        "status": "not_required",
        "session_id": "session-001",
        "source_kind": "mic",
        "clock_day_of_week": "tuesday",
        "clock_local_time": "09:00",
        "course_count": 2,
        "due_count": 0,
        "ready_to_start": False,
        "confirmation_required": False,
        "confirmation_status": "not_required",
        "confirmation_response": "confirmed",
        "confirmation_verified": False,
        "confirmed_start_count": 0,
        "blocked_execution_count": 0,
        "courses": [],
    }


def _disabled_response() -> dict[str, object]:
    payload = _not_required_response()
    payload.update(
        {
            "status": "disabled",
            "source_kind": "file",
            "clock_day_of_week": "monday",
            "confirmation_status": "disabled",
            "confirmation_response": "declined",
        }
    )
    return payload


def test_build_start_authorization_confirmed_required_path() -> None:
    summary = build_session_window_start_authorization_summary(_confirmed_response())

    assert summary == {
        "status": "authorized",
        "session_id": "session-001",
        "source_kind": "file",
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 2,
        "due_count": 3,
        "ready_to_start": True,
        "confirmation_required": True,
        "confirmation_status": "required",
        "confirmation_response": "confirmed",
        "confirmation_verified": True,
        "authorized": True,
        "authorized_start_count": 3,
        "blocked_start_count": 0,
        "block_reason": "none",
        "courses": [
            {
                "course_id": "cs101",
                "selected_class_time_index": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "due": True,
                "minutes_until_start": 0,
                "stop_after_minutes": 90,
                "enabled": True,
                "requires_confirmation": True,
                "confirmation_response": "confirmed",
                "authorized": True,
            },
            {
                "course_id": "cs101",
                "selected_class_time_index": 1,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "due": True,
                "minutes_until_start": 0,
                "stop_after_minutes": 75,
                "enabled": True,
                "requires_confirmation": True,
                "confirmation_response": "confirmed",
                "authorized": True,
            },
            {
                "course_id": "math101",
                "selected_class_time_index": 0,
                "scheduled_day_of_week": "monday",
                "scheduled_local_start_time": "09:00",
                "due": True,
                "minutes_until_start": 0,
                "stop_after_minutes": 60,
                "enabled": True,
                "requires_confirmation": True,
                "confirmation_response": "confirmed",
                "authorized": True,
            },
        ],
    }
    assert json.loads(json.dumps(summary)) == summary
    _assert_authorization_summary_is_safe(summary)


def test_build_start_authorization_declined_is_blocked_without_courses() -> None:
    summary = build_session_window_start_authorization_summary(_declined_response())

    assert summary["status"] == "blocked"
    assert summary["authorized"] is False
    assert summary["authorized_start_count"] == 0
    assert summary["blocked_start_count"] == 3
    assert summary["block_reason"] == "confirmation_declined"
    assert summary["courses"] == []
    _assert_authorization_summary_is_safe(summary)


def test_builder_rejects_declined_course_count_mismatch() -> None:
    payload = _declined_response()
    payload["course_count"] = 99

    with pytest.raises(ValueError) as exc_info:
        build_session_window_start_authorization_summary(payload)

    assert str(exc_info.value) == STORED_SESSION_WINDOW_START_AUTHORIZATION_ERROR


def test_builder_rejects_declined_course_response_mismatch() -> None:
    payload = _declined_response()
    courses = payload["courses"]
    assert isinstance(courses, list)
    courses[0] = {**courses[0], "confirmation_response": "confirmed"}

    with pytest.raises(ValueError) as exc_info:
        build_session_window_start_authorization_summary(payload)

    assert str(exc_info.value) == STORED_SESSION_WINDOW_START_AUTHORIZATION_ERROR


@pytest.mark.parametrize(
    ("response", "expected_status", "expected_reason"),
    [
        (_disabled_response(), "disabled", "disabled"),
        (_not_required_response(), "not_required", "confirmation_not_required"),
    ],
)
def test_build_start_authorization_non_required_paths_have_no_courses(
    response: dict[str, object],
    expected_status: str,
    expected_reason: str,
) -> None:
    summary = build_session_window_start_authorization_summary(response)

    assert summary["status"] == expected_status
    assert summary["authorized"] is False
    assert summary["authorized_start_count"] == 0
    assert summary["blocked_start_count"] == 0
    assert summary["block_reason"] == expected_reason
    assert summary["courses"] == []
    _assert_authorization_summary_is_safe(summary)


@pytest.mark.parametrize(
    "payload_update",
    [
        {"status": "declined"},
        {"confirmation_status": "not_required"},
        {"confirmation_response": "declined"},
        {"confirmation_verified": False},
        {"confirmed_start_count": 2},
        {"blocked_execution_count": 1},
        {"course_count": 999},
        {"ready_to_start": False},
        {"confirmation_required": False},
        {"due_count": 0},
        {"due_count": True},
        {"session_id": "..\\private\\session"},
        {"clock_local_time": "24:00"},
    ],
)
def test_builder_rejects_malformed_inconsistent_confirmed_response(
    payload_update: dict[str, object],
) -> None:
    payload = _confirmed_response()
    payload.update(payload_update)

    with pytest.raises(ValueError) as exc_info:
        build_session_window_start_authorization_summary(payload)

    assert str(exc_info.value) == STORED_SESSION_WINDOW_START_AUTHORIZATION_ERROR


@pytest.mark.parametrize(
    "course_update",
    [
        {"course_id": "../private"},
        {"selected_class_time_index": -1},
        {"scheduled_day_of_week": "funday"},
        {"scheduled_local_start_time": "24:00"},
        {"due": False},
        {"minutes_until_start": 1},
        {"stop_after_minutes": 0},
        {"enabled": False},
        {"requires_confirmation": False},
        {"confirmation_response": "declined"},
        {"meeting_url": "https://meet.example.edu/private-token"},
    ],
)
def test_builder_rejects_malformed_course_rows(
    course_update: dict[str, object],
) -> None:
    payload = _confirmed_response()
    courses = payload["courses"]
    assert isinstance(courses, list)
    first_course = dict(courses[0])
    first_course.update(course_update)
    courses[0] = first_course

    with pytest.raises(ValueError) as exc_info:
        build_session_window_start_authorization_summary(payload)

    assert str(exc_info.value) == STORED_SESSION_WINDOW_START_AUTHORIZATION_ERROR


def test_builder_rejects_missing_extra_private_fields_safely() -> None:
    for payload in (
        {
            key: value
            for key, value in _confirmed_response().items()
            if key != "courses"
        },
        {
            **_confirmed_response(),
            "private_response_text": "confirmed from C:\\Users\\student\\cookie.txt",
        },
    ):
        with pytest.raises(ValueError) as exc_info:
            build_session_window_start_authorization_summary(payload)

        assert str(exc_info.value) == STORED_SESSION_WINDOW_START_AUTHORIZATION_ERROR
        assert "cookie" not in str(exc_info.value)
        assert "C:\\Users" not in str(exc_info.value)


def test_builder_rejects_duplicate_course_rows() -> None:
    payload = _confirmed_response()
    courses = payload["courses"]
    assert isinstance(courses, list)
    courses[1] = dict(courses[2])

    with pytest.raises(ValueError) as exc_info:
        build_session_window_start_authorization_summary(payload)

    assert str(exc_info.value) == STORED_SESSION_WINDOW_START_AUTHORIZATION_ERROR


def test_builder_sorts_authorized_courses_deterministically() -> None:
    summary = build_session_window_start_authorization_summary(_confirmed_response())

    assert [
        (course["course_id"], course["selected_class_time_index"])
        for course in summary["courses"]
    ] == [("cs101", 0), ("cs101", 1), ("math101", 0)]


def test_safe_summary_rejects_extra_private_fields_instead_of_stripping() -> None:
    payload = {
        **build_session_window_start_authorization_summary(_confirmed_response()),
        "archive_root": "C:\\Users\\student\\archive",
    }

    with pytest.raises(ValueError) as exc_info:
        session_window_start_authorization_safe_summary(payload)

    assert str(exc_info.value) == STORED_SESSION_WINDOW_START_AUTHORIZATION_ERROR


def test_safe_summary_rejects_authorized_course_count_mismatch() -> None:
    payload = build_session_window_start_authorization_summary(_confirmed_response())
    payload["course_count"] = 999

    with pytest.raises(ValueError) as exc_info:
        session_window_start_authorization_safe_summary(payload)

    assert str(exc_info.value) == STORED_SESSION_WINDOW_START_AUTHORIZATION_ERROR


@pytest.mark.parametrize(
    "payload_update",
    [
        {"status": "authorized", "block_reason": "confirmation_declined"},
        {"status": "blocked", "authorized": True},
        {"status": "blocked", "blocked_start_count": 0},
        {"status": "not_required", "ready_to_start": True},
        {"status": "disabled", "confirmation_status": "not_required"},
    ],
)
def test_safe_summary_revalidates_authorization_policy(
    payload_update: dict[str, object],
) -> None:
    payload = build_session_window_start_authorization_summary(_declined_response())
    payload.update(payload_update)

    with pytest.raises(ValueError) as exc_info:
        session_window_start_authorization_safe_summary(payload)

    assert str(exc_info.value) == STORED_SESSION_WINDOW_START_AUTHORIZATION_ERROR


def test_source_has_no_execution_persistence_cli_or_dependency_behavior() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "async_scholar"
        / "session_window_start_authorization.py"
    )
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "argparse",
        "asyncio",
        "httpx",
        "os",
        "pathlib",
        "requests",
        "shutil",
        "socket",
        "sqlite3",
        "subprocess",
        "threading",
        "time",
        "urllib",
        "webbrowser",
    }
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(
                alias.name.split(".", maxsplit=1)[0] for alias in node.names
            )
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", maxsplit=1)[0])
    assert imported_roots.isdisjoint(forbidden_import_roots)

    forbidden_call_names = {
        "open",
        "unlink",
        "remove",
        "rmdir",
        "mkdir",
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
        "rename",
        "replace",
        "rmtree",
        "copy",
        "copyfile",
        "move",
        "system",
        "Popen",
        "run",
        "call",
        "check_call",
        "check_output",
        "Thread",
        "Timer",
        "sleep",
        "connect",
        "request",
        "urlopen",
        "notify",
        "send",
        "dispatch",
    }
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            if isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)
    assert call_names.isdisjoint(forbidden_call_names)

    lowered_source = source.lower()
    for forbidden_fragment in (
        "argparse",
        "__main__",
        "scheduler",
        "background",
        "desktop",
        "telegram",
        "browser",
        "network",
        "audio",
        "stt",
        "microphone",
        "sqlite",
        "persist",
        "pyproject",
        "readme",
        "gate d passed",
        "product promise alpha passed",
        "autonomous participation",
        "academic answer",
        "git push",
        "public release",
    ):
        assert forbidden_fragment not in lowered_source


def _assert_authorization_summary_is_safe(payload: dict[str, object]) -> None:
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
