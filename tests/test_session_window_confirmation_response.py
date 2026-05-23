from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from async_scholar.session_window_confirmation_response import (
    STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR,
    build_session_window_confirmation_response_summary,
    session_window_confirmation_response_safe_summary,
)


def _required_preflight() -> dict[str, object]:
    return {
        "status": "required",
        "session_id": "session-001",
        "source_kind": "file",
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 2,
        "due_count": 3,
        "ready_to_start": True,
        "confirmation_required": True,
        "confirmation_status": "required",
        "blocked_execution_count": 3,
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
            },
        ],
    }


def _not_required_preflight() -> dict[str, object]:
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
        "blocked_execution_count": 0,
        "courses": [],
    }


def _disabled_preflight() -> dict[str, object]:
    return {
        "status": "disabled",
        "session_id": "session-001",
        "source_kind": "file",
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 2,
        "due_count": 0,
        "ready_to_start": False,
        "confirmation_required": False,
        "confirmation_status": "disabled",
        "blocked_execution_count": 0,
        "courses": [],
    }


def test_build_confirmation_response_confirmed_required_path() -> None:
    summary = build_session_window_confirmation_response_summary(
        _required_preflight(),
        "confirmed",
    )

    assert summary == {
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
        ],
    }
    _assert_response_summary_is_safe(summary)


def test_build_confirmation_response_declined_required_path() -> None:
    summary = build_session_window_confirmation_response_summary(
        _required_preflight(),
        "declined",
    )

    assert summary["status"] == "declined"
    assert summary["confirmation_response"] == "declined"
    assert summary["confirmation_verified"] is False
    assert summary["confirmed_start_count"] == 0
    assert summary["blocked_execution_count"] == 3
    assert [course["confirmation_response"] for course in summary["courses"]] == [
        "declined",
        "declined",
        "declined",
    ]
    _assert_response_summary_is_safe(summary)


@pytest.mark.parametrize(
    ("preflight", "response", "expected_status"),
    [
        (_not_required_preflight(), "confirmed", "not_required"),
        (_not_required_preflight(), "declined", "not_required"),
        (_disabled_preflight(), "confirmed", "disabled"),
        (_disabled_preflight(), "declined", "disabled"),
    ],
)
def test_build_confirmation_response_non_required_paths_have_no_courses(
    preflight: dict[str, object],
    response: str,
    expected_status: str,
) -> None:
    summary = build_session_window_confirmation_response_summary(preflight, response)

    assert summary["status"] == expected_status
    assert summary["confirmation_response"] == response
    assert summary["confirmation_verified"] is False
    assert summary["confirmed_start_count"] == 0
    assert summary["blocked_execution_count"] == 0
    assert summary["courses"] == []
    _assert_response_summary_is_safe(summary)


@pytest.mark.parametrize(
    "confirmation_response",
    [
        "",
        " ",
        "confirm",
        "CONFIRMED",
        "confirmed ",
        " confirmed",
        "declined because private meeting token secret",
        None,
        True,
        1,
        b"confirmed",
        [],
    ],
)
def test_builder_rejects_free_form_private_and_non_string_response_values(
    confirmation_response: object,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_session_window_confirmation_response_summary(
            _required_preflight(),
            confirmation_response,  # type: ignore[arg-type]
        )

    assert str(exc_info.value) == STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR
    assert "private meeting token secret" not in str(exc_info.value)


@pytest.mark.parametrize(
    "payload_update",
    [
        {"status": "confirmed"},
        {"confirmation_status": "not_required"},
        {"confirmation_required": False},
        {"ready_to_start": False},
        {"due_count": 0},
        {"due_count": True},
        {"blocked_execution_count": 0},
        {"blocked_execution_count": True},
        {"courses": []},
        {"private_path": "C:\\Users\\student\\secret.txt"},
    ],
)
def test_builder_rejects_malformed_required_preflight_shape(
    payload_update: dict[str, object],
) -> None:
    payload = _required_preflight()
    payload.update(payload_update)

    with pytest.raises(ValueError) as exc_info:
        build_session_window_confirmation_response_summary(payload, "confirmed")

    assert str(exc_info.value) == STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR


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
        {"meeting_url": "https://meet.example.edu/private-token"},
    ],
)
def test_builder_rejects_unsafe_course_rows(
    course_update: dict[str, object],
) -> None:
    payload = _required_preflight()
    courses = payload["courses"]
    assert isinstance(courses, list)
    first_course = dict(courses[0])
    first_course.update(course_update)
    courses[0] = first_course

    with pytest.raises(ValueError) as exc_info:
        build_session_window_confirmation_response_summary(payload, "confirmed")

    assert str(exc_info.value) == STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR


