from __future__ import annotations

import inspect
import json
from copy import deepcopy
from pathlib import Path

import pytest

from async_scholar import session_window_stop_receipt as receipt


def _enabled_preview() -> dict[str, object]:
    return {
        "status": "enabled",
        "course_id": "cs101",
        "source_kind": "file",
        "selected_class_time_index": 0,
        "scheduled_day_of_week": "monday",
        "scheduled_local_start_time": "09:00",
        "stop_after_minutes": 75,
        "enabled": True,
    }


def _disabled_preview() -> dict[str, object]:
    payload = deepcopy(_enabled_preview())
    payload.update({"status": "disabled", "enabled": False})
    return payload


def test_enabled_stop_preview_appends_one_compact_sorted_runtime_receipt(
    tmp_path: Path,
) -> None:
    archive_root, runtime_path = _existing_runtime(tmp_path)
    existing_line = '{"existing":true}\n'
    runtime_path.write_text(existing_line, encoding="utf-8")

    result = receipt.write_stored_session_window_stop_receipt(
        _enabled_preview(),
        archive_root,
        "session-001",
    )

    expected = {
        "course_id": "cs101",
        "enabled": True,
        "receipt_kind": "stored_session_window_stop_receipt",
        "runtime_record_written": True,
        "scheduled_day_of_week": "monday",
        "scheduled_local_start_time": "09:00",
        "selected_class_time_index": 0,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "enabled",
        "stop_after_minutes": 75,
    }
    expected_line = json.dumps(expected, sort_keys=True, separators=(",", ":"))
    assert result == expected
    assert runtime_path.read_text(encoding="utf-8") == (
        f"{existing_line}{expected_line}\n"
    )
    assert runtime_path.read_text(encoding="utf-8").splitlines() == [
        '{"existing":true}',
        expected_line,
    ]
    assert " " not in expected_line
    _assert_receipt_payload_is_safe(result, runtime_path, tmp_path)


def test_disabled_stop_preview_returns_no_write_without_touching_archive(
    tmp_path: Path,
) -> None:
    archive_root = tmp_path / "missing-archive"

    result = receipt.write_stored_session_window_stop_receipt(
        _disabled_preview(),
        archive_root,
        "session-001",
    )

    assert result == {
        "course_id": "cs101",
        "enabled": False,
        "receipt_kind": "stored_session_window_stop_receipt",
        "runtime_record_written": False,
        "scheduled_day_of_week": "monday",
        "scheduled_local_start_time": "09:00",
        "selected_class_time_index": 0,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "disabled",
        "stop_after_minutes": 75,
    }
    assert not archive_root.exists()
    assert list(tmp_path.iterdir()) == []


def test_malformed_stop_preview_revalidates_before_filesystem_touch(
    tmp_path: Path,
) -> None:
    archive_root = tmp_path / "missing-archive-root"
    payload = _enabled_preview()
    payload["meeting_url"] = "https://meet.example.edu/token-secret"

    with pytest.raises(ValueError) as exc_info:
        receipt.write_stored_session_window_stop_receipt(
            payload,
            archive_root,
            "session-001",
        )

    assert str(exc_info.value) == receipt.STORED_SESSION_WINDOW_STOP_RECEIPT_ERROR
    assert not archive_root.exists()


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("status", "authorized"),
        ("course_id", "../private"),
        ("source_kind", "browser"),
        ("selected_class_time_index", True),
        ("scheduled_day_of_week", "funday"),
        ("scheduled_local_start_time", "99:99"),
        ("stop_after_minutes", 0),
        ("enabled", "true"),
    ],
)
def test_malformed_stop_preview_values_are_rejected_before_filesystem_touch(
    tmp_path: Path,
    field_name: str,
    value: object,
) -> None:
    archive_root = tmp_path / "missing-archive-root"
    payload = _enabled_preview()
    payload[field_name] = value

    with pytest.raises(ValueError) as exc_info:
        receipt.write_stored_session_window_stop_receipt(
            payload,
            archive_root,
            "session-001",
        )

    assert str(exc_info.value) == receipt.STORED_SESSION_WINDOW_STOP_RECEIPT_ERROR
    assert not archive_root.exists()


