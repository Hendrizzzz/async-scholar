from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

from async_scholar.session_window_recovery_review import (
    build_stored_session_window_recovery_review,
)

STORED_SESSION_WINDOW_RECOVERY_REVIEW_BATCH_ERROR = (
    "stored session window recovery review batch could not be built"
)

_BATCH_KIND = "stored_session_window_recovery_review_batch"
_REVIEW_KIND = "stored_session_window_recovery_review"
_MAX_SESSION_IDS = 25
_REVIEW_KEYS = (
    "review_kind",
    "session_id",
    "runtime_lifecycle_status",
    "archive_recovery_status",
    "archive_existing_count",
    "archive_missing_count",
    "recovery_decision",
    "manual_review_required",
    "review_status",
    "review_reason",
    "safe_next_review_action",
)
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


def build_stored_session_window_recovery_review_batch(
    archive_root: str | Path,
    session_ids: Sequence[str],
) -> dict[str, object]:
    try:
        safe_session_ids = _clean_session_ids(session_ids)
        reviews = [
            _validated_review(
                build_stored_session_window_recovery_review(
                    archive_root,
                    safe_session_id,
                ),
                safe_session_id,
            )
            for safe_session_id in safe_session_ids
        ]
        required_count = sum(
            1 for review in reviews if review["review_status"] == "required"
        )
        not_required_count = len(reviews) - required_count

        return {
            "batch_kind": _BATCH_KIND,
            "review_count": len(reviews),
            "manual_review_required_count": sum(
                1 for review in reviews if review["manual_review_required"] is True
            ),
            "not_required_count": not_required_count,
            "required_count": required_count,
            "reviews": reviews,
        }
    except Exception:
        raise ValueError(STORED_SESSION_WINDOW_RECOVERY_REVIEW_BATCH_ERROR) from None


def _clean_session_ids(session_ids: object) -> tuple[str, ...]:
    if isinstance(session_ids, (str, bytes, bytearray)):
        _fail()
    if not isinstance(session_ids, Sequence):
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


def _validated_review(
    review: dict[str, object],
    expected_session_id: str,
) -> dict[str, object]:
    if tuple(review) != _REVIEW_KEYS:
        _fail()
    if _string_value(review.get("review_kind")) != _REVIEW_KIND:
        _fail()

    session_id = _clean_session_id(review.get("session_id"))
    if session_id != expected_session_id:
        _fail()

    runtime_lifecycle_status = _runtime_lifecycle_status(review)
    archive_recovery_status = _archive_recovery_status(review)
    archive_existing_count = _non_negative_int(review.get("archive_existing_count"))
    archive_missing_count = _non_negative_int(review.get("archive_missing_count"))
    recovery_decision = _recovery_decision(review)
    manual_review_required = _bool_value(review.get("manual_review_required"))
    review_status = _string_value(review.get("review_status"))
    review_reason = _string_value(review.get("review_reason"))
    safe_next_review_action = _string_value(review.get("safe_next_review_action"))
    if (
        manual_review_required,
        review_status,
        review_reason,
        safe_next_review_action,
    ) != _REVIEW_MAPPING[recovery_decision]:
        _fail()

    return {
        "review_kind": _REVIEW_KIND,
        "session_id": session_id,
        "runtime_lifecycle_status": runtime_lifecycle_status,
        "archive_recovery_status": archive_recovery_status,
        "archive_existing_count": archive_existing_count,
        "archive_missing_count": archive_missing_count,
        "recovery_decision": recovery_decision,
        "manual_review_required": manual_review_required,
        "review_status": review_status,
        "review_reason": review_reason,
        "safe_next_review_action": safe_next_review_action,
    }


def _recovery_decision(review: dict[str, object]) -> str:
    value = _string_value(review.get("recovery_decision"))
    if value not in _REVIEW_MAPPING:
        _fail()
    return value


def _clean_session_id(value: object) -> str:
    value = _string_value(value)
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


def _runtime_lifecycle_status(review: dict[str, object]) -> str:
    value = _string_value(review.get("runtime_lifecycle_status"))
    if value not in _LIFECYCLE_VALUES:
        _fail()
    return value


def _archive_recovery_status(review: dict[str, object]) -> str:
    value = _string_value(review.get("archive_recovery_status"))
    if value not in _ARCHIVE_STATUS_VALUES:
        _fail()
    return value


def _non_negative_int(value: object) -> int:
    if type(value) is not int or value < 0:
        _fail()
    return value


def _bool_value(value: object) -> bool:
    if type(value) is not bool:
        _fail()
    return value


def _string_value(value: object) -> str:
    if type(value) is not str:
        _fail()
    return value


def _fail() -> NoReturn:
    raise ValueError(STORED_SESSION_WINDOW_RECOVERY_REVIEW_BATCH_ERROR)
