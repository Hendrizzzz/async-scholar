from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from async_scholar import session_window_runtime_summary as runtime_summary
from async_scholar.session_window_runtime_summary import (
    STORED_SESSION_WINDOW_RUNTIME_SUMMARY_ERROR,
    build_stored_session_window_runtime_summary,
)

SESSION_ID = "session-001"
SUMMARY_KIND = "stored_session_window_runtime_summary"


def _runtime_file(
    *records: dict[str, object],
    root: Path,
    raw_text: str | None = None,
) -> tuple[Path, Path]:
    archive_root = root / "archive"
    session_dir = archive_root / SESSION_ID
    runtime_path = session_dir / "runtime.jsonl"
    session_dir.mkdir(parents=True)
    if raw_text is None:
        raw_text = "".join(_compact_line(record) for record in records)
    runtime_path.write_text(raw_text, encoding="utf-8")
    return archive_root, runtime_path


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


def _assert_summary_error(archive_root: object, session_id: object) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_stored_session_window_runtime_summary(archive_root, session_id)  # type: ignore[arg-type]
    assert str(exc_info.value) == STORED_SESSION_WINDOW_RUNTIME_SUMMARY_ERROR


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


def _relative_paths(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def test_build_summary_for_empty_runtime(tmp_path: Path) -> None:
    archive_root, _runtime_path = _runtime_file(root=tmp_path)

    summary = build_stored_session_window_runtime_summary(archive_root, SESSION_ID)

    assert summary == {
        "summary_kind": SUMMARY_KIND,
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


def test_build_summary_for_start_only(tmp_path: Path) -> None:
    archive_root, _runtime_path = _runtime_file(_start_receipt(), root=tmp_path)

    summary = build_stored_session_window_runtime_summary(archive_root, SESSION_ID)

    assert summary == {
        "summary_kind": SUMMARY_KIND,
        "session_id": SESSION_ID,
        "runtime_record_count": 1,
        "start_receipt_count": 1,
        "stop_receipt_count": 0,
        "lifecycle_status": "started",
        "session_active": True,
        "session_stopped": False,
        "last_receipt_kind": "stored_session_window_start_receipt",
        "last_source_kind": "file",
    }


def test_build_summary_for_start_then_stop(tmp_path: Path) -> None:
    archive_root, _runtime_path = _runtime_file(
        _start_receipt(),
        _stop_receipt(),
        root=tmp_path,
    )

    summary = build_stored_session_window_runtime_summary(archive_root, SESSION_ID)

    assert summary == {
        "summary_kind": SUMMARY_KIND,
        "session_id": SESSION_ID,
        "runtime_record_count": 2,
        "start_receipt_count": 1,
        "stop_receipt_count": 1,
        "lifecycle_status": "stopped",
        "session_active": False,
        "session_stopped": True,
        "last_receipt_kind": "stored_session_window_stop_receipt",
        "last_source_kind": "file",
    }


@pytest.mark.parametrize(
    ("records", "expected_counts", "last_kind"),
    (
        pytest.param(
            (_stop_receipt(),),
            (0, 1),
            "stored_session_window_stop_receipt",
            id="stop-only",
        ),
        pytest.param(
            (_stop_receipt(), _start_receipt()),
            (1, 1),
            "stored_session_window_start_receipt",
            id="stop-before-start",
        ),
        pytest.param(
            (_start_receipt(), _start_receipt()),
            (2, 0),
            "stored_session_window_start_receipt",
            id="repeated-starts",
        ),
        pytest.param(
            (_start_receipt(), _stop_receipt(), _stop_receipt()),
            (1, 2),
            "stored_session_window_stop_receipt",
            id="repeated-stops",
        ),
        pytest.param(
            (_start_receipt(), _stop_receipt(), _start_receipt()),
            (2, 1),
            "stored_session_window_start_receipt",
            id="start-after-stop",
        ),
    ),
)
def test_valid_but_impossible_ordering_is_inconsistent(
    tmp_path: Path,
    records: tuple[dict[str, object], ...],
    expected_counts: tuple[int, int],
    last_kind: str,
) -> None:
    archive_root, _runtime_path = _runtime_file(*records, root=tmp_path)

    summary = build_stored_session_window_runtime_summary(archive_root, SESSION_ID)

    assert summary["lifecycle_status"] == "inconsistent"
    assert summary["session_active"] is False
    assert summary["session_stopped"] is False
    assert summary["start_receipt_count"] == expected_counts[0]
    assert summary["stop_receipt_count"] == expected_counts[1]
    assert summary["last_receipt_kind"] == last_kind


@pytest.mark.parametrize(
    "line",
    (
        pytest.param("\n", id="blank-line"),
        pytest.param("{bad json}\n", id="malformed-json"),
        pytest.param(
            json.dumps(_start_receipt(), sort_keys=True) + "\n",
            id="non-compact-json",
        ),
        pytest.param(_compact_line(_start_receipt(private_token="secret")), id="extra"),
        pytest.param(
            _compact_line({"receipt_kind": "stored_session_window_pause_receipt"}),
            id="unknown-kind",
        ),
        pytest.param(
            _compact_line(_start_receipt(session_id="session-002")),
            id="mismatched-session",
        ),
        pytest.param(
            _compact_line(_start_receipt(runtime_record_written=False)),
            id="runtime-record-not-written",
        ),
        pytest.param(
            _compact_line(
                _start_receipt(
                    status="blocked",
                    authorized=False,
                    authorized_start_count=0,
                    blocked_start_count=1,
                    block_reason="confirmation_declined",
                )
            ),
            id="non-authorized-start",
        ),
        pytest.param(
            _compact_line(_stop_receipt(status="disabled", enabled=False)),
            id="non-enabled-stop",
        ),
    ),
)
def test_rejects_invalid_or_private_runtime_lines(
    tmp_path: Path,
    line: str,
) -> None:
    archive_root, _runtime_path = _runtime_file(raw_text=line, root=tmp_path)

    _assert_summary_error(archive_root, SESSION_ID)


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

    _assert_summary_error(archive_root, session_id)


def test_rejects_missing_archive_root(tmp_path: Path) -> None:
    _assert_summary_error(tmp_path / "missing-archive", SESSION_ID)


def test_rejects_non_directory_archive_root(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-file"
    archive_root.write_text("", encoding="utf-8")

    _assert_summary_error(archive_root, SESSION_ID)


def test_rejects_url_file_uri_unc_blank_and_control_archive_roots() -> None:
    for archive_root in (
        "",
        " ",
        "https://example.test/archive",
        "file:///C:/Users/student/archive",
        "\\\\server\\share\\archive",
        "archive\nroot",
    ):
        _assert_summary_error(archive_root, SESSION_ID)


def test_rejects_missing_session_directory(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive"
    archive_root.mkdir()

    _assert_summary_error(archive_root, SESSION_ID)


def test_rejects_missing_runtime_file(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive"
    (archive_root / SESSION_ID).mkdir(parents=True)

    _assert_summary_error(archive_root, SESSION_ID)


def test_rejects_non_file_runtime_path(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive"
    runtime_path = archive_root / SESSION_ID / "runtime.jsonl"
    runtime_path.mkdir(parents=True)

    _assert_summary_error(archive_root, SESSION_ID)


def test_rejects_symlink_archive_root(tmp_path: Path) -> None:
    real_root = tmp_path / "real-archive"
    link_root = tmp_path / "archive-link"
    real_root.mkdir()
    _symlink_or_skip(real_root, link_root, target_is_directory=True)

    _assert_summary_error(link_root, SESSION_ID)


def test_rejects_symlink_session_directory(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive"
    real_session_dir = tmp_path / "real-session"
    link_session_dir = archive_root / SESSION_ID
    archive_root.mkdir()
    real_session_dir.mkdir()
    _symlink_or_skip(real_session_dir, link_session_dir, target_is_directory=True)

    _assert_summary_error(archive_root, SESSION_ID)


def test_rejects_symlink_runtime_file(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive"
    session_dir = archive_root / SESSION_ID
    real_runtime_path = tmp_path / "real-runtime.jsonl"
    link_runtime_path = session_dir / "runtime.jsonl"
    session_dir.mkdir(parents=True)
    real_runtime_path.write_text("", encoding="utf-8")
    _symlink_or_skip(real_runtime_path, link_runtime_path)

    _assert_summary_error(archive_root, SESSION_ID)


def test_reader_does_not_create_modify_or_delete_files(tmp_path: Path) -> None:
    archive_root, runtime_path = _runtime_file(_start_receipt(), root=tmp_path)
    before_text = runtime_path.read_text(encoding="utf-8")
    before_paths = _relative_paths(tmp_path)

    build_stored_session_window_runtime_summary(archive_root, SESSION_ID)

    assert runtime_path.read_text(encoding="utf-8") == before_text
    assert _relative_paths(tmp_path) == before_paths


def test_summary_output_is_allowlisted_and_does_not_leak_source_details(
    tmp_path: Path,
) -> None:
    archive_root, _runtime_path = _runtime_file(_start_receipt(), root=tmp_path)
    private_file = archive_root / SESSION_ID / "events.jsonl"
    private_file.write_text(
        "Confidential Systems token secret auth profile transcript audio browser",
        encoding="utf-8",
    )

    summary = build_stored_session_window_runtime_summary(archive_root, SESSION_ID)
    encoded_summary = json.dumps(summary, sort_keys=True).lower()

    assert tuple(summary) == (
        "summary_kind",
        "session_id",
        "runtime_record_count",
        "start_receipt_count",
        "stop_receipt_count",
        "lifecycle_status",
        "session_active",
        "session_stopped",
        "last_receipt_kind",
        "last_source_kind",
    )
    for forbidden_fragment in (
        "course_id",
        "clock",
        "scheduled",
        "private",
        "confidential",
        "token",
        "secret",
        "auth",
        "profile",
        "transcript",
        "audio",
        "browser",
        "events.jsonl",
        "runtime.jsonl",
        str(tmp_path).lower(),
    ):
        assert forbidden_fragment not in encoded_summary


def test_runtime_summary_source_stays_read_only_and_non_executing() -> None:
    source = inspect.getsource(runtime_summary)

    assert 'open("r"' in source
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
        '.open("a',
        ".open('a",
        '.open("w',
        ".open('w",
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
