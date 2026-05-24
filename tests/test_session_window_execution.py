from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from async_scholar import session_window_execution as execution
from async_scholar.course_metadata import CourseMetadata
from async_scholar.schedule_config import ScheduleConfig
from async_scholar.schedule_store import save_course_schedule
from async_scholar.scheduled_start import ScheduledStartClock
from async_scholar.session_window_execution import (
    STORED_SESSION_WINDOW_EXECUTION_ERROR,
    build_stored_session_window_execution_from_store,
)

SESSION_ID = "session-001"
EXECUTION_KEYS = (
    "execution_kind",
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
    "preflight_decision",
    "preflight_reason",
    "runtime_record_written",
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
    source_kind: str = "file",
    archive_root: Path | None = None,
    session_id: str = SESSION_ID,
) -> dict[str, object]:
    db_path = tmp_path / "schedule.sqlite"
    if not db_path.exists():
        _write_private_course_schedule(db_path)
    if archive_root is None:
        archive_root, _session_dir = _archive(tmp_path)

    return build_stored_session_window_execution_from_store(
        db_path,
        archive_root,
        session_id,
        source_kind,
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


def _runtime_records(runtime_path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in runtime_path.read_text(encoding="utf-8").splitlines()
    ]


def _assert_execution_error(*args: object) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_stored_session_window_execution_from_store(*args)  # type: ignore[arg-type]
    assert str(exc_info.value) == STORED_SESSION_WINDOW_EXECUTION_ERROR


def _assert_payload_is_safe(*payloads: object) -> None:
    combined_output = json.dumps(payloads, sort_keys=True).lower()
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


def test_execution_allows_due_confirmed_and_writes_one_start_receipt(
    tmp_path: Path,
) -> None:
    result = _build(tmp_path)
    runtime_path = tmp_path / "archive" / SESSION_ID / "runtime.jsonl"
    records = _runtime_records(runtime_path)

    assert type(result) is dict
    assert tuple(result) == EXECUTION_KEYS
    assert result == {
        "execution_kind": "stored_session_window_execution",
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
        "preflight_decision": "allow",
        "preflight_reason": "ready_to_execute",
        "runtime_record_written": True,
        "decision": "executed",
        "reason": "start_receipt_written",
    }
    assert len(records) == 1
    assert records[0]["receipt_kind"] == "stored_session_window_start_receipt"
    assert records[0]["runtime_record_written"] is True
    _assert_payload_is_safe(result, records)


def test_execution_blocks_no_due_session_and_writes_no_runtime(
    tmp_path: Path,
) -> None:
    result = _build(tmp_path, clock=_clock("tuesday", "09:00"))

    assert result["due_count"] == 0
    assert result["preflight_decision"] == "block"
    assert result["decision"] == "blocked"
    assert result["reason"] == "no_due_session"
    assert result["runtime_record_written"] is False
    assert not (tmp_path / "archive" / SESSION_ID / "runtime.jsonl").exists()
    _assert_payload_is_safe(result)


def test_execution_blocks_declined_confirmation_and_does_not_call_writer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_writer(_authorization: dict[str, object], _archive_root: Path) -> None:
        raise AssertionError("blocked execution must not write a receipt")

    monkeypatch.setattr(
        execution,
        "write_stored_session_window_start_receipt",
        fail_writer,
    )

    result = _build(tmp_path, confirmation_response="declined")

    assert result["authorization_status"] == "blocked"
    assert result["authorized"] is False
    assert result["preflight_decision"] == "block"
    assert result["decision"] == "blocked"
    assert result["reason"] == "confirmation_declined"
    assert result["runtime_record_written"] is False
    assert not (tmp_path / "archive" / SESSION_ID / "runtime.jsonl").exists()


def test_execution_blocks_completed_prior_runtime_without_appending(
    tmp_path: Path,
) -> None:
    archive_root, session_dir = _archive(tmp_path)
    _write_runtime(session_dir, _start_receipt(), _stop_receipt())
    before = (session_dir / "runtime.jsonl").read_text(encoding="utf-8")

    result = _build(tmp_path, archive_root=archive_root)

    assert result["runtime_state"] == "stopped"
    assert result["preflight_decision"] == "block"
    assert result["decision"] == "blocked"
    assert result["reason"] == "existing_conflicting_receipt"
    assert result["runtime_record_written"] is False
    assert (session_dir / "runtime.jsonl").read_text(encoding="utf-8") == before


def test_execution_blocks_recovery_review_required_without_runtime_write(
    tmp_path: Path,
) -> None:
    archive_root, session_dir = _archive(tmp_path)
    (session_dir / "events.jsonl").write_text(
        "private event token secret auth profile payload",
        encoding="utf-8",
    )

    result = _build(tmp_path, archive_root=archive_root)

    assert result["runtime_state"] == "not_started"
    assert result["recovery_review_status"] == "required"
    assert result["preflight_decision"] == "block"
    assert result["decision"] == "blocked"
    assert result["reason"] == "recovery_review_required"
    assert result["runtime_record_written"] is False
    assert not (session_dir / "runtime.jsonl").exists()


def test_execution_rejects_malformed_confirmation_input(tmp_path: Path) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    archive_root, _session_dir = _archive(tmp_path)

    _assert_execution_error(
        db_path,
        archive_root,
        SESSION_ID,
        "file",
        _clock(),
        "yes please start my private lecture",
    )
    assert not (archive_root / SESSION_ID / "runtime.jsonl").exists()


def test_execution_sanitizes_malformed_preflight_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    archive_root, _session_dir = _archive(tmp_path)

    def fake_preflight(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
            "preflight_kind": "stored_session_window_execution_preflight",
            "session_id": SESSION_ID,
            "private_path": "C:\\Users\\student\\token-secret-auth-profile",
        }

    monkeypatch.setattr(
        execution,
        "build_stored_session_window_execution_preflight_from_store",
        fake_preflight,
    )

    _assert_execution_error(
        db_path,
        archive_root,
        SESSION_ID,
        "file",
        _clock(),
        "confirmed",
    )
    assert not (archive_root / SESSION_ID / "runtime.jsonl").exists()


def test_execution_sanitizes_writer_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    archive_root, _session_dir = _archive(tmp_path)

    def fake_writer(
        _authorization: dict[str, object],
        _archive_root: Path,
    ) -> dict[str, object]:
        raise ValueError("C:\\Users\\student\\private-runtime-token")

    monkeypatch.setattr(
        execution,
        "write_stored_session_window_start_receipt",
        fake_writer,
    )

    _assert_execution_error(
        db_path,
        archive_root,
        SESSION_ID,
        "file",
        _clock(),
        "confirmed",
    )
    assert not (archive_root / SESSION_ID / "runtime.jsonl").exists()


def test_execution_accepts_mic_as_metadata_label_only(tmp_path: Path) -> None:
    result = _build(tmp_path, source_kind="mic")
    runtime_path = tmp_path / "archive" / SESSION_ID / "runtime.jsonl"
    records = _runtime_records(runtime_path)

    assert result["source_kind"] == "mic"
    assert result["decision"] == "executed"
    assert records[0]["source_kind"] == "mic"
    _assert_payload_is_safe(result, records)


def test_execution_source_guards_forbidden_execution_surfaces() -> None:
    source = inspect.getsource(execution)

    assert "build_stored_session_window_execution_preflight_from_store" in source
    assert "write_stored_session_window_start_receipt" in source
    for forbidden_fragment in (
        "sleep",
        "Timer(",
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
        "mic_recording",
        "vad",
        "stt",
        "telegram",
        "desktop",
        "notify",
        "delete",
        "unlink(",
        "rmdir(",
    ):
        assert forbidden_fragment not in source
