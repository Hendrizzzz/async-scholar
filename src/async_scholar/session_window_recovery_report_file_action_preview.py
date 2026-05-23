from __future__ import annotations

from collections.abc import Sequence
from typing import NoReturn

from async_scholar.session_window_recovery_report_file_verification import (
    build_stored_session_window_recovery_report_file_verification,
)

STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_ACTION_PREVIEW_ERROR = (
    "stored session window recovery report file action preview could not be built"
)

_REPORT_FILENAME = "stored-session-window-recovery-report.md"
_VERIFICATION_KIND = "stored_session_window_recovery_report_file_verification"
_PREVIEW_KIND = "stored_session_window_recovery_report_file_action_preview"
_VERIFICATION_KEYS = (
    "verification_kind",
    "session_count",
    "relative_path",
    "exists",
    "matches_expected",
    "size_bytes",
    "expected_size_bytes",
)


def build_stored_session_window_recovery_report_file_action_preview(
    session_ids: Sequence[str],
    archive_root: object,
    output_root: object,
) -> dict[str, object]:
    try:
        verification = _validated_verification_receipt(
            build_stored_session_window_recovery_report_file_verification(
                session_ids,
                archive_root,
                output_root,
            )
        )
        recommended_action, reason = _recommended_action_and_reason(verification)
        return {
            "preview_kind": _PREVIEW_KIND,
            "session_count": verification["session_count"],
            "relative_path": _REPORT_FILENAME,
            "exists": verification["exists"],
            "matches_expected": verification["matches_expected"],
            "recommended_action": recommended_action,
            "reason": reason,
        }
    except Exception:
        raise ValueError(
            STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_ACTION_PREVIEW_ERROR
        ) from None


def _validated_verification_receipt(
    verification: object,
) -> dict[str, object]:
    if type(verification) is not dict or tuple(verification) != _VERIFICATION_KEYS:
        _fail()

    if verification["verification_kind"] != _VERIFICATION_KIND:
        _fail()
    if verification["relative_path"] != _REPORT_FILENAME:
        _fail()

    if type(verification["exists"]) is not bool:
        _fail()
    if type(verification["matches_expected"]) is not bool:
        _fail()

    for key in ("session_count", "size_bytes", "expected_size_bytes"):
        value = verification[key]
        if type(value) is not int or value < 0:
            _fail()

    exists = verification["exists"]
    matches_expected = verification["matches_expected"]
    size_bytes = verification["size_bytes"]
    expected_size_bytes = verification["expected_size_bytes"]
    if exists is False:
        if matches_expected is not False or size_bytes != 0:
            _fail()
    elif matches_expected is True and size_bytes != expected_size_bytes:
        _fail()

    return verification


def _recommended_action_and_reason(
    verification: dict[str, object],
) -> tuple[str, str]:
    exists = verification["exists"]
    matches_expected = verification["matches_expected"]
    if exists is False and matches_expected is False:
        return "write_report", "report_missing"
    if exists is True and matches_expected is True:
        return "none", "report_already_current"
    if exists is True and matches_expected is False:
        return "manual_review", "report_content_mismatch"
    _fail()


def _fail() -> NoReturn:
    raise ValueError(STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_ACTION_PREVIEW_ERROR)
