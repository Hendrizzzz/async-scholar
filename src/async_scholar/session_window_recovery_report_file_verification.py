from __future__ import annotations

import re
import stat
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

from async_scholar.session_window_recovery_report import (
    build_stored_session_window_recovery_report,
)

STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_VERIFICATION_ERROR = (
    "stored session window recovery report file verification could not be built"
)

_REPORT_FILENAME = "stored-session-window-recovery-report.md"
_VERIFICATION_KIND = "stored_session_window_recovery_report_file_verification"
_MAX_SESSION_IDS = 25
_MAX_REPORT_BYTES = 1024 * 1024
_SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
_LIFECYCLE_VALUES = frozenset(("not_started", "started", "stopped", "inconsistent"))
_ARCHIVE_STATUS_VALUES = frozenset(("empty", "partial", "complete"))
_REVIEW_MAPPING = {
    "no_action": ("not_required", "none", "leave_archive_unchanged"),
    "inspect_active_session": (
        "required",
        "active_session_runtime",
        "inspect_runtime_metadata",
    ),
    "inspect_partial_archive": (
        "required",
        "partial_archive_metadata",
        "inspect_archive_metadata",
    ),
    "manual_review": (
        "required",
        "inconsistent_runtime",
        "escalate_manual_review",
    ),
}


def build_stored_session_window_recovery_report_file_verification(
    session_ids: Sequence[str],
    archive_root: str | Path,
    output_root: str | Path,
) -> dict[str, object]:
    try:
        safe_session_ids = _materialize_session_ids(session_ids)
        archive_root_path = _existing_directory(archive_root)
        output_root_path = _existing_directory(output_root)
        if _is_relative_to(output_root_path, archive_root_path):
            _fail()

        report_path = output_root_path / _REPORT_FILENAME
        report_metadata = _report_metadata(
            report_path, output_root_path, archive_root_path
        )
        expected_report = _validated_report(
            build_stored_session_window_recovery_report(
                archive_root_path,
                safe_session_ids,
            ),
            safe_session_ids,
        )
        expected_bytes = expected_report.encode("utf-8")

        if report_metadata is None:
            return _receipt(
                safe_session_ids,
                exists=False,
                matches_expected=False,
                size_bytes=0,
                expected_size_bytes=len(expected_bytes),
            )

        before_stat = report_metadata
        actual_bytes = _read_report_bytes(report_path)
        after_stat = _checked_report_stat(
            report_path,
            output_root_path,
            archive_root_path,
        )
        if (
            not _same_file_identity(before_stat, after_stat)
            or before_stat.st_size != after_stat.st_size
            or len(actual_bytes) != after_stat.st_size
        ):
            _fail()

        actual_bytes.decode("utf-8")
        return _receipt(
            safe_session_ids,
            exists=True,
            matches_expected=actual_bytes == expected_bytes,
            size_bytes=len(actual_bytes),
            expected_size_bytes=len(expected_bytes),
        )
    except Exception:
        raise ValueError(
            STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_VERIFICATION_ERROR
        ) from None


def _receipt(
    session_ids: tuple[str, ...],
    *,
    exists: bool,
    matches_expected: bool,
    size_bytes: int,
    expected_size_bytes: int,
) -> dict[str, object]:
    return {
        "verification_kind": _VERIFICATION_KIND,
        "session_count": len(session_ids),
        "relative_path": _REPORT_FILENAME,
        "exists": exists,
        "matches_expected": matches_expected,
        "size_bytes": size_bytes,
        "expected_size_bytes": expected_size_bytes,
    }


def _materialize_session_ids(session_ids: object) -> tuple[str, ...]:
    if isinstance(session_ids, (str, bytes, bytearray)) or not isinstance(
        session_ids,
        Sequence,
    ):
        _fail()
    reported_length = len(session_ids)
    if reported_length < 1 or reported_length > _MAX_SESSION_IDS:
        _fail()

    raw_session_ids: list[object] = []
    for session_id in session_ids:
        raw_session_ids.append(session_id)
        if (
            len(raw_session_ids) > reported_length
            or len(raw_session_ids) > _MAX_SESSION_IDS
        ):
            _fail()
    if len(raw_session_ids) != reported_length:
        _fail()

    safe_session_ids = tuple(
        _clean_session_id(session_id) for session_id in raw_session_ids
    )
    if len(frozenset(safe_session_ids)) != len(safe_session_ids):
        _fail()
    return safe_session_ids


def _existing_directory(root: str | Path) -> Path:
    if not isinstance(root, (str, Path)):
        _fail()
    raw_root_text = str(root)
    if (
        not raw_root_text
        or raw_root_text.strip() != raw_root_text
        or _has_control_character(raw_root_text)
        or _has_forbidden_uri_or_unc(raw_root_text)
        or _has_traversal_part(raw_root_text)
    ):
        _fail()
    raw_root = Path(root)
    if raw_root.is_symlink():
        _fail()
    root_path = raw_root.resolve(strict=True)
    if not root_path.is_dir():
        _fail()
    return root_path


def _report_metadata(
    report_path: Path,
    output_root: Path,
    archive_root: Path,
):
    try:
        report_stat = report_path.lstat()
    except FileNotFoundError:
        return None
    return _validated_report_stat(report_path, report_stat, output_root, archive_root)


def _checked_report_stat(
    report_path: Path,
    output_root: Path,
    archive_root: Path,
):
    report_stat = report_path.lstat()
    return _validated_report_stat(report_path, report_stat, output_root, archive_root)


