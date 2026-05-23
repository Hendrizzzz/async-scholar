from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from async_scholar import (
    session_window_recovery_report_file as recovery_report_file,
)
from async_scholar.session_window_recovery_report_file import (
    STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_ERROR,
    write_stored_session_window_recovery_report_file,
)

REPORT = (
    "# Stored Session Window Recovery Report\n"
    "\n"
    "Review count: 2\n"
    "Manual review required: 1\n"
    "Required: 1\n"
    "Not required: 1\n"
    "\n"
    "## session-001\n"
    "- Session ID: session-001\n"
    "- Lifecycle status: not_started\n"
    "- Archive status: empty\n"
    "- Recovery decision: no_action\n"
    "- Review status: not_required\n"
    "- Review reason: none\n"
    "- Safe next review action: leave_archive_unchanged\n"
    "\n"
    "## session-002\n"
    "- Session ID: session-002\n"
    "- Lifecycle status: inconsistent\n"
    "- Archive status: partial\n"
    "- Recovery decision: manual_review\n"
    "- Review status: required\n"
    "- Review reason: inconsistent_runtime\n"
    "- Safe next review action: escalate_manual_review\n"
)


def _assert_writer_error(
    archive_root: object,
    output_root: object,
    session_ids: object,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        write_stored_session_window_recovery_report_file(
            archive_root,  # type: ignore[arg-type]
            output_root,  # type: ignore[arg-type]
            session_ids,  # type: ignore[arg-type]
        )
    assert str(exc_info.value) == STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_ERROR


def test_write_recovery_report_file_writes_fixed_markdown_and_safe_receipt(
    tmp_path,
    monkeypatch,
) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    output_root.mkdir()
    delegated: dict[str, object] = {}

    def fake_build(archive_root_arg: Path, session_ids: tuple[str, ...]) -> str:
        delegated["archive_root"] = archive_root_arg
        delegated["session_ids"] = session_ids
        return REPORT

    monkeypatch.setattr(
        recovery_report_file,
        "build_stored_session_window_recovery_report",
        fake_build,
    )

    receipt = write_stored_session_window_recovery_report_file(
        archive_root,
        output_root,
        ("session-001", "session-002"),
    )

    report_path = output_root / "stored-session-window-recovery-report.md"
    assert report_path.read_text(encoding="utf-8") == REPORT
    assert receipt == {
        "bytes_written": len(REPORT.encode("utf-8")),
        "relative_path": "stored-session-window-recovery-report.md",
        "session_count": 2,
        "write_kind": "stored_session_window_recovery_report_file",
    }
    assert delegated == {
        "archive_root": archive_root,
        "session_ids": ("session-001", "session-002"),
    }


def test_write_recovery_report_file_never_overwrites_existing_file(
    tmp_path,
    monkeypatch,
) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    output_root.mkdir()
    destination = output_root / "stored-session-window-recovery-report.md"
    destination.write_text("existing private report", encoding="utf-8")
    monkeypatch.setattr(
        recovery_report_file,
        "build_stored_session_window_recovery_report",
        lambda archive_root_arg, session_ids: REPORT,
    )

    _assert_writer_error(archive_root, output_root, ("session-001",))

    assert destination.read_text(encoding="utf-8") == "existing private report"


@pytest.mark.parametrize(
    ("archive_root_name", "output_root_name"),
    (
        pytest.param("archive", "archive", id="same-root"),
        pytest.param("archive", "archive/child", id="inside-archive-root"),
    ),
)
def test_write_recovery_report_file_rejects_archive_root_writes(
    tmp_path,
    monkeypatch,
    archive_root_name: str,
    output_root_name: str,
) -> None:
    archive_root = tmp_path / archive_root_name
    output_root = tmp_path / output_root_name
    output_root.mkdir(parents=True)
    archive_root.mkdir(exist_ok=True)
    monkeypatch.setattr(
        recovery_report_file,
        "build_stored_session_window_recovery_report",
        lambda archive_root_arg, session_ids: REPORT,
    )

    _assert_writer_error(archive_root, output_root, ("session-001",))

    assert not (output_root / "stored-session-window-recovery-report.md").exists()


@pytest.mark.parametrize(
    "output_root_setup",
    (
        pytest.param("missing", id="missing-output-root"),
        pytest.param("file", id="file-output-root"),
    ),
)
def test_write_recovery_report_file_requires_existing_output_directory(
    tmp_path,
    monkeypatch,
    output_root_setup: str,
) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    if output_root_setup == "file":
        output_root.write_text("not a directory", encoding="utf-8")
    monkeypatch.setattr(
        recovery_report_file,
        "build_stored_session_window_recovery_report",
        lambda archive_root_arg, session_ids: REPORT,
    )

    _assert_writer_error(archive_root, output_root, ("session-001",))


@pytest.mark.parametrize("root_kind", ("archive", "output"))
@pytest.mark.parametrize(
    ("root_value", "root_label"),
    (
        pytest.param("", "blank", id="blank"),
        pytest.param("file://archive", "uri", id="uri"),
        pytest.param("\\\\server\\share\\archive", "unc", id="unc"),
        pytest.param("archive\x1froot", "control", id="control"),
        pytest.param(None, "traversal", id="traversal"),
    ),
)
def test_write_recovery_report_file_rejects_unsafe_root_spelling(
    tmp_path,
    monkeypatch,
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
    monkeypatch.setattr(
        recovery_report_file,
        "build_stored_session_window_recovery_report",
        lambda archive_root_arg, session_ids: REPORT,
    )

    if root_kind == "archive":
        _assert_writer_error(unsafe_root, output_root, ("session-001", "session-002"))
    else:
        _assert_writer_error(archive_root, unsafe_root, ("session-001", "session-002"))

    assert not (output_root / "stored-session-window-recovery-report.md").exists()


@pytest.mark.parametrize("root_kind", ("archive", "output"))
def test_write_recovery_report_file_rejects_symlink_roots(
    tmp_path,
    monkeypatch,
    root_kind: str,
) -> None:
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
    monkeypatch.setattr(
        recovery_report_file,
        "build_stored_session_window_recovery_report",
        lambda archive_root_arg, session_ids: REPORT,
    )

    _assert_writer_error(archive_root, output_root, ("session-001",))

    assert not (real_output_root / "stored-session-window-recovery-report.md").exists()


@pytest.mark.parametrize("target_kind", ("inside-output", "inside-archive"))
def test_write_recovery_report_file_rejects_existing_destination_symlink(
    tmp_path,
    monkeypatch,
    target_kind: str,
) -> None:
    output_parent = tmp_path / "reports"
    output_parent.mkdir()
    if target_kind == "inside-output":
        archive_root = tmp_path / "archive"
        output_root = output_parent
        symlink_target = output_root / "missing-target.md"
    else:
        archive_root = output_parent / "archive"
        output_root = output_parent
        symlink_target = archive_root / "missing-target.md"
    archive_root.mkdir()
    destination = output_root / "stored-session-window-recovery-report.md"
    try:
        destination.symlink_to(symlink_target)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"file symlink unavailable: {exc}")
    monkeypatch.setattr(
        recovery_report_file,
        "build_stored_session_window_recovery_report",
        lambda archive_root_arg, session_ids: REPORT,
    )

    _assert_writer_error(archive_root, output_root, ("session-001", "session-002"))

    assert not symlink_target.exists()
    assert destination.is_symlink()


def test_write_recovery_report_file_sanitizes_delegated_failure(
    tmp_path,
    monkeypatch,
) -> None:
    archive_root = tmp_path / "archive-token-secret-auth-profile"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    output_root.mkdir()

    def fake_build(archive_root_arg: Path, session_ids: tuple[str, ...]) -> str:
        raise RuntimeError("C:\\Users\\student\\token-secret-auth-profile")

    monkeypatch.setattr(
        recovery_report_file,
        "build_stored_session_window_recovery_report",
        fake_build,
    )

    _assert_writer_error(archive_root, output_root, ("session-001",))
    assert not (output_root / "stored-session-window-recovery-report.md").exists()


@pytest.mark.parametrize(
    "report",
    (
        pytest.param("", id="empty"),
        pytest.param(b"# bytes report\n", id="bytes"),
        pytest.param("# Missing final newline", id="missing-newline"),
        pytest.param(REPORT + "- Transcript: private words\n", id="extra-line"),
        pytest.param(
            REPORT.replace("- Archive status: empty", "- Archive status: unknown"),
            id="bad-enum",
        ),
        pytest.param(
            REPORT.replace("## session-001", "## session-999"),
            id="mismatched-session-heading",
        ),
    ),
)
def test_write_recovery_report_file_sanitizes_malformed_delegated_report(
    tmp_path,
    monkeypatch,
    report: object,
) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    output_root.mkdir()
    monkeypatch.setattr(
        recovery_report_file,
        "build_stored_session_window_recovery_report",
        lambda archive_root_arg, session_ids: report,
    )

    _assert_writer_error(archive_root, output_root, ("session-001",))
    assert not (output_root / "stored-session-window-recovery-report.md").exists()


def test_write_recovery_report_file_rejects_private_delegated_report_content(
    tmp_path,
    monkeypatch,
) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    output_root.mkdir()
    private_report = REPORT + "C:\\Users\\student\\token-secret-auth-profile\n"
    monkeypatch.setattr(
        recovery_report_file,
        "build_stored_session_window_recovery_report",
        lambda archive_root_arg, session_ids: private_report,
    )

    _assert_writer_error(archive_root, output_root, ("session-001", "session-002"))

    assert not (output_root / "stored-session-window-recovery-report.md").exists()


def test_write_recovery_report_file_receipt_excludes_private_data(
    tmp_path,
    monkeypatch,
) -> None:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    output_root.mkdir()
    monkeypatch.setattr(
        recovery_report_file,
        "build_stored_session_window_recovery_report",
        lambda archive_root_arg, session_ids: REPORT,
    )

    receipt = write_stored_session_window_recovery_report_file(
        archive_root, output_root, ("session-001", "session-002")
    )

    combined_receipt = repr(receipt).lower()
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "token",
        "secret",
        "auth",
        "profile",
        "transcript",
        "audio",
        "# stored session",
        "session-001",
        "runtime.jsonl",
        "source",
        "event",
        "url",
        "cookie",
        "traceback",
    ):
        assert forbidden_fragment not in combined_receipt


def test_write_recovery_report_file_source_stays_narrow() -> None:
    source = inspect.getsource(recovery_report_file)

    assert "build_stored_session_window_recovery_report" in source
    assert 'open("x"' in source
    for forbidden_fragment in (
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
