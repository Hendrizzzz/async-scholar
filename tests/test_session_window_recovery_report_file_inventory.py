from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from async_scholar import (
    session_window_recovery_report_file_inventory as recovery_report_inventory,
)
from async_scholar.session_window_recovery_report_file_inventory import (
    STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_INVENTORY_ERROR,
    build_stored_session_window_recovery_report_file_inventory,
)


def _assert_inventory_error(archive_root: object, output_root: object) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_stored_session_window_recovery_report_file_inventory(
            archive_root,  # type: ignore[arg-type]
            output_root,  # type: ignore[arg-type]
        )
    assert (
        str(exc_info.value)
        == STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_INVENTORY_ERROR
    )


def test_inventory_existing_recovery_report_file_returns_safe_metadata(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    output_root.mkdir()
    report_path = output_root / "stored-session-window-recovery-report.md"
    report_text = "# Stored Session Window Recovery Report\nprivate body\n"
    report_bytes = report_text.encode("utf-8")
    report_path.write_bytes(report_bytes)

    receipt = build_stored_session_window_recovery_report_file_inventory(
        archive_root,
        output_root,
    )

    assert receipt == {
        "exists": True,
        "inventory_kind": "stored_session_window_recovery_report_file_inventory",
        "relative_path": "stored-session-window-recovery-report.md",
        "size_bytes": len(report_bytes),
    }


def test_inventory_missing_recovery_report_file_returns_safe_absent_receipt(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    output_root.mkdir()

    receipt = build_stored_session_window_recovery_report_file_inventory(
        archive_root,
        output_root,
    )

    assert receipt == {
        "exists": False,
        "inventory_kind": "stored_session_window_recovery_report_file_inventory",
        "relative_path": "stored-session-window-recovery-report.md",
        "size_bytes": 0,
    }


@pytest.mark.parametrize(
    ("archive_root_name", "output_root_name"),
    (
        pytest.param("archive", "archive", id="same-root"),
        pytest.param("archive", "archive/reports", id="inside-archive-root"),
    ),
)
def test_inventory_rejects_output_root_inside_archive_root(
    tmp_path,
    archive_root_name: str,
    output_root_name: str,
) -> None:
    archive_root = tmp_path / archive_root_name
    output_root = tmp_path / output_root_name
    output_root.mkdir(parents=True)
    archive_root.mkdir(exist_ok=True)

    _assert_inventory_error(archive_root, output_root)


@pytest.mark.parametrize(
    "output_root_setup",
    (
        pytest.param("missing", id="missing-output-root"),
        pytest.param("file", id="file-output-root"),
    ),
)
def test_inventory_requires_existing_output_directory(
    tmp_path,
    output_root_setup: str,
) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    if output_root_setup == "file":
        output_root.write_text("not a directory", encoding="utf-8")

    _assert_inventory_error(archive_root, output_root)


@pytest.mark.parametrize(
    "archive_root_setup",
    (
        pytest.param("missing", id="missing-archive-root"),
        pytest.param("file", id="file-archive-root"),
    ),
)
def test_inventory_requires_existing_archive_directory(
    tmp_path,
    archive_root_setup: str,
) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    output_root.mkdir()
    if archive_root_setup == "file":
        archive_root.write_text("not a directory", encoding="utf-8")

    _assert_inventory_error(archive_root, output_root)


@pytest.mark.parametrize("root_kind", ("archive", "output"))
@pytest.mark.parametrize(
    ("root_value", "root_label"),
    (
        pytest.param("", "blank", id="blank"),
        pytest.param(" archive", "whitespace", id="leading-whitespace"),
        pytest.param("archive ", "whitespace", id="trailing-whitespace"),
        pytest.param("https://example.test/archive", "uri", id="uri"),
        pytest.param("file://archive", "file-uri", id="file-uri"),
        pytest.param("file:archive", "file-scheme", id="file-scheme"),
        pytest.param("\\\\server\\share\\archive", "unc", id="unc"),
        pytest.param("archive\x1froot", "control", id="control"),
        pytest.param(None, "traversal", id="traversal"),
    ),
)
def test_inventory_rejects_unsafe_root_spelling(
    tmp_path,
    root_kind: str,
    root_value: str | None,
    root_label: str,
) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    output_root.mkdir()
    if root_label == "traversal":
        unsafe_root = (
            archive_root / ".." / "archive"
            if root_kind == "archive"
            else output_root / ".." / "reports"
        )
    else:
        unsafe_root = root_value

    if root_kind == "archive":
        _assert_inventory_error(unsafe_root, output_root)
    else:
        _assert_inventory_error(archive_root, unsafe_root)


@pytest.mark.parametrize("root_kind", ("archive", "output"))
def test_inventory_rejects_symlink_roots(tmp_path, root_kind: str) -> None:
    real_archive_root = tmp_path / "archive"
    real_output_root = tmp_path / "reports"
    real_archive_root.mkdir()
    real_output_root.mkdir()
    archive_root = real_archive_root
    output_root = real_output_root
    link_root = tmp_path / f"{root_kind}-link"
    link_target = real_archive_root if root_kind == "archive" else real_output_root
    try:
        link_root.symlink_to(link_target, target_is_directory=True)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"directory symlink unavailable: {exc}")
    if root_kind == "archive":
        archive_root = link_root
    else:
        output_root = link_root

    _assert_inventory_error(archive_root, output_root)


@pytest.mark.parametrize("target_kind", ("missing", "inside-output", "inside-archive"))
def test_inventory_rejects_report_file_symlink(tmp_path, target_kind: str) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    output_root.mkdir()
    if target_kind == "missing":
        symlink_target = output_root / "missing-report.md"
    elif target_kind == "inside-output":
        symlink_target = output_root / "actual-report.md"
        symlink_target.write_text("private", encoding="utf-8")
    else:
        symlink_target = archive_root / "actual-report.md"
        symlink_target.write_text("private", encoding="utf-8")
    report_path = output_root / "stored-session-window-recovery-report.md"
    try:
        report_path.symlink_to(symlink_target)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"file symlink unavailable: {exc}")

    _assert_inventory_error(archive_root, output_root)


