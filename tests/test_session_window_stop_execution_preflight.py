from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from async_scholar import session_window_stop_execution_preflight as stop_preflight
from async_scholar.course_metadata import CourseMetadata
from async_scholar.schedule_config import ScheduleConfig
from async_scholar.schedule_store import save_course_schedule
from async_scholar.session_window_stop_execution_preflight import (
    STORED_SESSION_WINDOW_STOP_EXECUTION_PREFLIGHT_ERROR,
    build_stored_session_window_stop_execution_preflight_from_store,
)

SESSION_ID = "session-001"
PREFLIGHT_KEYS = (
    "preflight_kind",
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


def _build(
    tmp_path: Path,
    *,
    archive_root: Path | None = None,
    session_id: str = SESSION_ID,
    source_kind: str = "file",
    enabled: bool = True,
) -> dict[str, object]:
    db_path = tmp_path / "schedule.sqlite"
    if not db_path.exists():
        _write_private_course_schedule(db_path)
    if archive_root is None:
        archive_root, session_dir = _archive(tmp_path)
        _write_runtime(session_dir, _start_receipt(source_kind=source_kind))

    return build_stored_session_window_stop_execution_preflight_from_store(
        db_path,
        archive_root,
        session_id,
        "cs101",
        0,
        source_kind,
        enabled=enabled,
    )


def _assert_preflight_error(*args: object) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_stored_session_window_stop_execution_preflight_from_store(
            *args  # type: ignore[arg-type]
        )
    assert str(exc_info.value) == STORED_SESSION_WINDOW_STOP_EXECUTION_PREFLIGHT_ERROR


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


def test_stop_execution_preflight_allows_started_runtime_without_writing(
    tmp_path: Path,
) -> None:
    archive_root, session_dir = _archive(tmp_path)
    _write_runtime(session_dir, _start_receipt())
    runtime_path = session_dir / "runtime.jsonl"
    before = runtime_path.read_text(encoding="utf-8")

    result = _build(tmp_path, archive_root=archive_root)

    assert type(result) is dict
    assert tuple(result) == PREFLIGHT_KEYS
    assert result == {
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
        "ready_to_stop": True,
        "decision": "allow",
        "reason": "ready_to_stop",
    }
    assert runtime_path.read_text(encoding="utf-8") == before
    _assert_payload_is_safe(result)


def test_stop_execution_preflight_blocks_disabled_preview(tmp_path: Path) -> None:
    result = _build(tmp_path, enabled=False)

    assert result["runtime_state"] == "started"
    assert result["ready_to_stop"] is False
    assert result["decision"] == "block"
    assert result["reason"] == "disabled_stop_preview"
    _assert_payload_is_safe(result)


def test_stop_execution_preflight_blocks_missing_runtime(tmp_path: Path) -> None:
    archive_root, session_dir = _archive(tmp_path)

    result = _build(tmp_path, archive_root=archive_root)

    assert result["runtime_state"] == "missing"
    assert result["start_receipt_count"] == 0
    assert result["stop_receipt_count"] == 0
    assert result["ready_to_stop"] is False
    assert result["decision"] == "block"
    assert result["reason"] == "missing_runtime"
    assert not (session_dir / "runtime.jsonl").exists()


def test_stop_execution_preflight_blocks_not_started_runtime(tmp_path: Path) -> None:
    archive_root, session_dir = _archive(tmp_path)
    _write_runtime(session_dir)

    result = _build(tmp_path, archive_root=archive_root)

    assert result["runtime_state"] == "not_started"
    assert result["reason"] == "not_started_runtime"
    assert result["decision"] == "block"


def test_stop_execution_preflight_blocks_already_stopped_runtime(
    tmp_path: Path,
) -> None:
    archive_root, session_dir = _archive(tmp_path)
    _write_runtime(session_dir, _start_receipt(), _stop_receipt())
    before = (session_dir / "runtime.jsonl").read_text(encoding="utf-8")

    result = _build(tmp_path, archive_root=archive_root)

    assert result["runtime_state"] == "stopped"
    assert result["start_receipt_count"] == 1
    assert result["stop_receipt_count"] == 1
    assert result["reason"] == "already_stopped_runtime"
    assert result["decision"] == "block"
    assert (session_dir / "runtime.jsonl").read_text(encoding="utf-8") == before


def test_stop_execution_preflight_blocks_inconsistent_runtime(
    tmp_path: Path,
) -> None:
    archive_root, session_dir = _archive(tmp_path)
    _write_runtime(session_dir, _start_receipt(), _start_receipt())

    result = _build(tmp_path, archive_root=archive_root)

    assert result["runtime_state"] == "inconsistent"
    assert result["start_receipt_count"] == 2
    assert result["stop_receipt_count"] == 0
    assert result["reason"] == "inconsistent_runtime"
    assert result["decision"] == "block"


def test_stop_execution_preflight_blocks_source_mismatch(tmp_path: Path) -> None:
    archive_root, session_dir = _archive(tmp_path)
    _write_runtime(session_dir, _start_receipt(source_kind="file"))

    result = _build(tmp_path, archive_root=archive_root, source_kind="mic")

    assert result["source_kind"] == "mic"
    assert result["runtime_state"] == "started"
    assert result["reason"] == "source_mismatch"
    assert result["decision"] == "block"


def test_stop_execution_preflight_accepts_mic_as_metadata_label(
    tmp_path: Path,
) -> None:
    result = _build(tmp_path, source_kind="mic")

    assert result["source_kind"] == "mic"
    assert result["ready_to_stop"] is True
    assert result["decision"] == "allow"
    _assert_payload_is_safe(result)


def test_stop_execution_preflight_sanitizes_malformed_stop_preview(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    archive_root, session_dir = _archive(tmp_path)
    _write_runtime(session_dir, _start_receipt())

    def fake_preview(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
            "status": "enabled",
            "course_id": "cs101",
            "private_path": "C:\\Users\\student\\token-secret-auth-profile",
        }

    monkeypatch.setattr(
        stop_preflight,
        "build_session_stop_preview_from_store_input",
        fake_preview,
    )

    _assert_preflight_error(
        db_path,
        archive_root,
        SESSION_ID,
        "cs101",
        0,
        "file",
    )


def test_stop_execution_preflight_rejects_mismatched_delegated_stop_preview_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    archive_root, session_dir = _archive(tmp_path)
    _write_runtime(session_dir, _start_receipt(source_kind="mic"))

    def fake_preview(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
            "status": "enabled",
            "course_id": "cs999",
            "source_kind": "mic",
            "selected_class_time_index": 9,
            "scheduled_day_of_week": "monday",
            "scheduled_local_start_time": "09:00",
            "stop_after_minutes": 75,
            "enabled": True,
        }

    monkeypatch.setattr(
        stop_preflight,
        "build_session_stop_preview_from_store_input",
        fake_preview,
    )

    _assert_preflight_error(
        db_path,
        archive_root,
        SESSION_ID,
        "cs101",
        0,
        "file",
    )


def test_stop_execution_preflight_sanitizes_malformed_runtime_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    archive_root, session_dir = _archive(tmp_path)
    _write_runtime(session_dir, _start_receipt())

    def fake_runtime(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
            "summary_kind": "stored_session_window_runtime_summary",
            "session_id": SESSION_ID,
            "private_path": "C:\\Users\\student\\token-secret-auth-profile",
        }

    monkeypatch.setattr(
        stop_preflight,
        "build_stored_session_window_runtime_summary",
        fake_runtime,
    )

    _assert_preflight_error(
        db_path,
        archive_root,
        SESSION_ID,
        "cs101",
        0,
        "file",
    )


def test_stop_execution_preflight_rejects_mismatched_delegated_runtime_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    archive_root, session_dir = _archive(tmp_path)
    _write_runtime(session_dir, _start_receipt())

    def fake_runtime(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
            "summary_kind": "stored_session_window_runtime_summary",
            "session_id": "other-session",
            "runtime_record_count": 1,
            "start_receipt_count": 1,
            "stop_receipt_count": 0,
            "lifecycle_status": "started",
            "session_active": True,
            "session_stopped": False,
            "last_receipt_kind": "stored_session_window_start_receipt",
            "last_source_kind": "file",
        }

    monkeypatch.setattr(
        stop_preflight,
        "build_stored_session_window_runtime_summary",
        fake_runtime,
    )

    _assert_preflight_error(
        db_path,
        archive_root,
        SESSION_ID,
        "cs101",
        0,
        "file",
    )


def test_stop_execution_preflight_rejects_unsafe_archive_or_session(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    _write_private_course_schedule(db_path)
    unsafe_archive = tmp_path / "archive-token-secret-auth-profile"
    unsafe_archive.write_text("not a directory", encoding="utf-8")

    _assert_preflight_error(
        db_path,
        unsafe_archive,
        SESSION_ID,
        "cs101",
        0,
        "file",
    )
    _assert_preflight_error(
        db_path,
        tmp_path,
        "../session",
        "cs101",
        0,
        "file",
    )


def test_stop_execution_preflight_source_guards_forbidden_surfaces() -> None:
    source = inspect.getsource(stop_preflight)

    assert "build_session_stop_preview_from_store_input" in source
    assert "build_stored_session_window_runtime_summary" in source
    for forbidden_fragment in (
        "write_stored_session_window_stop_receipt",
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
        ".write_text(",
        ".open(",
        ".unlink(",
        ".rmdir(",
    ):
        assert forbidden_fragment not in source
