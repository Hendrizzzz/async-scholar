from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

from async_scholar.session_window_recovery_report import (
    build_stored_session_window_recovery_report,
)

STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_ERROR = (
    "stored session window recovery report file could not be written"
)

_REPORT_FILENAME = "stored-session-window-recovery-report.md"
_WRITE_KIND = "stored_session_window_recovery_report_file"
_MAX_SESSION_IDS = 25
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
_FORBIDDEN_REPORT_FRAGMENTS = (
    "c:\\",
    "\\\\",
    "://",
    "file:",
    "token",
    "secret",
    "cookie",
    "auth",
    "profile",
    "transcript",
    "runtime.jsonl",
    "source",
    "event",
    "recording",
    "audio",
    "browser",
    "generated media",
    "traceback",
)


def write_stored_session_window_recovery_report_file(
    archive_root: str | Path,
    output_root: str | Path,
    session_ids: Sequence[str],
) -> dict[str, object]:
    try:
        safe_session_ids = _materialize_session_ids(session_ids)
        archive_root_path = _existing_directory(archive_root)
        output_root_path = _existing_directory(output_root)
        destination = _contained_destination(output_root_path, archive_root_path)
        if _is_relative_to(output_root_path, archive_root_path):
            _fail()

        report = build_stored_session_window_recovery_report(
            archive_root_path,
            safe_session_ids,
        )
        report = _validated_report(report, safe_session_ids)
        report_bytes = report.encode("utf-8")
        with destination.open("x", encoding="utf-8", newline="") as report_file:
            report_file.write(report)

        return {
            "write_kind": _WRITE_KIND,
            "session_count": len(safe_session_ids),
            "relative_path": _REPORT_FILENAME,
            "bytes_written": len(report_bytes),
        }
    except Exception:
        raise ValueError(STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_ERROR) from None


def _materialize_session_ids(session_ids: object) -> tuple[str, ...]:
    if isinstance(session_ids, (str, bytes, bytearray)) or not isinstance(
        session_ids, Sequence
    ):
        _fail()
    raw_session_ids: list[object] = []
    for session_id in session_ids:
        raw_session_ids.append(session_id)
        if len(raw_session_ids) > _MAX_SESSION_IDS:
            _fail()
    if not raw_session_ids:
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


def _contained_destination(output_root: Path, archive_root: Path) -> Path:
    raw_destination = output_root / _REPORT_FILENAME
    if raw_destination.exists() or raw_destination.is_symlink():
        _fail()
    destination = raw_destination.resolve(strict=False)
    if not _is_relative_to(destination, output_root) or _is_relative_to(
        destination,
        archive_root,
    ):
        _fail()
    return destination


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _validated_report(report: object, expected_session_ids: tuple[str, ...]) -> str:
    if (
        type(report) is not str
        or not report
        or not report.endswith("\n")
        or "\r" in report
        or _has_forbidden_report_control_character(report)
        or any(fragment in report.lower() for fragment in _FORBIDDEN_REPORT_FRAGMENTS)
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
    raise ValueError(STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_ERROR)
