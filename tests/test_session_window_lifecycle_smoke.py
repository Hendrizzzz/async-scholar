from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from async_scholar import session_window_lifecycle_smoke as lifecycle_smoke
from async_scholar.session_window_lifecycle_smoke import (
    SESSION_WINDOW_LIFECYCLE_SMOKE_ERROR,
    build_local_session_window_lifecycle_smoke,
)

LIFECYCLE_KEYS = (
    "lifecycle_kind",
    "status",
    "start_decision",
    "start_reason",
    "start_runtime_record_written",
    "stop_decision",
    "stop_reason",
    "stop_runtime_record_written",
    "gate_d_pass_claimed",
    "product_promise_alpha_pass_claimed",
)
SESSION_ID = "lifecycle-smoke-session"


def _runtime_records(runtime_path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in runtime_path.read_text(encoding="utf-8").splitlines()
    ]


def _assert_lifecycle_error(*args: object, **kwargs: object) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_local_session_window_lifecycle_smoke(
            *args,
            **kwargs,  # type: ignore[arg-type]
        )
    assert str(exc_info.value) == SESSION_WINDOW_LIFECYCLE_SMOKE_ERROR


def _assert_payload_is_safe(*payloads: object) -> None:
    combined_output = json.dumps(payloads, sort_keys=True).lower()
    for forbidden_fragment in (
        "confidential",
        "private",
        "lecture",
        "meeting",
        "meet.example",
        "transcript",
        "audio",
        "alert title",
        "alert body",
        "token",
        "secret",
        "auth",
        "profile",
        "cookie",
        "browser",
        "sqlite",
        "archive_root",
        "runtime.jsonl",
        "traceback",
        str(Path.home()).lower(),
    ):
        assert forbidden_fragment not in combined_output


def test_lifecycle_smoke_runs_start_then_stop_with_synthetic_metadata(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    archive_root = tmp_path / "archive"

    result = build_local_session_window_lifecycle_smoke(db_path, archive_root)
    runtime_path = archive_root / SESSION_ID / "runtime.jsonl"
    records = _runtime_records(runtime_path)

    assert type(result) is dict
    assert tuple(result) == LIFECYCLE_KEYS
    assert result == {
        "lifecycle_kind": "local_session_window_lifecycle_smoke",
        "status": "completed",
        "start_decision": "executed",
        "start_reason": "start_receipt_written",
        "start_runtime_record_written": True,
        "stop_decision": "executed",
        "stop_reason": "stop_receipt_written",
        "stop_runtime_record_written": True,
        "gate_d_pass_claimed": False,
        "product_promise_alpha_pass_claimed": False,
    }
    assert db_path.exists()
    assert len(records) == 2
    assert records[0]["receipt_kind"] == "stored_session_window_start_receipt"
    assert records[1]["receipt_kind"] == "stored_session_window_stop_receipt"
    _assert_payload_is_safe(result)


def test_lifecycle_smoke_disabled_returns_without_touching_paths(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "missing-parent" / "schedule.sqlite"
    archive_root = tmp_path / "missing-archive"

    result = build_local_session_window_lifecycle_smoke(
        db_path,
        archive_root,
        enabled=False,
    )

    assert result == {
        "lifecycle_kind": "local_session_window_lifecycle_smoke",
        "status": "disabled",
        "start_decision": "disabled",
        "start_reason": "disabled",
        "start_runtime_record_written": False,
        "stop_decision": "disabled",
        "stop_reason": "disabled",
        "stop_runtime_record_written": False,
        "gate_d_pass_claimed": False,
        "product_promise_alpha_pass_claimed": False,
    }
    assert not db_path.exists()
    assert not db_path.parent.exists()
    assert not archive_root.exists()
    _assert_payload_is_safe(result)


def test_lifecycle_smoke_sanitizes_store_failure(tmp_path: Path) -> None:
    raw_path = tmp_path / "missing-parent-token-secret-auth-profile" / "schedule.sqlite"
    archive_root = tmp_path / "archive"

    _assert_lifecycle_error(raw_path, archive_root)

    assert not archive_root.exists()


def test_lifecycle_smoke_rejects_traversal_archive_root_before_mkdir(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "schedule.sqlite"
    traversal_root = tmp_path / "safe" / ".." / "outside-token-secret-auth-profile"

    _assert_lifecycle_error(db_path, traversal_root)

    assert db_path.exists()
    assert not (tmp_path / "outside-token-secret-auth-profile").exists()
    assert not (tmp_path / "safe").exists()


def test_lifecycle_smoke_rejects_delegated_start_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_start(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
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
            "runtime_record_written": False,
            "decision": "blocked",
            "reason": "C:\\Users\\student\\token-secret-auth-profile",
        }

    def fail_stop(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise AssertionError("mismatched start must not run stop")

    monkeypatch.setattr(
        lifecycle_smoke,
        "build_stored_session_window_execution_from_store",
        fake_start,
    )
    monkeypatch.setattr(
        lifecycle_smoke,
        "build_stored_session_window_stop_execution_from_store",
        fail_stop,
    )

    _assert_lifecycle_error(tmp_path / "schedule.sqlite", tmp_path / "archive")


def test_lifecycle_smoke_rejects_delegated_stop_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_start(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
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

    def fake_stop(*_args: object, **_kwargs: object) -> dict[str, object]:
        return {
            "execution_kind": "stored_session_window_stop_execution",
            "session_id": SESSION_ID,
            "course_id": "lifecycle101",
            "source_kind": "file",
            "selected_class_time_index": 0,
            "scheduled_day_of_week": "monday",
            "scheduled_local_start_time": "09:00",
            "stop_after_minutes": 60,
            "runtime_state": "started",
            "start_receipt_count": 1,
            "stop_receipt_count": 0,
            "ready_to_stop": True,
            "confirmation_response": "confirmed",
            "preflight_decision": "allow",
            "preflight_reason": "ready_to_stop",
            "runtime_record_written": False,
            "decision": "blocked",
            "reason": "token-secret-auth-profile",
        }

    monkeypatch.setattr(
        lifecycle_smoke,
        "build_stored_session_window_execution_from_store",
        fake_start,
    )
    monkeypatch.setattr(
        lifecycle_smoke,
        "build_stored_session_window_stop_execution_from_store",
        fake_stop,
    )

    _assert_lifecycle_error(tmp_path / "schedule.sqlite", tmp_path / "archive")


def test_lifecycle_smoke_source_guards_public_boundaries_only() -> None:
    source = inspect.getsource(lifecycle_smoke)

    assert "save_course_schedule" in source
    assert "build_stored_session_window_execution_from_store" in source
    assert "build_stored_session_window_stop_execution_from_store" in source
    for forbidden_fragment in (
        "write_stored_session_window_start_receipt",
        "write_stored_session_window_stop_receipt",
        "build_session_window_confirmation_preflight_summary",
        "build_session_window_confirmation_response_summary",
        "build_session_window_start_authorization_summary",
        "dispatch_alert",
        "telegram",
        "desktop",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "webbrowser",
        "sounddevice",
        "faster_whisper",
        "mic_recording",
        "vad",
        "stt",
        "transcript",
        "audio",
        "loopback",
        "cookie",
        "delete",
        "export",
        "unlink(",
        "rmdir(",
        "sleep",
        "Timer(",
        "threading",
        "asyncio",
    ):
        assert forbidden_fragment not in source