def test_inventory_rejects_fixed_report_directory(tmp_path) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    output_root.mkdir()
    (output_root / "stored-session-window-recovery-report.md").mkdir()

    _assert_inventory_error(archive_root, output_root)


def test_inventory_sanitizes_stat_failure(tmp_path, monkeypatch) -> None:
    archive_root = tmp_path / "archive-token-secret-auth-profile"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    output_root.mkdir()
    (output_root / "stored-session-window-recovery-report.md").write_bytes(b"private")
    original_lstat = Path.lstat

    def fail_report_lstat(path: Path, *args: object, **kwargs: object):
        if path.name == "stored-session-window-recovery-report.md":
            raise OSError("C:\\Users\\student\\token-secret-auth-profile")
        return original_lstat(path, *args, **kwargs)

    monkeypatch.setattr(recovery_report_inventory.Path, "lstat", fail_report_lstat)

    _assert_inventory_error(archive_root, output_root)


def test_inventory_sanitizes_missing_probe_stat_failure(tmp_path, monkeypatch) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    output_root.mkdir()
    original_exists = Path.exists
    original_lstat = Path.lstat

    def false_report_exists(path: Path, *args: object, **kwargs: object) -> bool:
        if path.name == "stored-session-window-recovery-report.md":
            return False
        return original_exists(path, *args, **kwargs)

    def fail_report_lstat(path: Path, *args: object, **kwargs: object):
        if path.name == "stored-session-window-recovery-report.md":
            raise OSError("C:\\Users\\student\\token-secret-auth-profile")
        return original_lstat(path, *args, **kwargs)

    monkeypatch.setattr(recovery_report_inventory.Path, "exists", false_report_exists)
    monkeypatch.setattr(recovery_report_inventory.Path, "lstat", fail_report_lstat)

    _assert_inventory_error(archive_root, output_root)


def test_inventory_receipt_excludes_private_data(tmp_path) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    output_root.mkdir()
    (output_root / "stored-session-window-recovery-report.md").write_bytes(
        b"# Stored Session Window Recovery Report\n"
        b"session-001 transcript token secret auth profile runtime.jsonl\n"
    )

    receipt = build_stored_session_window_recovery_report_file_inventory(
        archive_root,
        output_root,
    )

    assert tuple(receipt) == (
        "inventory_kind",
        "relative_path",
        "exists",
        "size_bytes",
    )
    combined_receipt = repr(receipt).lower()
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "session-001",
        "transcript",
        "token",
        "secret",
        "auth",
        "profile",
        "runtime.jsonl",
        "source",
        "event",
        "url",
        "cookie",
        "recording",
        "generated media",
        "traceback",
        "# stored session",
    ):
        assert forbidden_fragment not in combined_receipt


def test_inventory_source_stays_read_only_and_narrow() -> None:
    source = inspect.getsource(recovery_report_inventory)

    assert "stored-session-window-recovery-report.md" in source
    for forbidden_fragment in (
        "build_stored_session_window_recovery_report(",
        "write_stored_session_window_recovery_report_file(",
        "build_stored_session_window_recovery_review_batch",
        "build_stored_session_window_recovery_review(",
        "build_stored_session_window_recovery_decision",
        "build_stored_session_window_runtime_summary",
        "build_crash_recovery_session_preflight",
        "list_course_schedule_session_window_inputs",
        "load_course_schedule",
        "save_course_schedule",
        "initialize_course_schedule_store",
        "ScheduleConfig",
        "CourseMetadata",
        "ScheduledStartClock",
        "execute_archive",
        "archive_export",
        "archive_delete",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".write_bytes(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
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
        "participation",
        "academic_answer",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in source
