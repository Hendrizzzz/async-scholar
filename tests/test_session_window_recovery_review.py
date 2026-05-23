from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from async_scholar import session_window_recovery_review as recovery_review
from async_scholar.archive_export import ALLOWED_ARCHIVE_ARTIFACT_FILENAMES
from async_scholar.session_window_recovery_review import (
    STORED_SESSION_WINDOW_RECOVERY_REVIEW_ERROR,
    build_stored_session_window_recovery_review,
)

SESSION_ID = "session-001"
RUNTIME_FILENAME = "runtime.jsonl"
NON_RUNTIME_FILENAMES = tuple(
    filename
    for filename in ALLOWED_ARCHIVE_ARTIFACT_FILENAMES
    if filename != RUNTIME_FILENAME
)
REVIEW_KEYS = (
    "review_kind",
    "session_id",
    "runtime_lifecycle_status",
    "archive_recovery_status",
    "archive_existing_count",
    "archive_missing_count",
    "recovery_decision",
    "manual_review_required",
    "review_status",
    "review_reason",
    "safe_next_review_action",
)
DECISION_KEYS = (
    "decision_kind",
    "session_id",
    "runtime_lifecycle_status",
    "runtime_record_count",
    "start_receipt_count",
    "stop_receipt_count",
    "session_active",
    "session_stopped",
    "archive_recovery_status",
    "archive_existing_count",
    "archive_missing_count",
    "recovery_decision",
    "manual_review_required",
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


def _compact_line(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"


def _archive(
    tmp_path: Path,
    *runtime_records: dict[str, object],
    artifact_filenames: tuple[str, ...] = (),
    raw_runtime_text: str | None = None,
) -> Path:
    archive_root = tmp_path / "archive"
    session_dir = archive_root / SESSION_ID
    session_dir.mkdir(parents=True)
    runtime_text = (
        "".join(_compact_line(record) for record in runtime_records)
        if raw_runtime_text is None
        else raw_runtime_text
    )
    (session_dir / RUNTIME_FILENAME).write_text(runtime_text, encoding="utf-8")
    for filename in artifact_filenames:
        (session_dir / filename).write_text(
            f"{filename} private content must stay unread",
            encoding="utf-8",
        )
    return archive_root


def _decision(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "decision_kind": "stored_session_window_recovery_decision",
        "session_id": SESSION_ID,
        "runtime_lifecycle_status": "not_started",
        "runtime_record_count": 0,
        "start_receipt_count": 0,
        "stop_receipt_count": 0,
        "session_active": False,
        "session_stopped": False,
        "archive_recovery_status": "empty",
        "archive_existing_count": 0,
        "archive_missing_count": len(NON_RUNTIME_FILENAMES),
        "recovery_decision": "no_action",
        "manual_review_required": False,
    }
    payload.update(overrides)
    return payload


def _assert_review_error(archive_root: object, session_id: object) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_stored_session_window_recovery_review(archive_root, session_id)  # type: ignore[arg-type]
    assert str(exc_info.value) == STORED_SESSION_WINDOW_RECOVERY_REVIEW_ERROR


def test_build_recovery_review_no_action_summary(tmp_path: Path) -> None:
    archive_root = _archive(
        tmp_path,
        _start_receipt(),
        _stop_receipt(),
        artifact_filenames=NON_RUNTIME_FILENAMES,
    )

    review = build_stored_session_window_recovery_review(archive_root, SESSION_ID)

    assert review == {
        "review_kind": "stored_session_window_recovery_review",
        "session_id": SESSION_ID,
        "runtime_lifecycle_status": "stopped",
        "archive_recovery_status": "complete",
        "archive_existing_count": len(NON_RUNTIME_FILENAMES),
        "archive_missing_count": 0,
        "recovery_decision": "no_action",
        "manual_review_required": False,
        "review_status": "not_required",
        "review_reason": "none",
        "safe_next_review_action": "leave_archive_unchanged",
    }


@pytest.mark.parametrize(
    (
        "decision_payload",
        "expected_manual_review",
        "expected_status",
        "expected_reason",
        "expected_action",
    ),
    (
        pytest.param(
            _decision(recovery_decision="no_action", manual_review_required=False),
            False,
            "not_required",
            "none",
            "leave_archive_unchanged",
            id="no-action",
        ),
        pytest.param(
            _decision(
                runtime_lifecycle_status="started",
                recovery_decision="inspect_active_session",
                manual_review_required=True,
            ),
            True,
            "required",
            "active_session_runtime",
            "inspect_runtime_metadata",
            id="inspect-active-session",
        ),
        pytest.param(
            _decision(
                archive_recovery_status="partial",
                archive_existing_count=1,
                archive_missing_count=len(NON_RUNTIME_FILENAMES) - 1,
                recovery_decision="inspect_partial_archive",
                manual_review_required=True,
            ),
            True,
            "required",
            "partial_archive_metadata",
            "inspect_archive_metadata",
            id="inspect-partial-archive",
        ),
        pytest.param(
            _decision(
                runtime_lifecycle_status="inconsistent",
                recovery_decision="manual_review",
                manual_review_required=True,
            ),
            True,
            "required",
            "inconsistent_runtime",
            "escalate_manual_review",
            id="manual-review",
        ),
    ),
)
def test_build_recovery_review_decision_mapping(
    monkeypatch,
    decision_payload: dict[str, object],
    expected_manual_review: bool,
    expected_status: str,
    expected_reason: str,
    expected_action: str,
) -> None:
    monkeypatch.setattr(
        recovery_review,
        "build_stored_session_window_recovery_decision",
        lambda archive_root, session_id: decision_payload,
    )

    review = build_stored_session_window_recovery_review(
        Path("archive-root"),
        SESSION_ID,
    )

    assert tuple(review) == REVIEW_KEYS
    assert review["recovery_decision"] == decision_payload["recovery_decision"]
    assert review["manual_review_required"] is expected_manual_review
    assert review["review_status"] == expected_status
    assert review["review_reason"] == expected_reason
    assert review["safe_next_review_action"] == expected_action


@pytest.mark.parametrize(
    "decision_payload",
    (
        pytest.param(
            {**_decision(), "private_path": "C:\\Users\\student\\secret"},
            id="extra-key",
        ),
        pytest.param(
            _decision(decision_kind="stored_session_window_runtime_summary"),
            id="bad-kind",
        ),
        pytest.param(_decision(session_id=""), id="bad-session-id"),
        pytest.param(_decision(session_id="session-002"), id="mismatched-session-id"),
        pytest.param(
            _decision(session_id="token-secret-auth-profile"),
            id="mismatched-token-like-session-id",
        ),
        pytest.param(
            _decision(session_id="C:\\Users\\student\\token-secret-auth-profile"),
            id="private-path-session-id",
        ),
        pytest.param(_decision(session_id="../session"), id="traversal-session-id"),
        pytest.param(
            _decision(session_id="https://example.test/session"),
            id="uri-session-id",
        ),
        pytest.param(_decision(session_id=" session-001"), id="space-session-id"),
        pytest.param(
            _decision(runtime_lifecycle_status="gate_d_passed"),
            id="bad-lifecycle",
        ),
        pytest.param(
            _decision(archive_recovery_status="deleted"),
            id="bad-archive-status",
        ),
        pytest.param(_decision(archive_existing_count=-1), id="negative-count"),
        pytest.param(_decision(archive_missing_count=True), id="bool-count"),
        pytest.param(
            _decision(recovery_decision="execute_recovery"),
            id="bad-decision",
        ),
        pytest.param(
            _decision(
                recovery_decision="inspect_partial_archive",
                manual_review_required=False,
            ),
            id="manual-review-mismatch",
        ),
    ),
)
def test_bad_composed_decision_payloads_are_sanitized(
    monkeypatch,
    decision_payload: dict[str, object],
) -> None:
    monkeypatch.setattr(
        recovery_review,
        "build_stored_session_window_recovery_decision",
        lambda archive_root, session_id: decision_payload,
    )

    _assert_review_error(Path("archive-root"), SESSION_ID)


def test_delegated_failure_is_sanitized(monkeypatch) -> None:
    def fake_decision(archive_root: Path, session_id: str) -> dict[str, object]:
        raise ValueError("C:\\Users\\student\\token-secret-auth-profile")

    monkeypatch.setattr(
        recovery_review,
        "build_stored_session_window_recovery_decision",
        fake_decision,
    )

    _assert_review_error(Path("archive-root"), SESSION_ID)


def test_malformed_or_unsafe_input_is_sanitized(tmp_path: Path) -> None:
    archive_root = _archive(
        tmp_path,
        raw_runtime_text=_compact_line(_start_receipt(private_token="secret")),
    )

    _assert_review_error(archive_root, SESSION_ID)
    _assert_review_error(archive_root, "../session")


def test_output_uses_only_allowlisted_safe_metadata(tmp_path: Path) -> None:
    archive_root = _archive(
        tmp_path,
        _start_receipt(),
        artifact_filenames=(NON_RUNTIME_FILENAMES[0],),
    )

    review = build_stored_session_window_recovery_review(archive_root, SESSION_ID)
    encoded = json.dumps(review, sort_keys=True, separators=(",", ":")).lower()

    assert tuple(review) == REVIEW_KEYS
    assert set(review) == set(REVIEW_KEYS)
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "private content",
        "confidential",
        "token",
        "secret",
        "auth",
        "profile",
        "cookie",
        "transcript",
        "audio",
        "browser",
        "alert body",
        "generated media",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in encoded


def test_review_builder_does_not_create_modify_or_delete_files(tmp_path: Path) -> None:
    archive_root = _archive(tmp_path)
    before = {
        path.relative_to(archive_root).as_posix(): (
            path.stat().st_size,
            path.stat().st_mtime_ns,
        )
        for path in archive_root.rglob("*")
        if path.is_file()
    }

    build_stored_session_window_recovery_review(archive_root, SESSION_ID)

    after = {
        path.relative_to(archive_root).as_posix(): (
            path.stat().st_size,
            path.stat().st_mtime_ns,
        )
        for path in archive_root.rglob("*")
        if path.is_file()
    }
    assert after == before


def test_json_serialization_is_deterministic_and_compact(tmp_path: Path) -> None:
    archive_root = _archive(tmp_path)
    review = build_stored_session_window_recovery_review(archive_root, SESSION_ID)

    encoded = json.dumps(review, sort_keys=True, separators=(",", ":"))

    assert json.loads(encoded) == review
    assert "\n" not in encoded
    assert ": " not in encoded


def test_recovery_review_source_stays_read_only_metadata_only() -> None:
    source = inspect.getsource(recovery_review)

    assert "build_stored_session_window_recovery_decision(" in source
    for forbidden_fragment in (
        "build_stored_session_window_runtime_summary",
        "build_crash_recovery_session_preflight",
        "session_recovery",
        "session_window_runtime_summary",
        "archive_export",
        "archive_delete",
        "load_course_schedule",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "ScheduledStartClock",
        "write_stored_session_window_start_receipt",
        "write_stored_session_window_stop_receipt",
        "datetime",
        "now(",
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
        "telegram",
        "desktop_notifier",
        "alert_dispatch",
        "execute_archive",
        ".open(",
        ".write_text(",
        ".write(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
        "participation",
        "academic_answer",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in source
