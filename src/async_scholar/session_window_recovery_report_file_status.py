from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

from async_scholar.session_window_recovery_report_file_verification import (
    build_stored_session_window_recovery_report_file_verification,
)

STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_STATUS_ERROR = (
    "stored session window recovery report file status could not be built"
)

_REPORT_FILENAME = "stored-session-window-recovery-report.md"
_VERIFICATION_KIND = "stored_session_window_recovery_report_file_verification"
_STATUS_KIND = "stored_session_window_recovery_report_file_status"
_VERIFICATION_KEYS = (
    "verification_kind",
    "session_count",
    "relative_path",
    "exists",
    "matches_expected",
    "size_bytes",
    "expected_size_bytes",
)


def build_stored_session_window_recovery_report_file_status(
    session_ids: Sequence[str],
    archive_root: str | Path,
    output_root: str | Path,
) -> dict[str, object]:
    try:
        verification = _validated_verification(
            build_stored_session_window_recovery_report_file_verification(
                session_ids,
                archive_root,
                output_root,
            )
        )
        recommended_action, reason = _recommended_status(
            exists=verification["exists"],
            matches_expected=verification["matches_expected"],
        )
        return {
            "status_kind": _STATUS_KIND,
            "session_count": verification["session_count"],
            "relative_path": _REPORT_FILENAME,
            "exists": verification["exists"],
            "matches_expected": verification["matches_expected"],
            "size_bytes": verification["size_bytes"],
            "expected_size_bytes": verification["expected_size_bytes"],
            "recommended_action": recommended_action,
            "reason": reason,
        }
    except Exception:
        raise ValueError(
            STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_STATUS_ERROR
        ) from None


def _validated_verification(receipt: object) -> dict[str, object]:
    if type(receipt) is not dict or tuple(receipt) != _VERIFICATION_KEYS:
        _fail()

    verification_kind = receipt["verification_kind"]
    session_count = receipt["session_count"]
    relative_path = receipt["relative_path"]
    exists = receipt["exists"]
    matches_expected = receipt["matches_expected"]
    size_bytes = receipt["size_bytes"]
    expected_size_bytes = receipt["expected_size_bytes"]

    if type(verification_kind) is not str or verification_kind != _VERIFICATION_KIND:
        _fail()
    if type(relative_path) is not str or relative_path != _REPORT_FILENAME:
        _fail()
    if type(session_count) is not int or session_count < 1:
        _fail()
    if type(exists) is not bool or type(matches_expected) is not bool:
        _fail()
    if type(size_bytes) is not int or size_bytes < 0:
        _fail()
    if type(expected_size_bytes) is not int or expected_size_bytes < 1:
        _fail()
    _validate_state(
        exists=exists,
        matches_expected=matches_expected,
        size_bytes=size_bytes,
        expected_size_bytes=expected_size_bytes,
    )
    return {
        "session_count": session_count,
        "exists": exists,
        "matches_expected": matches_expected,
        "size_bytes": size_bytes,
        "expected_size_bytes": expected_size_bytes,
    }


def _validate_state(
    *,
    exists: bool,
    matches_expected: bool,
    size_bytes: int,
    expected_size_bytes: int,
) -> None:
    if not exists:
        if matches_expected or size_bytes != 0:
            _fail()
        return
    if matches_expected and (size_bytes < 1 or size_bytes != expected_size_bytes):
        _fail()


def _recommended_status(
    *,
    exists: bool,
    matches_expected: bool,
) -> tuple[str, str]:
    if exists and matches_expected:
        return ("none", "report_already_current")
    if not exists:
        return ("write_report", "report_missing")
    return ("manual_review", "report_content_mismatch")


def _fail() -> NoReturn:
    raise ValueError(STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_STATUS_ERROR)