def test_missing_stop_preview_key_is_rejected_before_filesystem_touch(
    tmp_path: Path,
) -> None:
    archive_root = tmp_path / "missing-archive-root"
    payload = _enabled_preview()
    del payload["stop_after_minutes"]

    with pytest.raises(ValueError) as exc_info:
        receipt.write_stored_session_window_stop_receipt(
            payload,
            archive_root,
            "session-001",
        )

    assert str(exc_info.value) == receipt.STORED_SESSION_WINDOW_STOP_RECEIPT_ERROR
    assert not archive_root.exists()


def test_status_and_enabled_must_match_before_filesystem_touch(
    tmp_path: Path,
) -> None:
    archive_root = tmp_path / "missing-archive-root"
    payload = _enabled_preview()
    payload["enabled"] = False

    with pytest.raises(ValueError) as exc_info:
        receipt.write_stored_session_window_stop_receipt(
            payload,
            archive_root,
            "session-001",
        )

    assert str(exc_info.value) == receipt.STORED_SESSION_WINDOW_STOP_RECEIPT_ERROR
    assert not archive_root.exists()


@pytest.mark.parametrize(
    "session_id",
    [
        "",
        "   ",
        ".",
        "..",
        "session/001",
        "session\\001",
        "session:001",
        "https://example.edu/session",
        "file:///tmp/session",
        "session\x00id",
    ],
)
def test_unsafe_session_id_is_rejected_before_filesystem_touch(
    tmp_path: Path,
    session_id: str,
) -> None:
    archive_root = tmp_path / "missing-archive-root"

    with pytest.raises(ValueError) as exc_info:
        receipt.write_stored_session_window_stop_receipt(
            _enabled_preview(),
            archive_root,
            session_id,
        )

    assert str(exc_info.value) == receipt.STORED_SESSION_WINDOW_STOP_RECEIPT_ERROR
    assert not archive_root.exists()


