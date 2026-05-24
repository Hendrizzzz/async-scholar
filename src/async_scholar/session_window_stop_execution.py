from __future__ import annotations

import re
from pathlib import Path
from typing import NoReturn

from async_scholar.session_window_stop_execution_preflight import (
    build_stored_session_window_stop_execution_preflight_from_store,
)
from async_scholar.session_window_stop_receipt import (
    write_stored_session_window_stop_receipt,
)

STORED_SESSION_WINDOW_STOP_EXECUTION_ERROR = (
    "stored session window stop execution could not be built"
)

StoredSessionWindowStopExecution = dict[str, object]

_EXECUTION_KIND = "stored_session_window_stop_execution"
_PREFLIGHT_KIND = "stored_session_window_stop_execution_preflight"
_RECEIPT_KIND = "stored_session_window_stop_receipt"
_SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
_COURSE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_LOCAL_TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")
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
_RUNTIME_STATES = frozenset(
    ("missing", "not_started", "started", "stopped", "inconsistent")
)
_PREFLIGHT_DECISIONS = frozenset(("allow", "block"))
_CONFIRMATION_RESPONSES = frozenset(("confirmed", "declined"))
_EXECUTION_DECISIONS = frozenset(("executed", "blocked"))
_PREFLIGHT_REASONS = frozenset(
    (
        "ready_to_stop",
        "disabled_stop_preview",
        "missing_runtime",
        "not_started_runtime",
        "already_stopped_runtime",
        "inconsistent_runtime",
        "source_mismatch",
    )
)
_EXECUTION_REASONS = _PREFLIGHT_REASONS | frozenset(
    ("confirmation_declined", "stop_receipt_written")
)
_STOP_AFTER_MINUTES_MAX = 24 * 60
_TEXT_MAX_LENGTH = 128
_PREFLIGHT_KEYS = (
    "preflight_kind",
    "session_id",
    "course_id",
    "source_kind",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "stop_after_minutes",
    "runtime_state",
    "start_receipt_count",
    "stop_receipt_count",
    "ready_to_stop",
    "decision",
    "reason",
)
_STOP_PREVIEW_KEYS = (
    "status",
    "course_id",
    "source_kind",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "stop_after_minutes",
    "enabled",
)
_RECEIPT_KEYS = (
    "receipt_kind",
    "status",
    "session_id",
    "course_id",
    "source_kind",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "stop_after_minutes",
    "enabled",
    "runtime_record_written",
)
_EXECUTION_KEYS = (
    "execution_kind",
    "session_id",
    "course_id",
    "source_kind",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "stop_after_minutes",
    "runtime_state",
    "start_receipt_count",
    "stop_receipt_count",
    "ready_to_stop",
    "confirmation_response",
    "preflight_decision",
    "preflight_reason",
    "runtime_record_written",
    "decision",
    "reason",
)


def build_stored_session_window_stop_execution_from_store(
    db_path: str | Path,
    archive_root: str | Path,
    session_id: str,
    course_id: str,
    class_time_index: int,
    source_kind: str,
    confirmation_response: str,
    *,
    enabled: bool = True,
) -> StoredSessionWindowStopExecution:
    try:
        response = _confirmation_response(confirmation_response)
        safe_enabled = _bool_value(enabled)
        preflight = _preflight_safe_summary(
            build_stored_session_window_stop_execution_preflight_from_store(
                db_path,
                archive_root,
                session_id,
                course_id,
                class_time_index,
                source_kind,
                enabled=safe_enabled,
            ),
            expected_session_id=session_id,
            expected_course_id=course_id,
            expected_class_time_index=class_time_index,
            expected_source_kind=source_kind,
        )
        if not _preflight_allows_stop(preflight) or response == "declined":
            return _execution_safe_summary(_blocked_payload(preflight, response))

        receipt = _receipt_safe_summary(
            write_stored_session_window_stop_receipt(
                _stop_preview_from_preflight(preflight),
                Path(archive_root),
                preflight["session_id"],
            )
        )
        _ensure_receipt_matches_preflight(receipt, preflight)
        return _execution_safe_summary(_executed_payload(preflight, response, receipt))
    except (KeyError, OSError, RuntimeError, TypeError, ValueError):
        raise ValueError(STORED_SESSION_WINDOW_STOP_EXECUTION_ERROR) from None


