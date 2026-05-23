from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from async_scholar import session_window_execution_preflight as execution_preflight
from async_scholar.course_metadata import CourseMetadata
from async_scholar.schedule_config import ScheduleConfig
from async_scholar.schedule_store import save_course_schedule
from async_scholar.scheduled_start import ScheduledStartClock
from async_scholar.session_window_execution_preflight import (
    STORED_SESSION_WINDOW_EXECUTION_PREFLIGHT_ERROR,
    build_stored_session_window_execution_preflight_from_store,
)

SESSION_ID = "session-001"
PREFLIGHT_KEYS = (
    "preflight_kind",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "due_count",
    "authorization_status",
    "authorized",
    "authorized_start_count",
    "runtime_state",
    "recovery_review_status",
    "ready_to_execute",
    "decision",
    "reason",
)


def _write_private_course_schedule(db_path: Path) -> None:
    save_course_schedule(
        db_path,
        CourseMetadata(
            course_id="cs101",
            title="Confidential Systems",
            instructor_name="Dr. Private",
            meeting_url="https://meet.example.edu/private-token",
            meeting_label="Private lecture",
        ),
        ScheduleConfig(
            course_id="cs101",
            class_times=[
                {
                    "day_of_week": "monday",
                    "local_start_time": "09:00",
                    "duration_minutes": 75,
                    "timezone_name": "Asia/Manila",
                    "meeting_label": "Private lecture",
                }
            ],
        ),
    )


def _archive(tmp_path: Path) -> tuple[Path, Path]:
    archive_root = tmp_path / "archive"
    session_dir = archive_root / SESSION_ID
    session_dir.mkdir(parents=True)
    return archive_root, session_dir


def _clock(day: str = "monday", time: str = "09:00") -> ScheduledStartClock:
    return ScheduledStartClock(day_of_week=day, local_time=time)


def _build(
    tmp_path: Path,
    *,
    clock: ScheduledStartClock | None = None,
    confirmation_response: str = "confirmed",
    archive_root: Path | None = None,
    session_id: str = SESSION_ID,
) -> dict[str, object]:
    db_path = tmp_path / "schedule.sqlite"
    if not db_path.exists():
        _write_private_course_schedule(db_path)
    if archive_root is None:
        archive_root, _session_dir = _archive(tmp_path)

    return build_stored_session_window_execution_preflight_from_store(
        db_path,
        archive_root,
        session_id,
        "file",
        clock or _clock(),
        confirmation_response,
    )


def _start_receipt(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "receipt_kind": "stored_session_window_start_receipt",
        "status": "authorized",
        "session_id": SESSION_ID,
        "source_kind": "file",
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 1,
        "due_count": 1,
        "ready_to_start": True,
        "confirmation_required": True,
        "confirmation_status": "required",
        "confirmation_response": "confirmed",
        "confirmation_verified": True,
        "authorized": True,
        "authorized_start_count": 1,
        "blocked_start_count": 0,
        "block_reason": "none",
        "runtime_record_written": True,
    }
    payload.update(overrides)
    return payload


def _stop_receipt(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "receipt_kind": "stored_session_window_stop_receipt",
        "status": "enabled",
        "session_id": SESSION_ID,
        "course_id": "cs101",
        "source_kind": "file",
        "selected_class_time_index": 0,
        "scheduled_day_of_week": "monday",
        "scheduled_local_start_time": "09:00",
        "stop_after_minutes": 75,
        "enabled": True,
        "runtime_record_written": True,
    }
    payload.update(overrides)
    return payload


def _write_runtime(session_dir: Path, *records: dict[str, object]) -> None:
    runtime_text = "".join(
        json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
        for record in records
    )
    (session_dir / "runtime.jsonl").write_text(runtime_text, encoding="utf-8")


def _authorization_summary(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "status": "authorized",
        "session_id": SESSION_ID,
        "source_kind": "file",
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_count": 1,
        "due_count": 1,
        "ready_to_start": True,
        "confirmation_required": True,
        "confirmation_status": "required",
        "confirmation_response": "confirmed",
        "confirmation_verified": True,
        "authorized": True,
        "authorized_start_count": 1,
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
                "stop_after_minutes": 75,
                "enabled": True,
                "requires_confirmation": True,
                "confirmation_response": "confirmed",
                "authorized": True,
            }
        ],
    }
    payload.update(overrides)
    return payload


def _assert_preflight_error(*args: object) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_stored_session_window_execution_preflight_from_store(*args)  # type: ignore[arg-type]
    assert str(exc_info.value) == STORED_SESSION_WINDOW_EXECUTION_PREFLIGHT_ERROR