@pytest.mark.parametrize(
    "archive_root",
    [
        "",
        "   ",
        "https://example.edu/archive",
        "file:///tmp/archive",
        "\\\\server\\share\\archive",
    ],
)
def test_enabled_receipt_rejects_unsafe_archive_root_text(
    tmp_path: Path,
    archive_root: str,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        receipt.write_stored_session_window_stop_receipt(
            _enabled_preview(),
            archive_root,
            "session-001",
        )

    assert str(exc_info.value) == receipt.STORED_SESSION_WINDOW_STOP_RECEIPT_ERROR
    assert list(tmp_path.iterdir()) == []


def test_enabled_receipt_rejects_traversal_archive_root(tmp_path: Path) -> None:
    safe_parent = tmp_path / "safe-parent"
    safe_parent.mkdir()
    unsafe_root = safe_parent / ".." / "safe-parent"

    with pytest.raises(ValueError):
        receipt.write_stored_session_window_stop_receipt(
            _enabled_preview(),
            unsafe_root,
            "session-001",
        )

    assert list(safe_parent.iterdir()) == []


def test_enabled_receipt_requires_existing_archive_directory(
    tmp_path: Path,
) -> None:
    archive_root = tmp_path / "missing"

    with pytest.raises(ValueError):
        receipt.write_stored_session_window_stop_receipt(
            _enabled_preview(),
            archive_root,
            "session-001",
        )

    assert not archive_root.exists()


def test_enabled_receipt_requires_existing_session_directory(
    tmp_path: Path,
) -> None:
    archive_root = tmp_path / "archive"
    archive_root.mkdir()

    with pytest.raises(ValueError):
        receipt.write_stored_session_window_stop_receipt(
            _enabled_preview(),
            archive_root,
            "session-001",
        )

    assert list(archive_root.iterdir()) == []


def test_enabled_receipt_requires_existing_runtime_file(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)

    with pytest.raises(ValueError):
        receipt.write_stored_session_window_stop_receipt(
            _enabled_preview(),
            archive_root,
            "session-001",
        )

    assert list(session_dir.iterdir()) == []


def test_enabled_receipt_rejects_archive_root_file(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive"
    archive_root.write_text("private root placeholder", encoding="utf-8")

    with pytest.raises(ValueError):
        receipt.write_stored_session_window_stop_receipt(
            _enabled_preview(),
            archive_root,
            "session-001",
        )

    assert archive_root.read_text(encoding="utf-8") == "private root placeholder"


def test_enabled_receipt_rejects_existing_session_non_directory(
    tmp_path: Path,
) -> None:
    archive_root = tmp_path / "archive"
    archive_root.mkdir()
    (archive_root / "session-001").write_text("private", encoding="utf-8")

    with pytest.raises(ValueError):
        receipt.write_stored_session_window_stop_receipt(
            _enabled_preview(),
            archive_root,
            "session-001",
        )

    assert (archive_root / "session-001").read_text(encoding="utf-8") == "private"


def test_enabled_receipt_rejects_existing_runtime_non_file(
    tmp_path: Path,
) -> None:
    archive_root = tmp_path / "archive"
    runtime_path = archive_root / "session-001" / "runtime.jsonl"
    runtime_path.mkdir(parents=True)

    with pytest.raises(ValueError):
        receipt.write_stored_session_window_stop_receipt(
            _enabled_preview(),
            archive_root,
            "session-001",
        )

    assert runtime_path.is_dir()
    assert list(runtime_path.iterdir()) == []


def test_enabled_receipt_rejects_symlink_archive_root(tmp_path: Path) -> None:
    real_root = tmp_path / "real-archive"
    link_root = tmp_path / "archive-link"
    real_root.mkdir()
    _symlink_or_skip(link_root, real_root, target_is_directory=True)

    with pytest.raises(ValueError):
        receipt.write_stored_session_window_stop_receipt(
            _enabled_preview(),
            link_root,
            "session-001",
        )

    assert list(real_root.iterdir()) == []


def test_enabled_receipt_rejects_symlink_session_dir(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive"
    target_dir = tmp_path / "target-session"
    archive_root.mkdir()
    target_dir.mkdir()
    _symlink_or_skip(
        archive_root / "session-001",
        target_dir,
        target_is_directory=True,
    )

    with pytest.raises(ValueError):
        receipt.write_stored_session_window_stop_receipt(
            _enabled_preview(),
            archive_root,
            "session-001",
        )

    assert list(target_dir.iterdir()) == []


def test_enabled_receipt_rejects_symlink_runtime_path(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive"
    session_dir = archive_root / "session-001"
    target_file = tmp_path / "target-runtime.jsonl"
    session_dir.mkdir(parents=True)
    target_file.write_text("private", encoding="utf-8")
    _symlink_or_skip(session_dir / "runtime.jsonl", target_file)

    with pytest.raises(ValueError):
        receipt.write_stored_session_window_stop_receipt(
            _enabled_preview(),
            archive_root,
            "session-001",
        )

    assert target_file.read_text(encoding="utf-8") == "private"


def test_receipt_writer_source_has_no_execution_or_delivery_surfaces() -> None:
    source = inspect.getsource(receipt)

    for forbidden_fragment in (
        "session_window_start",
        "list_course_schedule",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "ScheduledStartClock",
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
        "alert_dispatch",
        "telegram",
        "desktop_notifier",
        "archive_export",
        "archive_delete",
        "autonomous_participation",
        "academic_answer",
        ".mkdir(",
        ".write_text(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
        "pyproject",
        "uv.lock",
    ):
        assert forbidden_fragment not in source


def _existing_runtime(tmp_path: Path) -> tuple[Path, Path]:
    archive_root = tmp_path / "archive"
    session_dir = archive_root / "session-001"
    runtime_path = session_dir / "runtime.jsonl"
    session_dir.mkdir(parents=True)
    runtime_path.write_text("", encoding="utf-8")
    return archive_root, runtime_path


def _symlink_or_skip(
    link_path: Path,
    target_path: Path,
    *,
    target_is_directory: bool = False,
) -> None:
    try:
        link_path.symlink_to(target_path, target_is_directory=target_is_directory)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlinks unavailable: {exc}")


def _assert_receipt_payload_is_safe(
    payload: dict[str, object],
    runtime_path: Path,
    tmp_path: Path,
) -> None:
    combined = (
        json.dumps(payload, sort_keys=True)
        + "\n"
        + runtime_path.read_text(encoding="utf-8")
    ).lower()
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "db_path",
        "archive_root",
        "title",
        "instructor",
        "meeting",
        "meet.example",
        "timezone",
        "transcript",
        "audio",
        "browser",
        "auth state",
        "auth_state",
        "auth-profile",
        "cookie",
        "profile",
        "token",
        "secret",
        "sql",
        "traceback",
        "alert body",
        "alert title",
        "live delivery",
        "gate d",
        "product promise",
        "runtime.jsonl",
    ):
        assert forbidden_fragment not in combined