def _blocked_payload(
    preflight: dict[str, object],
    confirmation_response: str,
) -> dict[str, object]:
    reason = preflight["reason"]
    if confirmation_response == "declined" and _preflight_allows_stop(preflight):
        reason = "confirmation_declined"
    return {
        "execution_kind": _EXECUTION_KIND,
        "session_id": preflight["session_id"],
        "course_id": preflight["course_id"],
        "source_kind": preflight["source_kind"],
        "selected_class_time_index": preflight["selected_class_time_index"],
        "scheduled_day_of_week": preflight["scheduled_day_of_week"],
        "scheduled_local_start_time": preflight["scheduled_local_start_time"],
        "stop_after_minutes": preflight["stop_after_minutes"],
        "runtime_state": preflight["runtime_state"],
        "start_receipt_count": preflight["start_receipt_count"],
        "stop_receipt_count": preflight["stop_receipt_count"],
        "ready_to_stop": preflight["ready_to_stop"],
        "confirmation_response": confirmation_response,
        "preflight_decision": preflight["decision"],
        "preflight_reason": preflight["reason"],
        "runtime_record_written": False,
        "decision": "blocked",
        "reason": reason,
    }


def _executed_payload(
    preflight: dict[str, object],
    confirmation_response: str,
    receipt: dict[str, object],
) -> dict[str, object]:
    return {
        "execution_kind": _EXECUTION_KIND,
        "session_id": preflight["session_id"],
        "course_id": preflight["course_id"],
        "source_kind": preflight["source_kind"],
        "selected_class_time_index": preflight["selected_class_time_index"],
        "scheduled_day_of_week": preflight["scheduled_day_of_week"],
        "scheduled_local_start_time": preflight["scheduled_local_start_time"],
        "stop_after_minutes": preflight["stop_after_minutes"],
        "runtime_state": preflight["runtime_state"],
        "start_receipt_count": preflight["start_receipt_count"],
        "stop_receipt_count": preflight["stop_receipt_count"],
        "ready_to_stop": preflight["ready_to_stop"],
        "confirmation_response": confirmation_response,
        "preflight_decision": preflight["decision"],
        "preflight_reason": preflight["reason"],
        "runtime_record_written": receipt["runtime_record_written"],
        "decision": "executed",
        "reason": "stop_receipt_written",
    }


def _stop_preview_from_preflight(preflight: dict[str, object]) -> dict[str, object]:
    return {
        "status": "enabled",
        "course_id": preflight["course_id"],
        "source_kind": preflight["source_kind"],
        "selected_class_time_index": preflight["selected_class_time_index"],
        "scheduled_day_of_week": preflight["scheduled_day_of_week"],
        "scheduled_local_start_time": preflight["scheduled_local_start_time"],
        "stop_after_minutes": preflight["stop_after_minutes"],
        "enabled": True,
    }


def _preflight_allows_stop(preflight: dict[str, object]) -> bool:
    return (
        preflight["ready_to_stop"] is True
        and preflight["decision"] == "allow"
        and preflight["reason"] == "ready_to_stop"
    )


def _ensure_receipt_matches_preflight(
    receipt: dict[str, object],
    preflight: dict[str, object],
) -> None:
    if (
        receipt["receipt_kind"] != _RECEIPT_KIND
        or receipt["status"] != "enabled"
        or receipt["session_id"] != preflight["session_id"]
        or receipt["course_id"] != preflight["course_id"]
        or receipt["source_kind"] != preflight["source_kind"]
        or receipt["selected_class_time_index"]
        != preflight["selected_class_time_index"]
        or receipt["scheduled_day_of_week"] != preflight["scheduled_day_of_week"]
        or receipt["scheduled_local_start_time"]
        != preflight["scheduled_local_start_time"]
        or receipt["stop_after_minutes"] != preflight["stop_after_minutes"]
        or receipt["enabled"] is not True
        or receipt["runtime_record_written"] is not True
    ):
        _fail()


def _preflight_safe_summary(
    payload: dict[str, object],
    *,
    expected_session_id: object,
    expected_course_id: object,
    expected_class_time_index: object,
    expected_source_kind: object,
) -> dict[str, object]:
    if type(payload) is not dict or tuple(payload) != _PREFLIGHT_KEYS:
        _fail()
    safe_expected_session_id = _safe_session_id(expected_session_id)
    safe_expected_course_id = _course_id(expected_course_id)
    safe_expected_class_time_index = _non_negative_int(expected_class_time_index)
    safe_expected_source_kind = _source_kind(expected_source_kind)
    preflight = {
        "preflight_kind": _exact_text(payload["preflight_kind"], _PREFLIGHT_KIND),
        "session_id": _safe_session_id(payload["session_id"]),
        "course_id": _course_id(payload["course_id"]),
        "source_kind": _source_kind(payload["source_kind"]),
        "selected_class_time_index": _non_negative_int(
            payload["selected_class_time_index"]
        ),
        "scheduled_day_of_week": _day_of_week(payload["scheduled_day_of_week"]),
        "scheduled_local_start_time": _local_time(
            payload["scheduled_local_start_time"]
        ),
        "stop_after_minutes": _stop_after_minutes(payload["stop_after_minutes"]),
        "runtime_state": _runtime_state(payload["runtime_state"]),
        "start_receipt_count": _non_negative_int(payload["start_receipt_count"]),
        "stop_receipt_count": _non_negative_int(payload["stop_receipt_count"]),
        "ready_to_stop": _bool_value(payload["ready_to_stop"]),
        "decision": _preflight_decision(payload["decision"]),
        "reason": _preflight_reason(payload["reason"]),
    }
    if (
        preflight["session_id"] != safe_expected_session_id
        or preflight["course_id"] != safe_expected_course_id
        or preflight["selected_class_time_index"] != safe_expected_class_time_index
        or preflight["source_kind"] != safe_expected_source_kind
    ):
        _fail()
    _validate_preflight_policy(preflight)
    return preflight