def test_builder_rejects_duplicate_course_rows() -> None:
    payload = _required_preflight()
    courses = payload["courses"]
    assert isinstance(courses, list)
    courses[1] = dict(courses[2])

    with pytest.raises(ValueError) as exc_info:
        build_session_window_confirmation_response_summary(payload, "confirmed")

    assert str(exc_info.value) == STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR


def test_safe_summary_strips_private_fields_and_serializes_to_json() -> None:
    payload = {
        **build_session_window_confirmation_response_summary(
            _required_preflight(),
            "confirmed",
        ),
        "private_path": "C:\\Users\\student\\secret.txt",
        "meeting_url": "https://meet.example.edu/private-token",
    }
    courses = payload["courses"]
    assert isinstance(courses, list)
    courses[0] = {
        **courses[0],
        "title": "Confidential Systems",
        "notification_body": "Private alert body",
        "artifact_path": "C:\\Users\\student\\events.jsonl",
    }

    safe = session_window_confirmation_response_safe_summary(payload)

    assert set(safe) == {
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
        "confirmation_response",
        "confirmation_verified",
        "confirmed_start_count",
        "blocked_execution_count",
        "courses",
    }
    assert set(safe["courses"][0]) == {
        "course_id",
        "selected_class_time_index",
        "scheduled_day_of_week",
        "scheduled_local_start_time",
        "due",
        "minutes_until_start",
        "stop_after_minutes",
        "enabled",
        "requires_confirmation",
        "confirmation_response",
    }
    assert json.loads(json.dumps(safe)) == safe
    _assert_response_summary_is_safe(safe)


@pytest.mark.parametrize(
    "payload_update",
    [
        {"status": "confirmed", "confirmation_response": "declined"},
        {"status": "declined", "confirmation_response": "confirmed"},
        {"status": "not_required", "confirmation_status": "required"},
        {"status": "disabled", "confirmation_status": "not_required"},
        {"confirmation_verified": True},
        {"confirmed_start_count": 1},
        {"blocked_execution_count": 1},
        {"ready_to_start": True},
        {"confirmation_required": True},
        {"due_count": 1},
        {"courses": [{"course_id": "cs101"}]},
    ],
)
def test_safe_summary_revalidates_not_required_policy(
    payload_update: dict[str, object],
) -> None:
    payload = build_session_window_confirmation_response_summary(
        _not_required_preflight(),
        "confirmed",
    )
    payload.update(payload_update)

    with pytest.raises(ValueError) as exc_info:
        session_window_confirmation_response_safe_summary(payload)

    assert str(exc_info.value) == STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR


def test_safe_summary_revalidates_course_confirmation_response() -> None:
    payload = build_session_window_confirmation_response_summary(
        _required_preflight(),
        "confirmed",
    )
    courses = payload["courses"]
    assert isinstance(courses, list)
    courses[0] = {**courses[0], "confirmation_response": "declined"}

    with pytest.raises(ValueError) as exc_info:
        session_window_confirmation_response_safe_summary(payload)

    assert str(exc_info.value) == STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR


def test_safe_summary_revalidates_required_course_count() -> None:
    payload = build_session_window_confirmation_response_summary(
        _required_preflight(),
        "confirmed",
    )
    courses = payload["courses"]
    assert isinstance(courses, list)
    payload["courses"] = courses[:2]

    with pytest.raises(ValueError) as exc_info:
        session_window_confirmation_response_safe_summary(payload)

    assert str(exc_info.value) == STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_ERROR


def test_source_has_no_execution_or_persistence_behavior() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "async_scholar"
        / "session_window_confirmation_response.py"
    )
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
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
    }
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            if isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)
    assert call_names.isdisjoint(forbidden_call_names)


def _assert_response_summary_is_safe(payload: dict[str, object]) -> None:
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
