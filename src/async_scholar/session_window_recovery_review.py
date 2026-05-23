from __future__ import annotations

import re
from pathlib import Path
from typing import NoReturn

from async_scholar.session_window_recovery_decision import (
    build_stored_session_window_recovery_decision,
)

STORED_SESSION_WINDOW_RECOVERY_REVIEW_ERROR = (
    "stored session window recovery review could not be built"
)

_REVIEW_KIND = "stored_session_window_recovery_review"
_DECISION_KEYS = (
    "decision_kind",
    "session_id",
    "runtime_lifecycle_status",
    "runtime_record_count",
    "start_receipt_count",
    "stop_receipt_count",
    "session_active",
    "session_stopped",
    "archive_recovery_status",
    "archive_existing_count",
    "archive_missing_count",
    "recovery_decision",
    "manual_review_required",
)
_DECISION_KIND = "stored_session_window_recovery_decision"
_SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
_LIFECYCLE_VALUES = frozenset(("not_started", "started", "stopped", "inconsistent"))
_ARCHIVE_STATUS_VALUES = frozenset(("empty", "partial", "complete"))
_REVIEW_MAPPING = {
    "no_action": (False, "not_required", "none", "leave_archive_unchanged"),
    "inspect_active_session": (
        True,
        "required",
        "active_session_runtime",
        "inspect_runtime_metadata",
    ),
    "inspect_partial_archive": (
        True,
        "required",
        "partial_archive_metadata",
        "inspect_archive_metadata",
    ),
    "manual_review": (
        True,
        "required",
        "inconsistent_runtime",
        "escalate_manual_review",
    ),
}


def build_stored_session_window_recovery_review(
    archive_root: str | Path,
    session_id: str,
) -> dict[str, object]:
    try:
        safe_session_id = _clean_session_id(session_id)
        decision = build_stored_session_window_recovery_decision(
            archive_root,
            safe_session_id,
        )
        recovery_decision = _recovery_decision(decision)
        (
            manual_review_required,
            review_status,
            review_reason,
            safe_next_review_action,
        ) = _REVIEW_MAPPING[recovery_decision]
        if (
            _bool_value(decision.get("manual_review_required"))
            != manual_review_required
            or _session_id(decision) != safe_session_id
        ):
            _fail()

        return {
            "review_kind": _REVIEW_KIND,
            "session_id": safe_session_id,
            "runtime_lifecycle_status": _runtime_lifecycle_status(decision),
            "archive_recovery_status": _archive_recovery_status(decision),
            "archive_existing_count": _non_negative_int(
                decision.get("archive_existing_count")
            ),
            "archive_missing_count": _non_negative_int(
                decision.get("archive_missing_count")
            ),
            "recovery_decision": recovery_decision,
            "manual_review_required": manual_review_required,
            "review_status": review_status,
            "review_reason": review_reason,
            "safe_next_review_action": safe_next_review_action,
        }
    except Exception:
        raise ValueError(STORED_SESSION_WINDOW_RECOVERY_REVIEW_ERROR) from None


def _recovery_decision(decision: dict[str, object]) -> str:
    _validate_decision_shape(decision)
    recovery_decision = decision.get("recovery_decision")
    if (
        not isinstance(recovery_decision, str)
        or recovery_decision not in _REVIEW_MAPPING
    ):
        _fail()
    return recovery_decision


def _validate_decision_shape(decision: dict[str, object]) -> None:
    if tuple(decision) != _DECISION_KEYS:
        _fail()
    if decision.get("decision_kind") != _DECISION_KIND:
        _fail()
    _session_id(decision)
    _runtime_lifecycle_status(decision)
    _non_negative_int(decision.get("runtime_record_count"))
    _non_negative_int(decision.get("start_receipt_count"))
    _non_negative_int(decision.get("stop_receipt_count"))
    _bool_value(decision.get("session_active"))
    _bool_value(decision.get("session_stopped"))
    _archive_recovery_status(decision)
    _non_negative_int(decision.get("archive_existing_count"))
    _non_negative_int(decision.get("archive_missing_count"))
    _bool_value(decision.get("manual_review_required"))


def _session_id(decision: dict[str, object]) -> str:
    return _clean_session_id(decision.get("session_id"))


def _clean_session_id(value: object) -> str:
    if not isinstance(value, str):
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


def _runtime_lifecycle_status(decision: dict[str, object]) -> str:
    value = decision.get("runtime_lifecycle_status")
    if not isinstance(value, str) or value not in _LIFECYCLE_VALUES:
        _fail()
    return value


def _archive_recovery_status(decision: dict[str, object]) -> str:
    value = decision.get("archive_recovery_status")
    if not isinstance(value, str) or value not in _ARCHIVE_STATUS_VALUES:
        _fail()
    return value


def _non_negative_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        _fail()
    return value


def _bool_value(value: object) -> bool:
    if not isinstance(value, bool):
        _fail()
    return value


def _fail() -> NoReturn:
    raise ValueError(STORED_SESSION_WINDOW_RECOVERY_REVIEW_ERROR)