def _receipt_safe_summary(payload: dict[str, object]) -> dict[str, object]:
    if type(payload) is not dict or tuple(payload) != _RECEIPT_KEYS:
        _fail()
    receipt = {
        "receipt_kind": _exact_text(payload["receipt_kind"], _RECEIPT_KIND),
        "status": _exact_text(payload["status"], "enabled"),
        "session_id": _safe_session_id(payload["session_id"]),
        "course_id": _course_id(payload["course_id"]),
        "source_kind": _source_kind(payload["source_kind"]),
        "selected_class_time_index": _non_negative_int(
            payload["selected_class_time_index"]
        ),
        "scheduled_day_of_week": _day_of_week(payload["scheduled_day_of_week"]),
        "scheduled_local_start_time": _local_time(
            payload["scheduled_local_start_time"]
        ),
        "stop_after_minutes": _stop_after_minutes(payload["stop_after_minutes"]),
        "enabled": _bool_value(payload["enabled"]),
        "runtime_record_written": _bool_value(payload["runtime_record_written"]),
    }
    if receipt["enabled"] is not True or receipt["runtime_record_written"] is not True:
        _fail()
    return receipt


def _execution_safe_summary(
    payload: dict[str, object],
) -> StoredSessionWindowStopExecution:
    if type(payload) is not dict or tuple(payload) != _EXECUTION_KEYS:
        _fail()
    execution = {
        "execution_kind": _exact_text(payload["execution_kind"], _EXECUTION_KIND),
        "session_id": _safe_session_id(payload["session_id"]),
        "course_id": _course_id(payload["course_id"]),
        "source_kind": _source_kind(payload["source_kind"]),
        "selected_class_time_index": _non_negative_int(
            payload["selected_class_time_index"]
        ),
        "scheduled_day_of_week": _day_of_week(payload["scheduled_day_of_week"]),
        "scheduled_local_start_time": _local_time(
            payload["scheduled_local_start_time"]
        ),
        "stop_after_minutes": _stop_after_minutes(payload["stop_after_minutes"]),
        "runtime_state": _runtime_state(payload["runtime_state"]),
        "start_receipt_count": _non_negative_int(payload["start_receipt_count"]),
        "stop_receipt_count": _non_negative_int(payload["stop_receipt_count"]),
        "ready_to_stop": _bool_value(payload["ready_to_stop"]),
        "confirmation_response": _confirmation_response(
            payload["confirmation_response"]
        ),
        "preflight_decision": _preflight_decision(payload["preflight_decision"]),
        "preflight_reason": _execution_reason(payload["preflight_reason"]),
        "runtime_record_written": _bool_value(payload["runtime_record_written"]),
        "decision": _execution_decision(payload["decision"]),
        "reason": _execution_reason(payload["reason"]),
    }
    _validate_execution_policy(execution)
    return execution


def _validate_preflight_policy(preflight: dict[str, object]) -> None:
    if preflight["decision"] == "allow":
        if not _preflight_allows_stop(preflight):
            _fail()
        if (
            preflight["runtime_state"] != "started"
            or preflight["start_receipt_count"] != 1
            or preflight["stop_receipt_count"] != 0
        ):
            _fail()
    elif preflight["ready_to_stop"] is True:
        _fail()
    elif preflight["reason"] == "missing_runtime":
        _require_runtime_counts(preflight, "missing", 0, 0)
    elif preflight["reason"] == "not_started_runtime":
        _require_runtime_counts(preflight, "not_started", 0, 0)
    elif preflight["reason"] == "already_stopped_runtime":
        _require_runtime_counts(preflight, "stopped", 1, 1)
    elif preflight["reason"] == "inconsistent_runtime":
        if preflight["runtime_state"] != "inconsistent":
            _fail()
    elif preflight["reason"] == "source_mismatch":
        _require_runtime_counts(preflight, "started", 1, 0)
    elif preflight["reason"] != "disabled_stop_preview":
        _fail()


