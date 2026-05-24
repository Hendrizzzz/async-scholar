"""Explicit local one-shot stored session-window execution runner."""

from __future__ import annotations

import re
from pathlib import Path
from typing import NoReturn

from async_scholar.schedule_store import list_course_schedule_session_window_inputs
from async_scholar.scheduled_start import ScheduledStartClock
from async_scholar.session_window_confirmation_preflight import (
    build_session_window_confirmation_preflight_summary,
)
from async_scholar.session_window_confirmation_response import (
    build_session_window_confirmation_response_summary,
)
from async_scholar.session_window_execution_preflight import (
    build_stored_session_window_execution_preflight_from_store,
)
from async_scholar.session_window_start_authorization import (
    build_session_window_start_authorization_summary,
    session_window_start_authorization_safe_summary,
)
from async_scholar.session_window_start_receipt import (
    write_stored_session_window_start_receipt,
)

STORED_SESSION_WINDOW_EXECUTION_ERROR = (
    "stored session window execution could not be built"
)

StoredSessionWindowExecution = dict[str, object]

_EXECUTION_KIND = "stored_session_window_execution"
_SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
_SOURCE_KINDS = frozenset(("file", "mic"))
_DAYS_OF_WEEK = frozenset(
    (
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    )
)
_LOCAL_TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")
_AUTHORIZATION_STATUSES = frozenset(
    ("authorized", "blocked", "not_required", "disabled")
)
_RUNTIME_STATES = frozenset(("not_started", "started", "stopped", "inconsistent"))
_RECOVERY_REVIEW_STATUSES = frozenset(("not_required", "required"))
_PREFLIGHT_DECISIONS = frozenset(("allow", "block"))
_EXECUTION_DECISIONS = frozenset(("executed", "blocked"))
_PREFLIGHT_REASONS = frozenset(
    (
        "ready_to_execute",
        "no_due_session",
        "confirmation_declined",
        "authorization_not_granted",
        "partial_runtime",
        "existing_conflicting_receipt",
        "recovery_review_required",
    )
)
_EXECUTION_REASONS = _PREFLIGHT_REASONS | frozenset(("start_receipt_written",))
_PREFLIGHT_KEYS = (
    "preflight_kind",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "due_count",
    "authorization_status",
    "authorized",
    "authorized_start_count",
    "runtime_state",
    "recovery_review_status",
    "ready_to_execute",
    "decision",
    "reason",
)
_AUTHORIZATION_KEYS = (
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "ready_to_start",
    "confirmation_required",
    "confirmation_status",
    "confirmation_response",
    "confirmation_verified",
    "authorized",
    "authorized_start_count",
    "blocked_start_count",
    "block_reason",
    "courses",
)
_RECEIPT_KEYS = (
    "receipt_kind",
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "ready_to_start",
    "confirmation_required",
    "confirmation_status",
    "confirmation_response",
    "confirmation_verified",
    "authorized",
    "authorized_start_count",
    "blocked_start_count",
    "block_reason",
    "runtime_record_written",
)
_EXECUTION_KEYS = (
    "execution_kind",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "due_count",
    "authorization_status",
    "authorized",
    "authorized_start_count",
    "runtime_state",
    "recovery_review_status",
    "preflight_decision",
    "preflight_reason",
    "runtime_record_written",
    "decision",
    "reason",
)


def build_stored_session_window_execution_from_store(
    db_path: str | Path,
    archive_root: str | Path,
    session_id: str,
    source_kind: str,
    clock: ScheduledStartClock,
    confirmation_response: str,
    *,
    enabled: bool = True,
) -> StoredSessionWindowExecution:
    """Run the explicit one-shot metadata receipt boundary for a stored session."""

    try:
        preflight = _preflight_safe_summary(
            build_stored_session_window_execution_preflight_from_store(
                db_path,
                archive_root,
                session_id,
                source_kind,
                clock,
                confirmation_response,
                enabled=enabled,
            )
        )
        if not _preflight_allows_execution(preflight):
            return _execution_safe_summary(_blocked_payload(preflight))

        authorization = _authorization_for_receipt(
            db_path,
            archive_root,
            session_id,
            source_kind,
            clock,
            confirmation_response,
            enabled=enabled,
        )
        _ensure_authorization_matches_preflight(authorization, preflight)
        receipt = _receipt_safe_summary(
            write_stored_session_window_start_receipt(
                authorization,
                Path(archive_root),
            )
        )
        _ensure_receipt_matches_preflight(receipt, preflight)
        return _execution_safe_summary(_executed_payload(preflight, receipt))
    except (KeyError, OSError, RuntimeError, TypeError, ValueError):
        raise ValueError(STORED_SESSION_WINDOW_EXECUTION_ERROR) from None


