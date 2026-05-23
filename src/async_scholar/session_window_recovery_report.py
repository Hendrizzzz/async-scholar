from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

from async_scholar.session_window_recovery_batch_review import (
    build_stored_session_window_recovery_review_batch,
)

STORED_SESSION_WINDOW_RECOVERY_REPORT_ERROR = (
    "stored session window recovery report could not be built"
)

_BATCH_KIND = "stored_session_window_recovery_review_batch"
_REVIEW_KIND = "stored_session_window_recovery_review"
_MAX_SESSION_IDS = 25
_BATCH_KEYS = (
    "batch_kind",
    "review_count",
    "manual_review_required_count",
    "not_required_count",
    "required_count",
    "reviews",
)
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


def build_stored_session_window_recovery_report(
    archive_root: str | Path,
    session_ids: Sequence[str],
) -> str:
    try:
        safe_session_ids = _clean_session_ids(session_ids)
        batch = _validated_batch(
            build_stored_session_window_recovery_review_batch(
                archive_root,
                safe_session_ids,
            ),
            safe_session_ids,
        )
        return _render_report(batch)
    except Exception:
        raise ValueError(STORED_SESSION_WINDOW_RECOVERY_REPORT_ERROR) from None


def _validated_batch(
    batch: dict[str, object],
    expected_session_ids: tuple[str, ...],
) -> dict[str, object]:
    if type(batch) is not dict or tuple(batch) != _BATCH_KEYS:
        _fail()
    if _string_value(batch.get("batch_kind")) != _BATCH_KIND:
        _fail()

    reviews = batch.get("reviews")
    if type(reviews) is not list:
        _fail()
    validated_reviews = [
        _validated_review(review, expected_session_id)
        for review, expected_session_id in zip(
            reviews,
            expected_session_ids,
            strict=True,
        )
    ]

    review_count = _non_negative_int(batch.get("review_count"))
    manual_review_required_count = _non_negative_int(
        batch.get("manual_review_required_count")
    )
    not_required_count = _non_negative_int(batch.get("not_required_count"))
    required_count = _non_negative_int(batch.get("required_count"))
    if review_count != len(validated_reviews):
        _fail()
    if required_count != sum(
        1 for review in validated_reviews if review["review_status"] == "required"
    ):
        _fail()
    if not_required_count != review_count - required_count:
        _fail()
    if manual_review_required_count != sum(
        1 for review in validated_reviews if review["manual_review_required"] is True
    ):
        _fail()

    return {
        "batch_kind": _BATCH_KIND,
        "review_count": review_count,
        "manual_review_required_count": manual_review_required_count,
        "not_required_count": not_required_count,
        "required_count": required_count,
        "reviews": validated_reviews,
    }


def _validated_review(
    review: object,
    expected_session_id: str,
) -> dict[str, object]:
    if type(review) is not dict or tuple(review) != _REVIEW_KEYS:
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
    _validate_archive_counts(
        archive_recovery_status,
        archive_existing_count,
        archive_missing_count,
    )
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


def _render_report(batch: dict[str, object]) -> str:
    lines = [
        "# Stored Session Window Recovery Report",
        "",
        f"Review count: {batch['review_count']}",
        f"Manual review required: {batch['manual_review_required_count']}",
        f"Required: {batch['required_count']}",
        f"Not required: {batch['not_required_count']}",
    ]
    reviews = batch["reviews"]
    if type(reviews) is not list:
        _fail()
    for review in reviews:
        if type(review) is not dict:
            _fail()
        lines.extend(
            (
                "",
                f"## {review['session_id']}",
                f"- Session ID: {review['session_id']}",
                f"- Lifecycle status: {review['runtime_lifecycle_status']}",
                f"- Archive status: {review['archive_recovery_status']}",
                f"- Recovery decision: {review['recovery_decision']}",
                f"- Review status: {review['review_status']}",
                f"- Review reason: {review['review_reason']}",
                f"- Safe next review action: {review['safe_next_review_action']}",
            )
        )
    return "\n".join(lines) + "\n"


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


def _validate_archive_counts(
    archive_recovery_status: str,
    archive_existing_count: int,
    archive_missing_count: int,
) -> None:
    if archive_recovery_status == "empty" and archive_existing_count != 0:
        _fail()
    if archive_recovery_status == "partial" and (
        archive_existing_count == 0 or archive_missing_count == 0
    ):
        _fail()
    if archive_recovery_status == "complete" and archive_missing_count != 0:
        _fail()


def _recovery_decision(review: dict[str, object]) -> str:
    value = _string_value(review.get("recovery_decision"))
    if value not in _REVIEW_MAPPING:
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
    raise ValueError(STORED_SESSION_WINDOW_RECOVERY_REPORT_ERROR)
