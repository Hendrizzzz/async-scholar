from __future__ import annotations

import inspect
import io
from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest

from async_scholar import (
    session_window_recovery_report_file_verification as recovery_report_verification,
)
from async_scholar.session_window_recovery_report_file_verification import (
    STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_VERIFICATION_ERROR,
    build_stored_session_window_recovery_report_file_verification,
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
REPORT_PATH = "stored-session-window-recovery-report.md"
MAX_REPORT_BYTES = 1024 * 1024


class _LongerThanReportedSequence(Sequence[str]):
    def __len__(self) -> int:
        return 1

    def __iter__(self) -> Iterator[str]:
        return iter(("session-001", "session-002"))

    def __getitem__(self, index: int) -> str:
        return ("session-001", "session-002")[index]


class _TrackingBytesIO(io.BytesIO):
    def __init__(self, payload: bytes):
        super().__init__(payload)
        self.read_sizes: list[int] = []

    def read(self, size: int = -1) -> bytes:
        self.read_sizes.append(size)
        return super().read(size)


def _assert_verification_error(
    session_ids: object,
    archive_root: object,
    output_root: object,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_stored_session_window_recovery_report_file_verification(
            session_ids,  # type: ignore[arg-type]
            archive_root,  # type: ignore[arg-type]
            output_root,  # type: ignore[arg-type]
        )
    assert (
        str(exc_info.value)
        == STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_VERIFICATION_ERROR
    )


def _roots(tmp_path: Path) -> tuple[Path, Path]:
    archive_root = tmp_path / "archive"
    output_root = tmp_path / "reports"
    archive_root.mkdir()
    output_root.mkdir()
    return archive_root, output_root


def _stub_expected_report(monkeypatch, report: object = REPORT) -> dict[str, object]:
    delegated: dict[str, object] = {}

    def fake_build(archive_root_arg: Path, session_ids_arg: tuple[str, ...]) -> object:
        delegated["archive_root"] = archive_root_arg
        delegated["session_ids"] = session_ids_arg
        return report

    monkeypatch.setattr(
        recovery_report_verification,
        "build_stored_session_window_recovery_report",
        fake_build,
    )
    return delegated


def test_verification_matching_report_returns_safe_receipt(
    tmp_path,
    monkeypatch,
) -> None:
    archive_root, output_root = _roots(tmp_path)
    report_bytes = REPORT.encode("utf-8")
    (output_root / REPORT_PATH).write_bytes(report_bytes)
    delegated = _stub_expected_report(monkeypatch)

    receipt = build_stored_session_window_recovery_report_file_verification(
        ("session-001", "session-002"),
        archive_root,
        output_root,
    )

    assert tuple(receipt) == (
        "verification_kind",
        "session_count",
        "relative_path",
        "exists",
        "matches_expected",
        "size_bytes",
        "expected_size_bytes",
    )
    assert receipt == {
        "verification_kind": (
            "stored_session_window_recovery_report_file_verification"
        ),
        "session_count": 2,
        "relative_path": REPORT_PATH,
        "exists": True,
        "matches_expected": True,
        "size_bytes": len(report_bytes),
        "expected_size_bytes": len(report_bytes),
    }
    assert delegated == {
        "archive_root": archive_root,
        "session_ids": ("session-001", "session-002"),
    }


def test_verification_mismatching_report_returns_safe_mismatch(
    tmp_path,
    monkeypatch,
) -> None:
    archive_root, output_root = _roots(tmp_path)
    actual_bytes = b"# Stored Session Window Recovery Report\nprivate mismatch\n"
    (output_root / REPORT_PATH).write_bytes(actual_bytes)
    _stub_expected_report(monkeypatch)

    receipt = build_stored_session_window_recovery_report_file_verification(
        ("session-001", "session-002"),
        archive_root,
        output_root,
    )

    assert receipt == {
        "verification_kind": (
            "stored_session_window_recovery_report_file_verification"
        ),
        "session_count": 2,
        "relative_path": REPORT_PATH,
        "exists": True,
        "matches_expected": False,
        "size_bytes": len(actual_bytes),
        "expected_size_bytes": len(REPORT.encode("utf-8")),
    }


def test_verification_missing_report_returns_safe_absent_receipt(
    tmp_path,
    monkeypatch,
) -> None:
    archive_root, output_root = _roots(tmp_path)
    _stub_expected_report(monkeypatch)

    receipt = build_stored_session_window_recovery_report_file_verification(
        ("session-001", "session-002"),
        archive_root,
        output_root,
    )

    assert receipt == {
        "verification_kind": (
            "stored_session_window_recovery_report_file_verification"
        ),
        "session_count": 2,
        "relative_path": REPORT_PATH,
        "exists": False,
        "matches_expected": False,
        "size_bytes": 0,
        "expected_size_bytes": len(REPORT.encode("utf-8")),
    }


@pytest.mark.parametrize(
    "session_ids",
    (
        pytest.param((), id="empty"),
        pytest.param("session-001", id="bare-string"),
        pytest.param(b"session-001", id="bare-bytes"),
        pytest.param(["session-001", 123], id="non-string"),
        pytest.param(["session-001", "session-001"], id="duplicates"),
        pytest.param(["../session-001"], id="unsafe"),
        pytest.param((f"session-{index:03d}" for index in range(2)), id="generator"),
        pytest.param(tuple(f"session-{index:03d}" for index in range(26)), id="large"),
        pytest.param(_LongerThanReportedSequence(), id="lying-sequence"),
    ),
)
def test_verification_rejects_unsafe_session_id_batches(
    tmp_path,
    monkeypatch,
    session_ids: object,
) -> None:
    archive_root, output_root = _roots(tmp_path)
    _stub_expected_report(monkeypatch)

    _assert_verification_error(session_ids, archive_root, output_root)


@pytest.mark.parametrize(
    ("archive_root_name", "output_root_name"),
    (
        pytest.param("archive", "archive", id="same-root"),
        pytest.param("archive", "archive/reports", id="inside-archive-root"),
    ),
)
def test_verification_rejects_output_root_inside_archive_root(
    tmp_path,
    monkeypatch,
    archive_root_name: str,
    output_root_name: str,
) -> None:
    archive_root = tmp_path / archive_root_name
    output_root = tmp_path / output_root_name
    output_root.mkdir(parents=True)
    archive_root.mkdir(exist_ok=True)
    _stub_expected_report(monkeypatch)

    _assert_verification_error(
        ("session-001", "session-002"), archive_root, output_root
    )


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
def test_verification_rejects_unsafe_root_spelling(
    tmp_path,
    monkeypatch,
    root_kind: str,
    root_value: str | None,
    root_label: str,
) -> None:
    archive_root, output_root = _roots(tmp_path)
    if root_label == "traversal":
        unsafe_root = (
            archive_root / ".." / "archive"
            if root_kind == "archive"
            else output_root / ".." / "reports"
        )
    else:
        unsafe_root = root_value
    _stub_expected_report(monkeypatch)

    if root_kind == "archive":
        _assert_verification_error(("session-001",), unsafe_root, output_root)
    else:
        _assert_verification_error(("session-001",), archive_root, unsafe_root)


@pytest.mark.parametrize("root_kind", ("archive", "output"))
def test_verification_rejects_symlink_roots(
    tmp_path,
    monkeypatch,
    root_kind: str,
) -> None:
    real_archive_root, real_output_root = _roots(tmp_path)
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
    _stub_expected_report(monkeypatch)

    _assert_verification_error(
        ("session-001", "session-002"), archive_root, output_root
    )


@pytest.mark.parametrize("target_kind", ("missing", "inside-output", "inside-archive"))
def test_verification_rejects_report_file_symlink(
    tmp_path,
    monkeypatch,
    target_kind: str,
) -> None:
    archive_root, output_root = _roots(tmp_path)
    if target_kind == "missing":
        symlink_target = output_root / "missing-report.md"
    elif target_kind == "inside-output":
        symlink_target = output_root / "actual-report.md"
        symlink_target.write_text("private", encoding="utf-8")
    else:
        symlink_target = archive_root / "actual-report.md"
        symlink_target.write_text("private", encoding="utf-8")
    report_path = output_root / REPORT_PATH
    try:
        report_path.symlink_to(symlink_target)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"file symlink unavailable: {exc}")
    _stub_expected_report(monkeypatch)

    _assert_verification_error(
        ("session-001", "session-002"),
        archive_root,
        output_root,
    )


def test_verification_rejects_fixed_report_directory(tmp_path, monkeypatch) -> None:
    archive_root, output_root = _roots(tmp_path)
    (output_root / REPORT_PATH).mkdir()
    _stub_expected_report(monkeypatch)

    _assert_verification_error(("session-001",), archive_root, output_root)


def test_verification_rejects_oversized_report(tmp_path, monkeypatch) -> None:
    archive_root, output_root = _roots(tmp_path)
    (output_root / REPORT_PATH).write_bytes(b"x" * (MAX_REPORT_BYTES + 1))
    _stub_expected_report(monkeypatch)

    _assert_verification_error(("session-001",), archive_root, output_root)


def test_verification_rejects_actual_read_over_cap(
    tmp_path,
    monkeypatch,
) -> None:
    archive_root, output_root = _roots(tmp_path)
    report_path = output_root / REPORT_PATH
    report_path.write_bytes(b"small")
    _stub_expected_report(monkeypatch)
    tracked_file = _TrackingBytesIO(b"x" * (MAX_REPORT_BYTES + 1))
    original_open = Path.open

    def fake_open(path: Path, *args: object, **kwargs: object):
        if path == report_path:
            return tracked_file
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(recovery_report_verification.Path, "open", fake_open)

    _assert_verification_error(
        ("session-001", "session-002"),
        archive_root,
        output_root,
    )
    assert tracked_file.read_sizes
    assert max(tracked_file.read_sizes) <= MAX_REPORT_BYTES + 1


def test_verification_rejects_file_swap_after_lstat(
    tmp_path,
    monkeypatch,
) -> None:
    archive_root, output_root = _roots(tmp_path)
    report_path = output_root / REPORT_PATH
    report_path.write_text(REPORT, encoding="utf-8")
    _stub_expected_report(monkeypatch)
    original_open = Path.open
    swapped = False

    def swapping_open(path: Path, *args: object, **kwargs: object):
        nonlocal swapped
        if path == report_path and not swapped:
            swapped = True
            path.unlink()
            path.write_text("# swapped private report\n", encoding="utf-8")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(recovery_report_verification.Path, "open", swapping_open)

    _assert_verification_error(
        ("session-001", "session-002"), archive_root, output_root
    )


def test_verification_sanitizes_unreadable_report(
    tmp_path,
    monkeypatch,
) -> None:
    archive_root, output_root = _roots(tmp_path)
    report_path = output_root / REPORT_PATH
    report_path.write_text(REPORT, encoding="utf-8")
    _stub_expected_report(monkeypatch)
    original_open = Path.open

    def failing_open(path: Path, *args: object, **kwargs: object):
        if path == report_path:
            raise OSError("C:\\Users\\student\\token-secret-auth-profile")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(recovery_report_verification.Path, "open", failing_open)

    _assert_verification_error(
        ("session-001", "session-002"), archive_root, output_root
    )


def test_verification_rejects_non_utf8_report(tmp_path, monkeypatch) -> None:
    archive_root, output_root = _roots(tmp_path)
    (output_root / REPORT_PATH).write_bytes(b"\xff\xfe\xfa")
    _stub_expected_report(monkeypatch)

    _assert_verification_error(("session-001",), archive_root, output_root)


def test_verification_sanitizes_delegated_report_failure(
    tmp_path,
    monkeypatch,
) -> None:
    archive_root, output_root = _roots(tmp_path)
    (output_root / REPORT_PATH).write_text(REPORT, encoding="utf-8")

    def fake_build(archive_root_arg: Path, session_ids: tuple[str, ...]) -> str:
        raise RuntimeError("C:\\Users\\student\\token-secret-auth-profile")

    monkeypatch.setattr(
        recovery_report_verification,
        "build_stored_session_window_recovery_report",
        fake_build,
    )

    _assert_verification_error(
        ("session-001", "session-002"), archive_root, output_root
    )


@pytest.mark.parametrize(
    "delegated_report",
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
def test_verification_sanitizes_malformed_delegated_report(
    tmp_path,
    monkeypatch,
    delegated_report: object,
) -> None:
    archive_root, output_root = _roots(tmp_path)
    (output_root / REPORT_PATH).write_text(REPORT, encoding="utf-8")
    _stub_expected_report(monkeypatch, delegated_report)

    _assert_verification_error(
        ("session-001", "session-002"), archive_root, output_root
    )


def test_verification_receipt_excludes_private_data(tmp_path, monkeypatch) -> None:
    archive_root, output_root = _roots(tmp_path)
    (output_root / REPORT_PATH).write_text(
        "# Stored Session Window Recovery Report\n"
        "session-001 transcript token secret auth profile runtime.jsonl\n",
        encoding="utf-8",
    )
    _stub_expected_report(monkeypatch)

    receipt = build_stored_session_window_recovery_report_file_verification(
        ("session-001", "session-002"),
        archive_root,
        output_root,
    )

    combined_receipt = repr(receipt).lower()
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "session-001",
        "session-002",
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


def test_verification_does_not_create_modify_or_delete_files(
    tmp_path,
    monkeypatch,
) -> None:
    archive_root, output_root = _roots(tmp_path)
    archive_marker = archive_root / "keep.txt"
    output_marker = output_root / "keep.txt"
    report_path = output_root / REPORT_PATH
    archive_marker.write_text("archive", encoding="utf-8")
    output_marker.write_text("output", encoding="utf-8")
    report_path.write_text(REPORT, encoding="utf-8")
    _stub_expected_report(monkeypatch)

    build_stored_session_window_recovery_report_file_verification(
        ("session-001", "session-002"),
        archive_root,
        output_root,
    )

    assert archive_marker.read_text(encoding="utf-8") == "archive"
    assert output_marker.read_text(encoding="utf-8") == "output"
    assert report_path.read_text(encoding="utf-8") == REPORT
    assert sorted(path.name for path in archive_root.iterdir()) == ["keep.txt"]
    assert sorted(path.name for path in output_root.iterdir()) == [
        "keep.txt",
        REPORT_PATH,
    ]


def test_verification_source_stays_read_only_and_narrow() -> None:
    source = inspect.getsource(recovery_report_verification)

    assert "build_stored_session_window_recovery_report" in source
    assert "stored-session-window-recovery-report.md" in source
    for forbidden_fragment in (
        "write_stored_session_window_recovery_report_file",
        "build_stored_session_window_recovery_report_file_inventory",
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