def _validated_report_stat(
    report_path: Path,
    report_stat: object,
    output_root: Path,
    archive_root: Path,
):
    if (
        stat.S_ISLNK(report_stat.st_mode)
        or not stat.S_ISREG(report_stat.st_mode)
        or report_stat.st_size > _MAX_REPORT_BYTES
    ):
        _fail()
    resolved_report_path = report_path.resolve(strict=True)
    if not _is_relative_to(
        resolved_report_path,
        output_root,
    ) or _is_relative_to(
        resolved_report_path,
        archive_root,
    ):
        _fail()
    return report_stat


def _read_report_bytes(report_path: Path) -> bytes:
    with report_path.open("rb") as report_file:
        report_bytes = report_file.read(_MAX_REPORT_BYTES + 1)
    if len(report_bytes) > _MAX_REPORT_BYTES:
        _fail()
    return report_bytes


def _same_file_identity(before_stat: object, after_stat: object) -> bool:
    before_identity = _portable_identity(before_stat)
    after_identity = _portable_identity(after_stat)
    return before_identity == after_identity


def _portable_identity(report_stat: object) -> tuple[object, ...]:
    device = getattr(report_stat, "st_dev", None)
    inode = getattr(report_stat, "st_ino", None)
    if isinstance(device, int) and isinstance(inode, int) and inode != 0:
        return ("inode", device, inode)
    return (
        "metadata",
        getattr(report_stat, "st_mode", None),
        getattr(report_stat, "st_size", None),
        getattr(report_stat, "st_mtime_ns", None),
        getattr(report_stat, "st_ctime_ns", None),
    )


def _validated_report(report: object, expected_session_ids: tuple[str, ...]) -> str:
    if (
        type(report) is not str
        or not report
        or not report.endswith("\n")
        or "\r" in report
        or _has_forbidden_report_control_character(report)
    ):
        _fail()
    lines = report[:-1].split("\n")
    expected_line_count = 6 + (len(expected_session_ids) * 9)
    if len(lines) != expected_line_count:
        _fail()
    if lines[:2] != ["# Stored Session Window Recovery Report", ""]:
        _fail()

    review_count = _count_line(lines[2], "Review count: ")
    manual_review_required_count = _count_line(
        lines[3],
        "Manual review required: ",
    )
    required_count = _count_line(lines[4], "Required: ")
    not_required_count = _count_line(lines[5], "Not required: ")
    if (
        review_count != len(expected_session_ids)
        or manual_review_required_count != required_count
        or required_count + not_required_count != review_count
    ):
        _fail()

    observed_required_count = 0
    for index, session_id in enumerate(expected_session_ids):
        observed_required_count += _validate_review_lines(
            lines[6 + (index * 9) : 15 + (index * 9)],
            session_id,
        )
    if observed_required_count != required_count:
        _fail()
    return report


def _validate_review_lines(lines: list[str], expected_session_id: str) -> int:
    if lines[0] != "" or lines[1] != f"## {expected_session_id}":
        _fail()
    if lines[2] != f"- Session ID: {expected_session_id}":
        _fail()
    lifecycle_status = _line_value(lines[3], "- Lifecycle status: ")
    if lifecycle_status not in _LIFECYCLE_VALUES:
        _fail()
    archive_status = _line_value(lines[4], "- Archive status: ")
    if archive_status not in _ARCHIVE_STATUS_VALUES:
        _fail()
    recovery_decision = _line_value(lines[5], "- Recovery decision: ")
    if recovery_decision not in _REVIEW_MAPPING:
        _fail()
    review_status = _line_value(lines[6], "- Review status: ")
    review_reason = _line_value(lines[7], "- Review reason: ")
    safe_next_review_action = _line_value(lines[8], "- Safe next review action: ")
    if (
        review_status,
        review_reason,
        safe_next_review_action,
    ) != _REVIEW_MAPPING[recovery_decision]:
        _fail()
    return 1 if review_status == "required" else 0


def _count_line(line: str, prefix: str) -> int:
    raw_value = _line_value(line, prefix)
    if not raw_value.isdecimal():
        _fail()
    return int(raw_value)


def _line_value(line: str, prefix: str) -> str:
    if not line.startswith(prefix):
        _fail()
    value = line[len(prefix) :]
    if type(value) is not str or not value:
        _fail()
    return value


def _clean_session_id(value: object) -> str:
    if type(value) is not str:
        _fail()
    if (
        not value
        or value.strip() != value
        or _has_control_character(value)
        or value in {".", ".."}
        or "/" in value
        or "\\" in value
        or ":" in value
        or _has_forbidden_uri_or_unc(value)
        or _has_traversal_part(value)
        or _SESSION_ID_PATTERN.fullmatch(value) is None
    ):
        _fail()
    return value


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _has_control_character(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _has_forbidden_report_control_character(value: str) -> bool:
    return any(
        (ord(character) < 32 and character != "\n") or ord(character) == 127
        for character in value
    )


def _has_forbidden_uri_or_unc(value: str) -> bool:
    normalized_path = value.replace("/", "\\")
    lower_value = value.lower()
    return (
        "://" in lower_value
        or lower_value.startswith("file:")
        or normalized_path.startswith("\\\\")
    )


def _has_traversal_part(value: str) -> bool:
    return any(part == ".." for part in value.replace("\\", "/").split("/"))


def _fail() -> NoReturn:
    raise ValueError(STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_VERIFICATION_ERROR)
