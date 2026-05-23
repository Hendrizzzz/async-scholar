from __future__ import annotations

import inspect
import json
from copy import deepcopy
from pathlib import Path

import pytest

from async_scholar import session_window_start_receipt as receipt


def _authorized_summary() -> dict[str, object]:
    return {
        "status": "authorized",
        "session_id": "session-001",
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


def _declined_summary() -> dict[str, object]:
    payload = deepcopy(_authorized_summary())
    payload.update(
        {
            "status": "blocked",
            "confirmation_response": "declined",
            "confirmation_verified": False,
            "authorized": False,
            "authorized_start_count": 0,
            "blocked_start_count": 1,
            "block_reason": "confirmation_declined",
            "courses": [],
        }
    )
    return payload


def _disabled_summary() -> dict[str, object]:
    payload = deepcopy(_authorized_summary())
    payload.update(
        {
            "status": "disabled",
            "due_count": 0,
            "ready_to_start": False,
            "confirmation_required": False,
            "confirmation_status": "disabled",
            "confirmation_verified": False,
            "authorized": False,
            "authorized_start_count": 0,
            "blocked_start_count": 0,
            "block_reason": "disabled",
            "courses": [],
        }
    )
    return payload


def _not_required_summary() -> dict[str, object]:
    payload = deepcopy(_authorized_summary())
    payload.update(
        {
            "status": "not_required",
            "clock_day_of_week": "tuesday",
            "due_count": 0,
            "ready_to_start": False,
            "confirmation_required": False,
            "confirmation_status": "not_required",
            "confirmation_verified": False,
            "authorized": False,
            "authorized_start_count": 0,
            "blocked_start_count": 0,
            "block_reason": "confirmation_not_required",
            "courses": [],
        }
    )
    return payload


def test_authorized_summary_writes_one_compact_runtime_receipt(
    tmp_path: Path,
) -> None:
    archive_root = tmp_path / "archive"
    archive_root.mkdir()

    result = receipt.write_stored_session_window_start_receipt(
        _authorized_summary(),
        archive_root,
    )

    runtime_path = archive_root / "session-001" / "runtime.jsonl"
    expected = {
        "authorized": True,
        "authorized_start_count": 1,
        "block_reason": "none",
        "blocked_start_count": 0,
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "confirmation_required": True,
        "confirmation_response": "confirmed",
        "confirmation_status": "required",
        "confirmation_verified": True,
        "course_count": 1,
        "due_count": 1,
        "ready_to_start": True,
        "receipt_kind": "stored_session_window_start_receipt",
        "runtime_record_written": True,
        "session_id": "session-001",
        "source_kind": "file",
        "status": "authorized",
    }
    expected_line = json.dumps(expected, sort_keys=True, separators=(",", ":"))
    assert result == expected
    assert runtime_path.is_file()
    assert runtime_path.read_text(encoding="utf-8") == f"{expected_line}\n"
    assert sorted(path.name for path in archive_root.iterdir()) == ["session-001"]
    assert sorted(path.name for path in (archive_root / "session-001").iterdir()) == [
        "runtime.jsonl"
    ]
    _assert_receipt_payload_is_safe(result, runtime_path, tmp_path)


@pytest.mark.parametrize(
    "authorization_summary",
    [_declined_summary(), _disabled_summary(), _not_required_summary()],
)
def test_non_authorized_summaries_do_not_touch_archive(
    tmp_path: Path,
    authorization_summary: dict[str, object],
) -> None:
    archive_root = tmp_path / "archive"
    archive_root.mkdir()

    result = receipt.write_stored_session_window_start_receipt(
        authorization_summary,
        archive_root,
    )

    assert result["runtime_record_written"] is False
    assert result["authorized"] is False
    assert not (archive_root / "session-001").exists()
    assert list(archive_root.iterdir()) == []


def test_malformed_authorization_revalidates_before_filesystem_touch(
    tmp_path: Path,
) -> None:
    archive_root = tmp_path / "missing-archive-root"
    payload = _authorized_summary()
    payload["meeting_url"] = "https://meet.example.edu/token-secret"

    with pytest.raises(ValueError) as exc_info:
        receipt.write_stored_session_window_start_receipt(payload, archive_root)

    assert str(exc_info.value) == receipt.STORED_SESSION_WINDOW_START_RECEIPT_ERROR
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
def test_authorized_receipt_rejects_unsafe_archive_root_text(
    tmp_path: Path,
    archive_root: str,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        receipt.write_stored_session_window_start_receipt(
            _authorized_summary(),
            archive_root,
        )

    assert str(exc_info.value) == receipt.STORED_SESSION_WINDOW_START_RECEIPT_ERROR
    assert list(tmp_path.iterdir()) == []


def test_authorized_receipt_rejects_traversal_archive_root(
    tmp_path: Path,
) -> None:
    safe_parent = tmp_path / "safe-parent"
    safe_parent.mkdir()
    unsafe_root = safe_parent / ".." / "safe-parent"

    with pytest.raises(ValueError):
        receipt.write_stored_session_window_start_receipt(
            _authorized_summary(),
            unsafe_root,
        )

    assert list(safe_parent.iterdir()) == []


def test_authorized_receipt_requires_existing_archive_directory(
    tmp_path: Path,
) -> None:
    archive_root = tmp_path / "missing"

    with pytest.raises(ValueError):
        receipt.write_stored_session_window_start_receipt(
            _authorized_summary(),
            archive_root,
        )

    assert not archive_root.exists()


def test_authorized_receipt_rejects_archive_root_file(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive"
    archive_root.write_text("private root placeholder", encoding="utf-8")

    with pytest.raises(ValueError):
        receipt.write_stored_session_window_start_receipt(
            _authorized_summary(),
            archive_root,
        )

    assert archive_root.read_text(encoding="utf-8") == "private root placeholder"


def test_authorized_receipt_rejects_unsafe_session_id(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive"
    archive_root.mkdir()
    payload = _authorized_summary()
    payload["session_id"] = ".."

    with pytest.raises(ValueError):
        receipt.write_stored_session_window_start_receipt(payload, archive_root)

    assert list(archive_root.iterdir()) == []


def test_authorized_receipt_rejects_existing_session_non_directory(
    tmp_path: Path,
) -> None:
    archive_root = tmp_path / "archive"
    archive_root.mkdir()
    (archive_root / "session-001").write_text("private", encoding="utf-8")

    with pytest.raises(ValueError):
        receipt.write_stored_session_window_start_receipt(
            _authorized_summary(),
            archive_root,
        )

    assert (archive_root / "session-001").read_text(encoding="utf-8") == "private"


def test_authorized_receipt_rejects_existing_runtime_non_file(
    tmp_path: Path,
) -> None:
    archive_root = tmp_path / "archive"
    runtime_path = archive_root / "session-001" / "runtime.jsonl"
    runtime_path.mkdir(parents=True)

    with pytest.raises(ValueError):
        receipt.write_stored_session_window_start_receipt(
            _authorized_summary(),
            archive_root,
        )

    assert runtime_path.is_dir()
    assert list(runtime_path.iterdir()) == []


def test_authorized_receipt_rejects_symlink_archive_root(tmp_path: Path) -> None:
    real_root = tmp_path / "real-archive"
    link_root = tmp_path / "archive-link"
    real_root.mkdir()
    _symlink_or_skip(link_root, real_root, target_is_directory=True)

    with pytest.raises(ValueError):
        receipt.write_stored_session_window_start_receipt(
            _authorized_summary(),
            link_root,
        )

    assert list(real_root.iterdir()) == []


def test_authorized_receipt_rejects_symlink_session_dir(tmp_path: Path) -> None:
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
        receipt.write_stored_session_window_start_receipt(
            _authorized_summary(),
            archive_root,
        )

    assert list(target_dir.iterdir()) == []


def test_authorized_receipt_rejects_symlink_runtime_path(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive"
    session_dir = archive_root / "session-001"
    target_file = tmp_path / "target-runtime.jsonl"
    session_dir.mkdir(parents=True)
    target_file.write_text("private", encoding="utf-8")
    _symlink_or_skip(session_dir / "runtime.jsonl", target_file)

    with pytest.raises(ValueError):
        receipt.write_stored_session_window_start_receipt(
            _authorized_summary(),
            archive_root,
        )

    assert target_file.read_text(encoding="utf-8") == "private"


def test_receipt_writer_source_has_no_execution_or_delivery_surfaces() -> None:
    source = inspect.getsource(receipt)

    assert "session_window_start_authorization_safe_summary" in source
    for forbidden_fragment in (
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
        "pyproject",
        "uv.lock",
    ):
        assert forbidden_fragment not in source


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