def _authorization_for_receipt(
    db_path: str | Path,
    archive_root: str | Path,
    session_id: str,
    source_kind: str,
    clock: ScheduledStartClock,
    confirmation_response: str,
    *,
    enabled: bool,
) -> dict[str, object]:
    preflight_payload = build_session_window_confirmation_preflight_summary(
        list_course_schedule_session_window_inputs(db_path),
        archive_root,
        session_id,
        source_kind,
        clock,
        enabled=enabled,
    )
    response_payload = build_session_window_confirmation_response_summary(
        preflight_payload,
        confirmation_response,
    )
    return _authorization_safe_summary(
        build_session_window_start_authorization_summary(response_payload)
    )


def _blocked_payload(preflight: dict[str, object]) -> dict[str, object]:
    return {
        "execution_kind": _EXECUTION_KIND,
        "session_id": preflight["session_id"],
        "source_kind": preflight["source_kind"],
        "clock_day_of_week": preflight["clock_day_of_week"],
        "clock_local_time": preflight["clock_local_time"],
        "due_count": preflight["due_count"],
        "authorization_status": preflight["authorization_status"],
        "authorized": preflight["authorized"],
        "authorized_start_count": preflight["authorized_start_count"],
        "runtime_state": preflight["runtime_state"],
        "recovery_review_status": preflight["recovery_review_status"],
        "preflight_decision": preflight["decision"],
        "preflight_reason": preflight["reason"],
        "runtime_record_written": False,
        "decision": "blocked",
        "reason": preflight["reason"],
    }


def _executed_payload(
    preflight: dict[str, object],
    receipt: dict[str, object],
) -> dict[str, object]:
    return {
        "execution_kind": _EXECUTION_KIND,
        "session_id": preflight["session_id"],
        "source_kind": preflight["source_kind"],
        "clock_day_of_week": preflight["clock_day_of_week"],
        "clock_local_time": preflight["clock_local_time"],
        "due_count": preflight["due_count"],
        "authorization_status": preflight["authorization_status"],
        "authorized": preflight["authorized"],
        "authorized_start_count": preflight["authorized_start_count"],
        "runtime_state": preflight["runtime_state"],
        "recovery_review_status": preflight["recovery_review_status"],
        "preflight_decision": preflight["decision"],
        "preflight_reason": preflight["reason"],
        "runtime_record_written": receipt["runtime_record_written"],
        "decision": "executed",
        "reason": "start_receipt_written",
    }


def _preflight_allows_execution(preflight: dict[str, object]) -> bool:
    return (
        preflight["ready_to_execute"] is True
        and preflight["decision"] == "allow"
        and preflight["reason"] == "ready_to_execute"
    )


def _ensure_authorization_matches_preflight(
    authorization: dict[str, object],
    preflight: dict[str, object],
) -> None:
    if (
        authorization["status"] != preflight["authorization_status"]
        or authorization["session_id"] != preflight["session_id"]
        or authorization["source_kind"] != preflight["source_kind"]
        or authorization["clock_day_of_week"] != preflight["clock_day_of_week"]
        or authorization["clock_local_time"] != preflight["clock_local_time"]
        or authorization["due_count"] != preflight["due_count"]
        or authorization["authorized"] != preflight["authorized"]
        or authorization["authorized_start_count"]
        != preflight["authorized_start_count"]
        or authorization["status"] != "authorized"
        or authorization["authorized"] is not True
        or authorization["confirmation_response"] != "confirmed"
        or authorization["confirmation_verified"] is not True
        or authorization["block_reason"] != "none"
    ):
        _fail()


def _ensure_receipt_matches_preflight(
    receipt: dict[str, object],
    preflight: dict[str, object],
) -> None:
    if (
        receipt["status"] != "authorized"
        or receipt["session_id"] != preflight["session_id"]
        or receipt["source_kind"] != preflight["source_kind"]
        or receipt["clock_day_of_week"] != preflight["clock_day_of_week"]
        or receipt["clock_local_time"] != preflight["clock_local_time"]
        or receipt["due_count"] != preflight["due_count"]
        or receipt["authorized"] is not True
        or receipt["authorized_start_count"] != preflight["authorized_start_count"]
        or receipt["block_reason"] != "none"
        or receipt["runtime_record_written"] is not True
    ):
        _fail()


