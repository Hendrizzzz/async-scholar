from __future__ import annotations

from collections.abc import Sequence
from typing import NoReturn

from async_scholar.session_window_recovery_report_file_action_preview import (
    build_stored_session_window_recovery_report_file_action_preview,
)

STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_ACTION_ERROR = (
    "stored session window recovery report file action could not be applied"
)

_REPORT_FILENAME = "stored-session-window-recovery-report.md"
_PREVIEW_KIND = "stored_session_window_recovery_report_file_action_preview"
_WRITE_KIND = "stored_session_window_recovery_report_file"
_ACTION_KIND = "stored_session_window_recovery_report_file_action"
_PREVIEW_KEYS = (
    "preview_kind",
    "session_count",
    "relative_path",
    "exists",
    "matches_expected",
    "recommended_action",
    "reason",
)
_WRITE_KEYS = (
    "write_kind",
    "session_count",
    "relative_path",
    "bytes_written",
)


def build_stored_session_window_recovery_report_file_action(
    session_ids: Sequence[str],
    archive_root: object,
    output_root: object,
) -> dict[str, object]:
    try:
        preview = _validated_preview_receipt(
            build_stored_session_window_recovery_report_file_action_preview(
                session_ids,
                archive_root,
                output_root,
            )
        )
        preview_action = preview["recommended_action"]
        preview_reason = preview["reason"]
        if preview_action == "write_report" and preview_reason == "report_missing":
            from async_scholar.session_window_recovery_report_file import (
                write_stored_session_window_recovery_report_file,
            )

            writer = _validated_writer_receipt(
                write_stored_session_window_recovery_report_file(
                    archive_root,
                    output_root,
                    session_ids,
                ),
                preview["session_count"],
            )
            return _action_receipt(
                preview,
                "written",
                writer["bytes_written"],
            )
        if preview_action == "none" and preview_reason == "report_already_current":
            return _action_receipt(preview, "no_action", 0)
        if (
            preview_action == "manual_review"
            and preview_reason == "report_content_mismatch"
        ):
            return _action_receipt(preview, "manual_review_required", 0)
        _fail()
    except Exception:
        raise ValueError(
            STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_ACTION_ERROR
        ) from None


def _validated_preview_receipt(preview: object) -> dict[str, object]:
    if type(preview) is not dict or tuple(preview) != _PREVIEW_KEYS:
        _fail()
    for key in ("preview_kind", "relative_path", "recommended_action", "reason"):
        if type(preview[key]) is not str:
            _fail()
    if preview["preview_kind"] != _PREVIEW_KIND:
        _fail()
    if preview["relative_path"] != _REPORT_FILENAME:
        _fail()
    if type(preview["session_count"]) is not int or preview["session_count"] <= 0:
        _fail()
    if type(preview["exists"]) is not bool:
        _fail()
    if type(preview["matches_expected"]) is not bool:
        _fail()

    if (
        preview["exists"] is True
        and preview["matches_expected"] is True
        and preview["recommended_action"] == "none"
        and preview["reason"] == "report_already_current"
    ):
        return preview
    if (
        preview["exists"] is False
        and preview["matches_expected"] is False
        and preview["recommended_action"] == "write_report"
        and preview["reason"] == "report_missing"
    ):
        return preview
    if (
        preview["exists"] is True
        and preview["matches_expected"] is False
        and preview["recommended_action"] == "manual_review"
        and preview["reason"] == "report_content_mismatch"
    ):
        return preview
    _fail()


def _validated_writer_receipt(
    writer: object,
    expected_session_count: object,
) -> dict[str, object]:
    if type(writer) is not dict or tuple(writer) != _WRITE_KEYS:
        _fail()
    for key in ("write_kind", "relative_path"):
        if type(writer[key]) is not str:
            _fail()
    if writer["write_kind"] != _WRITE_KIND:
        _fail()
    if writer["relative_path"] != _REPORT_FILENAME:
        _fail()
    if (
        type(writer["session_count"]) is not int
        or writer["session_count"] <= 0
        or writer["session_count"] != expected_session_count
    ):
        _fail()
    if type(writer["bytes_written"]) is not int or writer["bytes_written"] <= 0:
        _fail()
    return writer


def _action_receipt(
    preview: dict[str, object],
    outcome: str,
    bytes_written: object,
) -> dict[str, object]:
    return {
        "action_kind": _ACTION_KIND,
        "session_count": preview["session_count"],
        "relative_path": _REPORT_FILENAME,
        "preview_action": preview["recommended_action"],
        "preview_reason": preview["reason"],
        "outcome": outcome,
        "bytes_written": bytes_written,
    }


def _fail() -> NoReturn:
    raise ValueError(STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_ACTION_ERROR)
