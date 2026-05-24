from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from async_scholar import session_window_stop_execution as stop_execution
from async_scholar.course_metadata import CourseMetadata
from async_scholar.schedule_config import ScheduleConfig
from async_scholar.schedule_store import save_course_schedule
from async_scholar.session_window_stop_execution import (
    STORED_SESSION_WINDOW_STOP_EXECUTION_ERROR,
    build_stored_session_window_stop_execution_from_store,
)

SESSION_ID = "session-001"
EXECUTION_KEYS = (
    "execution_kind",
    "session_id",
    "course_id",
    "source_kind",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "stop_after_minutes",
    "runtime_state",
    "start_receipt_count",
    "stop_receipt_count",
    "ready_to_stop",
    "confirmation_response",
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


def _build(
    tmp_path: Path,
    *,
    archive_root: Path | None = None,
    session_id: str = SESSION_ID,
    source_kind: str = "file",
    confirmation_response: str = "confirmed",
    enabled: bool = True,
) -> dict[str, object]:
    db_path = tmp_path / "schedule.sqlite"
    if not db_path.exists():
        _write_private_course_schedule(db_path)
    if archive_root is None:
        archive_root, session_dir = _archive(tmp_path)
        _write_runtime(session_dir, _start_receipt(source_kind=source_kind))

    return build_stored_session_window_stop_execution_from_store(
        db_path,
        archive_root,
        session_id,
        "cs101",
        0,
        source_kind,
        confirmation_response,
        enabled=enabled,
    )


def _assert_stop_execution_error(*args: object) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_stored_session_window_stop_execution_from_store(
            *args  # type: ignore[arg-type]
        )
    assert str(exc_info.value) == STORED_SESSION_WINDOW_STOP_EXECUTION_ERROR


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


def test_stop_execution_allows_started_confirmed_and_writes_one_stop_receipt(
    tmp_path: Path,
) -> None:
    result = _build(tmp_path)
    runtime_path = tmp_path / "archive" / SESSION_ID / "runtime.jsonl"
    records = _runtime_records(runtime_path)

    assert type(result) is dict
    assert tuple(result) == EXECUTION_KEYS
    assert result == {
        "execution_kind": "stored_session_window_stop_execution",
        "session_id": SESSION_ID,
        "course_id": "cs101",
        "source_kind": "file",
        "selected_class_time_index": 0,
        "scheduled_day_of_week": "monday",
        "scheduled_local_start_time": "09:00",
        "stop_after_minutes": 75,
        "runtime_state": "started",
        "start_receipt_count": 1,
        "stop_receipt_count": 0,
        "ready_to_stop": True,
        "confirmation_response": "confirmed",
        "preflight_decision": "allow",
        "preflight_reason": "ready_to_stop",
        "runtime_record_written": True,
        "decision": "executed",
        "reason": "stop_receipt_written",
    }
    assert len(records) == 2
    assert records[1]["receipt_kind"] == "stored_session_window_stop_receipt"
    assert records[1]["runtime_record_written"] is True
    _assert_payload_is_safe(result, records)


def test_stop_execution_blocks_declined_confirmation_without_writer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive_root, session_dir = _archive(tmp_path)
    _write_runtime(session_dir, _start_receipt())
    before = (session_dir / "runtime.jsonl").read_text(encoding="utf-8")

    def fail_writer(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("declined stop execution must not write")

    monkeypatch.setattr(
        stop_execution,
        "write_stored_session_window_stop_receipt",
        fail_writer,
    )

    result = _build(
        tmp_path,
        archive_root=archive_root,
        confirmation_response="declined",
    )

    assert result["ready_to_stop"] is True
    assert result["preflight_decision"] == "allow"
    assert result["decision"] == "blocked"
    assert result["reason"] == "confirmation_declined"
    assert result["runtime_record_written"] is False
    assert (session_dir / "runtime.jsonl").read_text(encoding="utf-8") == before
    _assert_payload_is_safe(result)


@pytest.mark.parametrize(
    ("runtime_records", "expected_state", "expected_reason"),
    (
        ((), "missing", "missing_runtime"),
        ((None,), "not_started", "not_started_runtime"),
        ((_start_receipt(), _stop_receipt()), "stopped", "already_stopped_runtime"),
    ),
)
def test_stop_execution_blocks_preflight_without_writing(
    tmp_path: Path,
    runtime_records: tuple[dict[str, object] | None, ...],
    expected_state: str,
    expected_reason: str,
) -> None:
    archive_root, session_dir = _archive(tmp_path)
    if runtime_records and runtime_records != (None,):
        _write_runtime(session_dir, *[record for record in runtime_records if record])
    elif runtime_records == (None,):
        _write_runtime(session_dir)
    runtime_path = session_dir / "runtime.jsonl"
    before = runtime_path.read_text(encoding="utf-8") if runtime_path.exists() else ""

    result = _build(tmp_path, archive_root=archive_root)

    assert result["runtime_state"] == expected_state
    assert result["preflight_decision"] == "block"
    assert result["decision"] == "blocked"
    assert result["reason"] == expected_reason
    assert result["runtime_record_written"] is False
    if runtime_path.exists():
        assert runtime_path.read_text(encoding="utf-8") == before
    else:
        assert before == ""
    _assert_payload_is_safe(result)


def test_stop_execution_blocks_disabled_preview_without_writing(tmp_path: Path) -> None:
    archive_root, session_dir = _archive(tmp_path)
    _write_runtime(session_dir, _start_receipt())
    before = (session_dir / "runtime.jsonl").read_text(encoding="utf-8")

    result = _build(tmp_path, archive_root=archive_root, enabled=False)

    assert result["preflight_decision"] == "block"
    assert result["decision"] == "blocked"
    assert result["reason"] == "disabled_stop_preview"
    assert result["runtime_record_written"] is False
    assert (session_dir / "runtime.jsonl").read_text(encoding="utf-8") == before


def test_stop_execution_blocks_source_mismatch_without_writing(tmp_path: Path) -> None:
    archive_root, session_dir = _archive(tmp_path)
    _write_runtime(session_dir, _start_receipt(source_kind="file"))
    before = (session_dir / "runtime.jsonl").read_text(encoding="utf-8")

    result = _build(tmp_path, archive_root=archive_root, source_kind="mic")

    assert result["source_kind"] == "mic"
    assert result["preflight_decision"] == "block"
    assert result["decision"] == "blocked"
    assert result["reason"] == "source_mismatch"
    assert result["runtime_record_written"] is False
    assert (session_dir / "runtime.jsonl").read_text(encoding="utf-8") == before


def test_stop_execution_rejects_malformed_confirmation_input(tmp_path: Path) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    archive_root, session_dir = _archive(tmp_path)
    _write_runtime(session_dir, _start_receipt())

    _assert_stop_execution_error(
        db_path,
        archive_root,
        SESSION_ID,
        "cs101",
        0,
        "file",
        "yes please stop my private lecture",
    )
    assert len(_runtime_records(session_dir / "runtime.jsonl")) == 1


def test_stop_execution_sanitizes_malformed_preflight_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    archive_root, session_dir = _archive(tmp_path)
    _write_runtime(session_dir, _start_receipt())

    def fake_preflight(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
            "preflight_kind": "stored_session_window_stop_execution_preflight",
            "session_id": SESSION_ID,
            "private_path": "C:\\Users\\student\\token-secret-auth-profile",
        }

    monkeypatch.setattr(
        stop_execution,
        "build_stored_session_window_stop_execution_preflight_from_store",
        fake_preflight,
    )

    _assert_stop_execution_error(
        db_path,
        archive_root,
        SESSION_ID,
        "cs101",
        0,
        "file",
        "confirmed",
    )
    assert len(_runtime_records(session_dir / "runtime.jsonl")) == 1


@pytest.mark.parametrize(
    ("decision", "reason"),
    (
        ("block", "ready_to_stop"),
        ("block", "stop_receipt_written"),
    ),
)
def test_stop_execution_sanitizes_semantic_preflight_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    decision: str,
    reason: str,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    archive_root, session_dir = _archive(tmp_path)
    _write_runtime(session_dir, _start_receipt())

    def fake_preflight(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
            "preflight_kind": "stored_session_window_stop_execution_preflight",
            "session_id": SESSION_ID,
            "course_id": "cs101",
            "source_kind": "file",
            "selected_class_time_index": 0,
            "scheduled_day_of_week": "monday",
            "scheduled_local_start_time": "09:00",
            "stop_after_minutes": 75,
            "runtime_state": "started",
            "start_receipt_count": 1,
            "stop_receipt_count": 0,
            "ready_to_stop": False,
            "decision": decision,
            "reason": reason,
        }

    monkeypatch.setattr(
        stop_execution,
        "build_stored_session_window_stop_execution_preflight_from_store",
        fake_preflight,
    )

    _assert_stop_execution_error(
        db_path,
        archive_root,
        SESSION_ID,
        "cs101",
        0,
        "file",
        "confirmed",
    )
    assert len(_runtime_records(session_dir / "runtime.jsonl")) == 1


def test_stop_execution_rejects_mismatched_preflight_context_before_writing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    archive_root, session_dir = _archive(tmp_path)
    _write_runtime(session_dir, _start_receipt())

    def fake_preflight(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
            "preflight_kind": "stored_session_window_stop_execution_preflight",
            "session_id": "session-999",
            "course_id": "cs999",
            "source_kind": "mic",
            "selected_class_time_index": 1,
            "scheduled_day_of_week": "monday",
            "scheduled_local_start_time": "09:00",
            "stop_after_minutes": 75,
            "runtime_state": "started",
            "start_receipt_count": 1,
            "stop_receipt_count": 0,
            "ready_to_stop": True,
            "decision": "allow",
            "reason": "ready_to_stop",
        }

    def fail_writer(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("mismatched delegated preflight must not write")

    monkeypatch.setattr(
        stop_execution,
        "build_stored_session_window_stop_execution_preflight_from_store",
        fake_preflight,
    )
    monkeypatch.setattr(
        stop_execution,
        "write_stored_session_window_stop_receipt",
        fail_writer,
    )

    _assert_stop_execution_error(
        db_path,
        archive_root,
        SESSION_ID,
        "cs101",
        0,
        "file",
        "confirmed",
    )
    assert len(_runtime_records(session_dir / "runtime.jsonl")) == 1


def test_stop_execution_rejects_mismatched_receipt_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    archive_root, session_dir = _archive(tmp_path)
    _write_runtime(session_dir, _start_receipt())

    def fake_writer(
        _stop_preview: dict[str, object],
        _archive_root: Path,
        _session_id: str,
    ) -> dict[str, object]:
        return _stop_receipt(course_id="cs999")

    monkeypatch.setattr(
        stop_execution,
        "write_stored_session_window_stop_receipt",
        fake_writer,
    )

    _assert_stop_execution_error(
        db_path,
        archive_root,
        SESSION_ID,
        "cs101",
        0,
        "file",
        "confirmed",
    )
    assert len(_runtime_records(session_dir / "runtime.jsonl")) == 1


def test_stop_execution_sanitizes_malformed_receipt_payload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    archive_root, session_dir = _archive(tmp_path)
    _write_runtime(session_dir, _start_receipt())

    def fake_writer(
        _stop_preview: dict[str, object],
        _archive_root: Path,
        _session_id: str,
    ) -> dict[str, object]:
        return {
            "receipt_kind": "stored_session_window_stop_receipt",
            "session_id": SESSION_ID,
            "private_path": "C:\\Users\\student\\token-secret-auth-profile",
        }

    monkeypatch.setattr(
        stop_execution,
        "write_stored_session_window_stop_receipt",
        fake_writer,
    )

    _assert_stop_execution_error(
        db_path,
        archive_root,
        SESSION_ID,
        "cs101",
        0,
        "file",
        "confirmed",
    )
    assert len(_runtime_records(session_dir / "runtime.jsonl")) == 1


def test_stop_execution_accepts_mic_as_metadata_label_only(tmp_path: Path) -> None:
    result = _build(tmp_path, source_kind="mic")
    runtime_path = tmp_path / "archive" / SESSION_ID / "runtime.jsonl"
    records = _runtime_records(runtime_path)

    assert result["source_kind"] == "mic"
    assert result["decision"] == "executed"
    assert records[1]["source_kind"] == "mic"
    _assert_payload_is_safe(result, records)


def test_stop_execution_source_guards_forbidden_surfaces() -> None:
    source = inspect.getsource(stop_execution)

    assert "build_stored_session_window_stop_execution_preflight_from_store" in source
    assert "write_stored_session_window_stop_receipt" in source
    for forbidden_fragment in (
        "write_stored_session_window_start_receipt",
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
        "archive_export",
        "autonomous_participation",
        "academic_answer",
        ".unlink(",
        ".rmdir(",
    ):
        assert forbidden_fragment not in source