def _preflight_safe_summary(payload: dict[str, object]) -> dict[str, object]:
    if type(payload) is not dict or tuple(payload) != _PREFLIGHT_KEYS:
        _fail()
    safe_payload = {key: payload[key] for key in _PREFLIGHT_KEYS}
    if _exact_text(safe_payload["preflight_kind"]) != (
        "stored_session_window_execution_preflight"
    ):
        _fail()
    safe_payload["session_id"] = _safe_session_id(safe_payload["session_id"])
    safe_payload["source_kind"] = _source_kind(safe_payload["source_kind"])
    safe_payload["clock_day_of_week"] = _day_of_week(safe_payload["clock_day_of_week"])
    safe_payload["clock_local_time"] = _local_time(safe_payload["clock_local_time"])
    safe_payload["due_count"] = _non_negative_int(safe_payload["due_count"])
    safe_payload["authorization_status"] = _authorization_status(
        safe_payload["authorization_status"]
    )
    safe_payload["authorized"] = _bool_value(safe_payload["authorized"])
    safe_payload["authorized_start_count"] = _non_negative_int(
        safe_payload["authorized_start_count"]
    )
    safe_payload["runtime_state"] = _runtime_state(safe_payload["runtime_state"])
    safe_payload["recovery_review_status"] = _recovery_review_status(
        safe_payload["recovery_review_status"]
    )
    safe_payload["ready_to_execute"] = _bool_value(safe_payload["ready_to_execute"])
    safe_payload["decision"] = _preflight_decision(safe_payload["decision"])
    safe_payload["reason"] = _execution_reason(safe_payload["reason"])
    _validate_preflight_policy(safe_payload)
    return safe_payload


def _authorization_safe_summary(payload: dict[str, object]) -> dict[str, object]:
    if type(payload) is not dict or tuple(payload) != _AUTHORIZATION_KEYS:
        _fail()
    try:
        safe_payload = session_window_start_authorization_safe_summary(payload)
    except (KeyError, TypeError, ValueError):
        _fail()
    if type(safe_payload) is not dict or tuple(safe_payload) != _AUTHORIZATION_KEYS:
        _fail()
    return safe_payload


def _receipt_safe_summary(payload: dict[str, object]) -> dict[str, object]:
    if type(payload) is not dict or tuple(payload) != _RECEIPT_KEYS:
        _fail()
    safe_payload = {key: payload[key] for key in _RECEIPT_KEYS}
    if _exact_text(safe_payload["receipt_kind"]) != (
        "stored_session_window_start_receipt"
    ):
        _fail()
    safe_payload["status"] = _authorization_status(safe_payload["status"])
    safe_payload["session_id"] = _safe_session_id(safe_payload["session_id"])
    safe_payload["source_kind"] = _source_kind(safe_payload["source_kind"])
    safe_payload["clock_day_of_week"] = _day_of_week(safe_payload["clock_day_of_week"])
    safe_payload["clock_local_time"] = _local_time(safe_payload["clock_local_time"])
    safe_payload["course_count"] = _non_negative_int(safe_payload["course_count"])
    safe_payload["due_count"] = _non_negative_int(safe_payload["due_count"])
    safe_payload["ready_to_start"] = _bool_value(safe_payload["ready_to_start"])
    safe_payload["confirmation_required"] = _bool_value(
        safe_payload["confirmation_required"]
    )
    _exact_text(safe_payload["confirmation_status"])
    _exact_text(safe_payload["confirmation_response"])
    safe_payload["confirmation_verified"] = _bool_value(
        safe_payload["confirmation_verified"]
    )
    safe_payload["authorized"] = _bool_value(safe_payload["authorized"])
    safe_payload["authorized_start_count"] = _non_negative_int(
        safe_payload["authorized_start_count"]
    )
    safe_payload["blocked_start_count"] = _non_negative_int(
        safe_payload["blocked_start_count"]
    )
    _exact_text(safe_payload["block_reason"])
    safe_payload["runtime_record_written"] = _bool_value(
        safe_payload["runtime_record_written"]
    )
    return safe_payload