def _validate_execution_policy(payload: dict[str, object]) -> None:
    if payload["decision"] == "executed":
        if (
            payload["preflight_decision"] != "allow"
            or payload["preflight_reason"] != "ready_to_stop"
            or payload["ready_to_stop"] is not True
            or payload["confirmation_response"] != "confirmed"
            or payload["runtime_record_written"] is not True
            or payload["runtime_state"] != "started"
            or payload["start_receipt_count"] != 1
            or payload["stop_receipt_count"] != 0
            or payload["reason"] != "stop_receipt_written"
        ):
            _fail()
    elif payload["runtime_record_written"] is not False:
        _fail()
    elif payload["confirmation_response"] == "declined":
        if payload["preflight_decision"] == "allow":
            if (
                payload["preflight_reason"] != "ready_to_stop"
                or payload["reason"] != "confirmation_declined"
                or payload["ready_to_stop"] is not True
                or payload["runtime_state"] != "started"
                or payload["start_receipt_count"] != 1
                or payload["stop_receipt_count"] != 0
            ):
                _fail()
        elif payload["reason"] != payload["preflight_reason"]:
            _fail()
    elif (
        payload["preflight_decision"] != "block"
        or payload["reason"] != payload["preflight_reason"]
    ):
        _fail()


def _require_runtime_counts(
    payload: dict[str, object],
    runtime_state: str,
    start_count: int,
    stop_count: int,
) -> None:
    if (
        payload["runtime_state"] != runtime_state
        or payload["start_receipt_count"] != start_count
        or payload["stop_receipt_count"] != stop_count
    ):
        _fail()


def _safe_session_id(value: object) -> str:
    session_id = _required_text(value)
    if (
        session_id in {".", ".."}
        or "/" in session_id
        or "\\" in session_id
        or ":" in session_id
        or _SESSION_ID_PATTERN.fullmatch(session_id) is None
    ):
        _fail()
    return session_id


def _course_id(value: object) -> str:
    course_id = _required_text(value)
    if _COURSE_ID_PATTERN.fullmatch(course_id) is None:
        _fail()
    return course_id


def _source_kind(value: object) -> str:
    source_kind = _required_text(value)
    if source_kind not in _SOURCE_KINDS:
        _fail()
    return source_kind


def _day_of_week(value: object) -> str:
    day_of_week = _required_text(value)
    if day_of_week not in _DAYS_OF_WEEK:
        _fail()
    return day_of_week


def _local_time(value: object) -> str:
    local_time = _required_text(value)
    if _LOCAL_TIME_PATTERN.fullmatch(local_time) is None:
        _fail()
    hour_text, minute_text = local_time.split(":")
    if int(hour_text) > 23 or int(minute_text) > 59:
        _fail()
    return local_time


def _runtime_state(value: object) -> str:
    runtime_state = _required_text(value)
    if runtime_state not in _RUNTIME_STATES:
        _fail()
    return runtime_state


def _preflight_decision(value: object) -> str:
    decision = _required_text(value)
    if decision not in _PREFLIGHT_DECISIONS:
        _fail()
    return decision


def _preflight_reason(value: object) -> str:
    reason = _required_text(value)
    if reason not in _PREFLIGHT_REASONS:
        _fail()
    return reason


def _confirmation_response(value: object) -> str:
    response = _required_text(value)
    if response not in _CONFIRMATION_RESPONSES:
        _fail()
    return response


def _execution_decision(value: object) -> str:
    decision = _required_text(value)
    if decision not in _EXECUTION_DECISIONS:
        _fail()
    return decision


def _execution_reason(value: object) -> str:
    reason = _required_text(value)
    if reason not in _EXECUTION_REASONS:
        _fail()
    return reason


def _stop_after_minutes(value: object) -> int:
    minutes = _positive_int(value)
    if minutes > _STOP_AFTER_MINUTES_MAX:
        _fail()
    return minutes


def _positive_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
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


def _exact_text(value: object, expected: str) -> str:
    text = _required_text(value)
    if text != expected:
        _fail()
    return text


def _required_text(value: object) -> str:
    if not isinstance(value, str):
        _fail()
    if (
        not value
        or value.strip() != value
        or len(value) > _TEXT_MAX_LENGTH
        or _has_control_character(value)
        or _has_forbidden_uri_or_unc(value)
        or _has_traversal_part(value)
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


def _fail() -> NoReturn:
    raise ValueError(STORED_SESSION_WINDOW_STOP_EXECUTION_ERROR)