def _assert_receipt_is_safe(receipt: dict[str, object]) -> None:
    combined_output = json.dumps(receipt, sort_keys=True).lower()
    for forbidden_fragment in (
        "confidential",
        "dr.",
        "private",
        "lecture",
        "meeting",
        "meet.example",
        "token",
        "secret",
        "auth-profile",
        "profile",
        "timezone",
        "asia/manila",
        "sqlite",
        "archive_root",
        "runtime.jsonl",
        "events.jsonl",
        "alert",
        "notification",
        "browser",
        "cookie",
        "traceback",
        str(Path.home()).lower(),
    ):
        assert forbidden_fragment not in combined_output


def _relative_paths(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def test_execution_preflight_allows_due_confirmed_clean_missing_runtime(
    tmp_path: Path,
) -> None:
    receipt = _build(tmp_path)

    assert type(receipt) is dict
    assert tuple(receipt) == PREFLIGHT_KEYS
    assert receipt == {
        "preflight_kind": "stored_session_window_execution_preflight",
        "session_id": SESSION_ID,
        "source_kind": "file",
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "due_count": 1,
        "authorization_status": "authorized",
        "authorized": True,
        "authorized_start_count": 1,
        "runtime_state": "not_started",
        "recovery_review_status": "not_required",
        "ready_to_execute": True,
        "decision": "allow",
        "reason": "ready_to_execute",
    }
    _assert_receipt_is_safe(receipt)
    assert "runtime.jsonl" not in _relative_paths(tmp_path)


def test_execution_preflight_blocks_no_due_session(tmp_path: Path) -> None:
    receipt = _build(tmp_path, clock=_clock("tuesday", "09:00"))

    assert receipt["due_count"] == 0
    assert receipt["authorization_status"] == "not_required"
    assert receipt["ready_to_execute"] is False
    assert receipt["decision"] == "block"
    assert receipt["reason"] == "no_due_session"
    _assert_receipt_is_safe(receipt)


def test_execution_preflight_blocks_declined_confirmation(tmp_path: Path) -> None:
    receipt = _build(tmp_path, confirmation_response="declined")

    assert receipt["authorization_status"] == "blocked"
    assert receipt["authorized"] is False
    assert receipt["ready_to_execute"] is False
    assert receipt["decision"] == "block"
    assert receipt["reason"] == "confirmation_declined"
    _assert_receipt_is_safe(receipt)


def test_execution_preflight_rejects_malformed_confirmation_input(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    archive_root, _session_dir = _archive(tmp_path)

    _assert_preflight_error(
        db_path,
        archive_root,
        SESSION_ID,
        "file",
        _clock(),
        "yes please start my private lecture",
    )


def test_execution_preflight_blocks_completed_prior_runtime_receipts(
    tmp_path: Path,
) -> None:
    archive_root, session_dir = _archive(tmp_path)
    _write_runtime(session_dir, _start_receipt(), _stop_receipt())

    receipt = _build(tmp_path, archive_root=archive_root)

    assert receipt["runtime_state"] == "stopped"
    assert receipt["recovery_review_status"] == "required"
    assert receipt["ready_to_execute"] is False
    assert receipt["decision"] == "block"
    assert receipt["reason"] == "existing_conflicting_receipt"


def test_execution_preflight_blocks_partial_runtime(tmp_path: Path) -> None:
    archive_root, session_dir = _archive(tmp_path)
    _write_runtime(session_dir, _start_receipt())

    receipt = _build(tmp_path, archive_root=archive_root)

    assert receipt["runtime_state"] == "started"
    assert receipt["recovery_review_status"] == "required"
    assert receipt["ready_to_execute"] is False
    assert receipt["decision"] == "block"
    assert receipt["reason"] == "partial_runtime"


def test_execution_preflight_blocks_recovery_review_required(
    tmp_path: Path,
) -> None:
    archive_root, session_dir = _archive(tmp_path)
    (session_dir / "events.jsonl").write_text(
        "private event token secret auth profile payload",
        encoding="utf-8",
    )

    receipt = _build(tmp_path, archive_root=archive_root)

    assert receipt["runtime_state"] == "not_started"
    assert receipt["recovery_review_status"] == "required"
    assert receipt["ready_to_execute"] is False
    assert receipt["decision"] == "block"
    assert receipt["reason"] == "recovery_review_required"
    _assert_receipt_is_safe(receipt)


def test_execution_preflight_sanitizes_malformed_delegated_summary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    archive_root, _session_dir = _archive(tmp_path)

    def fake_authorization(_payload: dict[str, object]) -> dict[str, object]:
        return {
            "status": "authorized",
            "session_id": SESSION_ID,
            "private_path": "C:\\Users\\student\\token-secret-auth-profile",
        }

    monkeypatch.setattr(
        execution_preflight,
        "build_session_window_start_authorization_summary",
        fake_authorization,
    )

    _assert_preflight_error(
        db_path,
        archive_root,
        SESSION_ID,
        "file",
        _clock(),
        "confirmed",
    )


@pytest.mark.parametrize(
    "authorization",
    (
        pytest.param(
            _authorization_summary(confirmation_verified=False),
            id="unverified-authorized-start",
        ),
        pytest.param(
            _authorization_summary(confirmation_response="declined"),
            id="declined-authorized-start",
        ),
        pytest.param(
            _authorization_summary(block_reason="confirmation_declined"),
            id="authorized-with-block-reason",
        ),
        pytest.param(
            _authorization_summary(courses=[]),
            id="authorized-without-courses",
        ),
    ),
)
def test_execution_preflight_sanitizes_policy_inconsistent_authorization(
    tmp_path: Path,
    monkeypatch,
    authorization: dict[str, object],
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    archive_root, _session_dir = _archive(tmp_path)

    def fake_authorization(_payload: dict[str, object]) -> dict[str, object]:
        return authorization

    monkeypatch.setattr(
        execution_preflight,
        "build_session_window_start_authorization_summary",
        fake_authorization,
    )

    _assert_preflight_error(
        db_path,
        archive_root,
        SESSION_ID,
        "file",
        _clock(),
        "confirmed",
    )


@pytest.mark.parametrize(
    "authorization",
    (
        pytest.param(
            _authorization_summary(session_id="other-session"),
            id="wrong-session",
        ),
        pytest.param(_authorization_summary(source_kind="mic"), id="wrong-source"),
        pytest.param(
            _authorization_summary(clock_day_of_week="tuesday"),
            id="wrong-day",
        ),
        pytest.param(_authorization_summary(clock_local_time="09:01"), id="wrong-time"),
        pytest.param(
            _authorization_summary(
                due_count=2,
                authorized_start_count=2,
                courses=[
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
            ),
            id="wrong-due-count",
        ),
    ),
)
def test_execution_preflight_sanitizes_mismatched_authorization_context(
    tmp_path: Path,
    monkeypatch,
    authorization: dict[str, object],
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    archive_root, _session_dir = _archive(tmp_path)

    def fake_authorization(_payload: dict[str, object]) -> dict[str, object]:
        return authorization

    monkeypatch.setattr(
        execution_preflight,
        "build_session_window_start_authorization_summary",
        fake_authorization,
    )

    _assert_preflight_error(
        db_path,
        archive_root,
        SESSION_ID,
        "file",
        _clock(),
        "confirmed",
    )


def test_execution_preflight_sanitizes_detached_authorization_confirmation_context(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    archive_root, _session_dir = _archive(tmp_path)

    def fake_authorization(_payload: dict[str, object]) -> dict[str, object]:
        return _authorization_summary()

    monkeypatch.setattr(
        execution_preflight,
        "build_session_window_start_authorization_summary",
        fake_authorization,
    )

    _assert_preflight_error(
        db_path,
        archive_root,
        SESSION_ID,
        "file",
        _clock(),
        "declined",
    )


def test_execution_preflight_rejects_unsafe_path_and_session_id(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    archive_root = tmp_path / "archive-token-secret-auth-profile"
    archive_root.write_text("not a directory", encoding="utf-8")

    _assert_preflight_error(
        db_path,
        archive_root,
        SESSION_ID,
        "file",
        _clock(),
        "confirmed",
    )
    _assert_preflight_error(
        db_path,
        tmp_path,
        "../session-token-secret",
        "file",
        _clock(),
        "confirmed",
    )


def test_execution_preflight_sanitizes_unreadable_runtime_state(
    tmp_path: Path,
) -> None:
    archive_root, session_dir = _archive(tmp_path)
    (session_dir / "runtime.jsonl").mkdir()

    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    _assert_preflight_error(
        db_path,
        archive_root,
        SESSION_ID,
        "file",
        _clock(),
        "confirmed",
    )


def test_execution_preflight_does_not_write_or_delete_files(tmp_path: Path) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    archive_root, _session_dir = _archive(tmp_path)
    before = _relative_paths(tmp_path)

    build_stored_session_window_execution_preflight_from_store(
        db_path,
        archive_root,
        SESSION_ID,
        "file",
        _clock(),
        "confirmed",
    )

    assert _relative_paths(tmp_path) == before


def test_execution_preflight_source_has_no_execution_or_delivery_imports() -> None:
    source = inspect.getsource(execution_preflight)

    for forbidden_fragment in (
        "write_stored_session_window_start_receipt",
        "write_stored_session_window_stop_receipt",
        "alert_dispatch",
        "notification",
        "desktop_notifier",
        "telegram",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "mic_recording",
        "browser",
        "archive_delete",
        "archive_export_local",
        "execute_archive",
        "participation",
        "academic_answer",
        ".write_text(",
        ".unlink(",
        ".rmdir(",
        ".mkdir(",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
    ):
        assert forbidden_fragment not in source