def _execution_safe_summary(
    payload: dict[str, object],
) -> StoredSessionWindowExecution:
    if type(payload) is not dict or tuple(payload) != _EXECUTION_KEYS:
        _fail()
    safe_payload = {key: payload[key] for key in _EXECUTION_KEYS}
    if _exact_text(safe_payload["execution_kind"]) != _EXECUTION_KIND:
        _fail()
    safe_payload["session_id"] = _safe_session_id(safe_payload["session_id"])
    safe_payload["source_kind"] = _source_kind(safe_payload["source_kind"])
    safe_payload["clock_day_of_week"] = _day_of_week(safe_payload["clock_day_of_week"])
    safe_payload["clock_local_time"] = _local_time(safe_payload["clock_local_time"])
    safe_payload["due_count"] = _non_negative_int(safe_payload["due_count"])
    safe_payload["authorization_status"] = _authorization_status(
        safe_payload["authorization_status"]
    )
    safe_payload["authorized"] = _bool_value(safe_payload["authorized"])
    safe_payload["authorized_start_count"] = _non_negative_int(
        safe_payload["authorized_start_count"]
    )
    safe_payload["runtime_state"] = _runtime_state(safe_payload["runtime_state"])
    safe_payload["recovery_review_status"] = _recovery_review_status(
        safe_payload["recovery_review_status"]
    )
    safe_payload["preflight_decision"] = _preflight_decision(
        safe_payload["preflight_decision"]
    )
    safe_payload["preflight_reason"] = _execution_reason(
        safe_payload["preflight_reason"]
    )
    safe_payload["runtime_record_written"] = _bool_value(
        safe_payload["runtime_record_written"]
    )
    safe_payload["decision"] = _execution_decision(safe_payload["decision"])
    safe_payload["reason"] = _execution_reason(safe_payload["reason"])
    _validate_execution_policy(safe_payload)
    return safe_payload


def _validate_preflight_policy(preflight: dict[str, object]) -> None:
    if preflight["decision"] == "allow":
        if not _preflight_allows_execution(preflight):
            _fail()
        if (
            preflight["due_count"] <= 0
            or preflight["authorization_status"] != "authorized"
            or preflight["authorized"] is not True
            or preflight["authorized_start_count"] != preflight["due_count"]
            or preflight["runtime_state"] != "not_started"
            or preflight["recovery_review_status"] != "not_required"
        ):
            _fail()
    elif preflight["ready_to_execute"] is True:
        _fail()


def _validate_execution_policy(payload: dict[str, object]) -> None:
    if payload["decision"] == "executed":
        if (
            payload["preflight_decision"] != "allow"
            or payload["preflight_reason"] != "ready_to_execute"
            or payload["reason"] != "start_receipt_written"
            or payload["runtime_record_written"] is not True
            or payload["due_count"] <= 0
            or payload["authorization_status"] != "authorized"
            or payload["authorized"] is not True
            or payload["authorized_start_count"] != payload["due_count"]
            or payload["runtime_state"] != "not_started"
            or payload["recovery_review_status"] != "not_required"
        ):
            _fail()
    elif (
        payload["preflight_decision"] != "block"
        or payload["runtime_record_written"] is not False
        or payload["reason"] != payload["preflight_reason"]
    ):
        _fail()


def _safe_session_id(value: object) -> str:
    if not isinstance(value, str) or not _SESSION_ID_PATTERN.fullmatch(value):
        _fail()
    return value


def _source_kind(value: object) -> str:
    if not isinstance(value, str) or value not in _SOURCE_KINDS:
        _fail()
    return value


def _day_of_week(value: object) -> str:
    if not isinstance(value, str) or value not in _DAYS_OF_WEEK:
        _fail()
    return value


def _local_time(value: object) -> str:
    if not isinstance(value, str) or not _LOCAL_TIME_PATTERN.fullmatch(value):
        _fail()
    return value


def _authorization_status(value: object) -> str:
    if not isinstance(value, str) or value not in _AUTHORIZATION_STATUSES:
        _fail()
    return value


def _runtime_state(value: object) -> str:
    if not isinstance(value, str) or value not in _RUNTIME_STATES:
        _fail()
    return value


def _recovery_review_status(value: object) -> str:
    if not isinstance(value, str) or value not in _RECOVERY_REVIEW_STATUSES:
        _fail()
    return value


def _preflight_decision(value: object) -> str:
    if not isinstance(value, str) or value not in _PREFLIGHT_DECISIONS:
        _fail()
    return value


def _execution_decision(value: object) -> str:
    if not isinstance(value, str) or value not in _EXECUTION_DECISIONS:
        _fail()
    return value


def _execution_reason(value: object) -> str:
    if not isinstance(value, str) or value not in _EXECUTION_REASONS:
        _fail()
    return value


def _non_negative_int(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        _fail()
    return value


def _bool_value(value: object) -> bool:
    if not isinstance(value, bool):
        _fail()
    return value


def _exact_text(value: object) -> str:
    if not isinstance(value, str):
        _fail()
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        _fail()
    return value


def _fail() -> NoReturn:
    raise ValueError(STORED_SESSION_WINDOW_EXECUTION_ERROR)
