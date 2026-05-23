from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from async_scholar import session_window_recovery_decision as recovery_decision
from async_scholar.archive_export import ALLOWED_ARCHIVE_ARTIFACT_FILENAMES
from async_scholar.session_window_recovery_decision import (
    STORED_SESSION_WINDOW_RECOVERY_DECISION_ERROR,
    build_stored_session_window_recovery_decision,
)

SESSION_ID = "session-001"
DECISION_KIND = "stored_session_window_recovery_decision"
RUNTIME_FILENAME = "runtime.jsonl"
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
NON_RUNTIME_FILENAMES = tuple(
    filename
    for filename in ALLOWED_ARCHIVE_ARTIFACT_FILENAMES
    if filename != RUNTIME_FILENAME
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
) -> tuple[Path, Path]:
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
    return archive_root, session_dir


def _assert_decision_error(archive_root: object, session_id: object) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_stored_session_window_recovery_decision(archive_root, session_id)  # type: ignore[arg-type]
    assert str(exc_info.value) == STORED_SESSION_WINDOW_RECOVERY_DECISION_ERROR


def _relative_paths(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def _symlink_or_skip(
    source: Path,
    target: Path,
    *,
    target_is_directory: bool = False,
) -> None:
    try:
        target.symlink_to(source, target_is_directory=target_is_directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")


@pytest.mark.parametrize(
    (
        "runtime_records",
        "artifact_filenames",
        "expected_lifecycle",
        "expected_archive_status",
        "expected_decision",
        "expected_manual_review",
    ),
    (
        pytest.param(
            (),
            (),
            "not_started",
            "empty",
            "no_action",
            False,
            id="not-started-empty",
        ),
        pytest.param(
            (_start_receipt(),),
            (),
            "started",
            "empty",
            "inspect_active_session",
            True,
            id="started",
        ),
        pytest.param(
            (_start_receipt(), _stop_receipt()),
            NON_RUNTIME_FILENAMES,
            "stopped",
            "complete",
            "no_action",
            False,
            id="stopped-complete",
        ),
        pytest.param(
            (_start_receipt(), _stop_receipt()),
            (NON_RUNTIME_FILENAMES[0],),
            "stopped",
            "partial",
            "inspect_partial_archive",
            True,
            id="stopped-partial",
        ),
        pytest.param(
            (),
            (NON_RUNTIME_FILENAMES[0],),
            "not_started",
            "partial",
            "inspect_partial_archive",
            True,
            id="not-started-partial",
        ),
        pytest.param(
            (_stop_receipt(),),
            (),
            "inconsistent",
            "empty",
            "manual_review",
            True,
            id="inconsistent",
        ),
    ),
)
def test_build_recovery_decision_matrix(
    tmp_path: Path,
    runtime_records: tuple[dict[str, object], ...],
    artifact_filenames: tuple[str, ...],
    expected_lifecycle: str,
    expected_archive_status: str,
    expected_decision: str,
    expected_manual_review: bool,
) -> None:
    archive_root, _session_dir = _archive(
        tmp_path,
        *runtime_records,
        artifact_filenames=artifact_filenames,
    )

    decision = build_stored_session_window_recovery_decision(archive_root, SESSION_ID)

    assert tuple(decision) == DECISION_KEYS
    assert decision["decision_kind"] == DECISION_KIND
    assert decision["session_id"] == SESSION_ID
    assert decision["runtime_lifecycle_status"] == expected_lifecycle
    assert decision["archive_recovery_status"] == expected_archive_status
    assert decision["archive_existing_count"] == len(artifact_filenames)
    assert decision["archive_missing_count"] == len(NON_RUNTIME_FILENAMES) - len(
        artifact_filenames
    )
    assert decision["recovery_decision"] == expected_decision
    assert decision["manual_review_required"] is expected_manual_review


def test_malformed_runtime_input_is_sanitized_through_runtime_summary(
    tmp_path: Path,
) -> None:
    archive_root, _session_dir = _archive(
        tmp_path,
        raw_runtime_text=_compact_line(_start_receipt(private_token="secret")),
    )

    _assert_decision_error(archive_root, SESSION_ID)


@pytest.mark.parametrize(
    "session_id",
    (
        "",
        " ",
        ".",
        "..",
        "../session",
        "session/001",
        "session\\001",
        "session:001",
        "session\n001",
        "https://example.test/session",
    ),
)
def test_rejects_unsafe_session_ids(tmp_path: Path, session_id: str) -> None:
    archive_root = tmp_path / "archive"
    archive_root.mkdir()

    _assert_decision_error(archive_root, session_id)


def test_rejects_unsafe_archive_roots() -> None:
    for archive_root in (
        "",
        " ",
        "https://example.test/archive",
        "file:///C:/Users/student/archive",
        "\\\\server\\share\\archive",
        "archive\nroot",
    ):
        _assert_decision_error(archive_root, SESSION_ID)


def test_missing_runtime_is_not_synthesized_as_not_started(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive"
    (archive_root / SESSION_ID).mkdir(parents=True)

    _assert_decision_error(archive_root, SESSION_ID)


def test_rejects_non_file_runtime_path(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive"
    runtime_path = archive_root / SESSION_ID / RUNTIME_FILENAME
    runtime_path.mkdir(parents=True)

    _assert_decision_error(archive_root, SESSION_ID)


def test_rejects_symlink_archive_root(tmp_path: Path) -> None:
    real_root = tmp_path / "real-archive"
    link_root = tmp_path / "archive-link"
    real_root.mkdir()
    _symlink_or_skip(real_root, link_root, target_is_directory=True)

    _assert_decision_error(link_root, SESSION_ID)


def test_rejects_symlink_runtime_file(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive"
    session_dir = archive_root / SESSION_ID
    real_runtime_path = tmp_path / "real-runtime.jsonl"
    link_runtime_path = session_dir / RUNTIME_FILENAME
    session_dir.mkdir(parents=True)
    real_runtime_path.write_text("", encoding="utf-8")
    _symlink_or_skip(real_runtime_path, link_runtime_path)

    _assert_decision_error(archive_root, SESSION_ID)


def test_decision_builder_does_not_create_modify_or_delete_files(
    tmp_path: Path,
) -> None:
    archive_root, session_dir = _archive(
        tmp_path,
        _start_receipt(),
        _stop_receipt(),
        artifact_filenames=NON_RUNTIME_FILENAMES,
    )
    before_texts = {
        path.relative_to(tmp_path).as_posix(): path.read_text(encoding="utf-8")
        for path in session_dir.iterdir()
        if path.is_file()
    }
    before_paths = _relative_paths(tmp_path)

    build_stored_session_window_recovery_decision(archive_root, SESSION_ID)

    after_texts = {
        path.relative_to(tmp_path).as_posix(): path.read_text(encoding="utf-8")
        for path in session_dir.iterdir()
        if path.is_file()
    }
    assert after_texts == before_texts
    assert _relative_paths(tmp_path) == before_paths


def test_output_is_allowlisted_and_private_artifact_content_is_not_leaked(
    tmp_path: Path,
) -> None:
    archive_root, session_dir = _archive(
        tmp_path,
        _start_receipt(),
        artifact_filenames=(NON_RUNTIME_FILENAMES[0],),
    )
    (session_dir / NON_RUNTIME_FILENAMES[0]).write_text(
        "Confidential token secret auth profile transcript audio browser",
        encoding="utf-8",
    )

    decision = build_stored_session_window_recovery_decision(archive_root, SESSION_ID)
    encoded_decision = json.dumps(decision, sort_keys=True).lower()

    assert tuple(decision) == DECISION_KEYS
    for forbidden_fragment in (
        "summary_kind",
        "preflight_kind",
        "last_receipt",
        "last_source",
        "artifacts",
        "filename",
        "runtime.jsonl",
        "transcript.jsonl",
        "private",
        "confidential",
        "token",
        "secret",
        "auth",
        "profile",
        "audio",
        "browser",
        str(tmp_path).lower(),
    ):
        assert forbidden_fragment not in encoded_decision


def test_json_serialization_is_deterministic_and_compact(tmp_path: Path) -> None:
    archive_root, _session_dir = _archive(tmp_path)
    decision = build_stored_session_window_recovery_decision(archive_root, SESSION_ID)

    encoded = json.dumps(decision, sort_keys=True, separators=(",", ":"))

    assert json.loads(encoded) == decision
    assert "\n" not in encoded
    assert ": " not in encoded


def test_decision_builder_delegates_narrowly_and_runtime_summary_runs_first(
    monkeypatch,
) -> None:
    calls: list[str] = []

    def fake_runtime_summary(archive_root: Path, session_id: str) -> dict[str, object]:
        calls.append(f"runtime:{archive_root}:{session_id}")
        return {
            "summary_kind": "stored_session_window_runtime_summary",
            "session_id": SESSION_ID,
            "runtime_record_count": 0,
            "start_receipt_count": 0,
            "stop_receipt_count": 0,
            "lifecycle_status": "not_started",
            "session_active": False,
            "session_stopped": False,
            "last_receipt_kind": "none",
            "last_source_kind": "none",
        }

    class FakePreflight:
        def to_json_ready(self) -> dict[str, object]:
            calls.append("preflight-json")
            return {
                "preflight_kind": "crash_recovery_session_preflight",
                "session_id": SESSION_ID,
                "session_dir": SESSION_ID,
                "recovery_status": "partial",
                "existing_count": 1,
                "missing_count": len(ALLOWED_ARCHIVE_ARTIFACT_FILENAMES) - 1,
                "total_existing_size_bytes": 2,
                "artifacts": [
                    {
                        "kind": "runtime_log",
                        "filename": RUNTIME_FILENAME,
                        "exists": True,
                        "size_bytes": 2,
                    },
                    *[
                        {
                            "kind": f"kind-{index}",
                            "filename": filename,
                            "exists": False,
                        }
                        for index, filename in enumerate(NON_RUNTIME_FILENAMES)
                    ],
                ],
            }

    def fake_recovery_preflight(archive_root: Path, session_id: str) -> FakePreflight:
        calls.append(f"preflight:{archive_root}:{session_id}")
        return FakePreflight()

    monkeypatch.setattr(
        recovery_decision,
        "build_stored_session_window_runtime_summary",
        fake_runtime_summary,
    )
    monkeypatch.setattr(
        recovery_decision,
        "build_crash_recovery_session_preflight",
        fake_recovery_preflight,
    )

    decision = build_stored_session_window_recovery_decision(
        Path("archive-root"),
        SESSION_ID,
    )

    assert calls == [
        "runtime:archive-root:session-001",
        "preflight:archive-root:session-001",
        "preflight-json",
    ]
    assert decision["archive_recovery_status"] == "empty"
    assert decision["recovery_decision"] == "no_action"


def test_runtime_failure_does_not_call_recovery_preflight(monkeypatch) -> None:
    calls: list[str] = []

    def fake_runtime_summary(archive_root: Path, session_id: str) -> dict[str, object]:
        calls.append("runtime")
        raise ValueError("private path")

    def fake_recovery_preflight(archive_root: Path, session_id: str) -> object:
        calls.append("preflight")
        raise AssertionError("preflight must not run after runtime failure")

    monkeypatch.setattr(
        recovery_decision,
        "build_stored_session_window_runtime_summary",
        fake_runtime_summary,
    )
    monkeypatch.setattr(
        recovery_decision,
        "build_crash_recovery_session_preflight",
        fake_recovery_preflight,
    )

    _assert_decision_error(Path("archive-root"), SESSION_ID)
    assert calls == ["runtime"]


def test_recovery_decision_source_stays_read_only_and_non_executing() -> None:
    source = inspect.getsource(recovery_decision)

    assert "build_stored_session_window_runtime_summary(" in source
    assert "build_crash_recovery_session_preflight(" in source
    for forbidden_fragment in (
        "write_stored_session_window",
        "load_course_schedule",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "_create_schema",
        "ScheduledStartClock",
        "build_session_window_confirmation",
        "build_session_window_start_authorization",
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
        "archive_export",
        "archive_delete",
        '.open("',
        ".open('",
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
