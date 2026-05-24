from __future__ import annotations

import re
from pathlib import Path
from typing import NoReturn

from async_scholar.schedule_store import load_course_schedule_session_stop_input
from async_scholar.session_stop import build_session_stop_preview_from_store_input
from async_scholar.session_window_runtime_summary import (
    build_stored_session_window_runtime_summary,
)

STORED_SESSION_WINDOW_STOP_EXECUTION_PREFLIGHT_ERROR = (
    "stored session window stop execution preflight could not be built"
)

StoredSessionWindowStopExecutionPreflight = dict[str, object]

_PREFLIGHT_KIND = "stored_session_window_stop_execution_preflight"
_RUNTIME_FILENAME = "runtime.jsonl"
_RUNTIME_SUMMARY_KIND = "stored_session_window_runtime_summary"
_START_RECEIPT_KIND = "stored_session_window_start_receipt"
_STOP_RECEIPT_KIND = "stored_session_window_stop_receipt"
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
_PREVIEW_STATUSES = frozenset(("enabled", "disabled"))
_RUNTIME_STATES = frozenset(
    ("missing", "not_started", "started", "stopped", "inconsistent")
)
_RECEIPT_KINDS = frozenset(("none", _START_RECEIPT_KIND, _STOP_RECEIPT_KIND))
_DECISIONS = frozenset(("allow", "block"))
_REASONS = frozenset(
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
_STOP_AFTER_MINUTES_MAX = 24 * 60
_TEXT_MAX_LENGTH = 128
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
_RUNTIME_SUMMARY_KEYS = (
    "summary_kind",
    "session_id",
    "runtime_record_count",
    "start_receipt_count",
    "stop_receipt_count",
    "lifecycle_status",
    "session_active",
    "session_stopped",
    "last_receipt_kind",
    "last_source_kind",
)
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


def build_stored_session_window_stop_execution_preflight_from_store(
    db_path: str | Path,
    archive_root: str | Path,
    session_id: str,
    course_id: str,
    class_time_index: int,
    source_kind: str,
    *,
    enabled: bool = True,
) -> StoredSessionWindowStopExecutionPreflight:
    try:
        safe_session_id = _safe_session_id(session_id)
        safe_course_id = _course_id(course_id)
        safe_class_time_index = _non_negative_int(class_time_index)
        safe_source_kind = _source_kind(source_kind)
        stop_preview = _stop_preview_safe_summary(
            build_session_stop_preview_from_store_input(
                load_course_schedule_session_stop_input(
                    db_path,
                    safe_course_id,
                    safe_class_time_index,
                ),
                safe_source_kind,
                enabled=enabled,
            ),
            expected_course_id=safe_course_id,
            expected_class_time_index=safe_class_time_index,
            expected_source_kind=safe_source_kind,
        )
        runtime = _runtime_summary_or_missing(archive_root, safe_session_id)
        return _preflight_safe_summary(
            _build_preflight_payload(safe_session_id, stop_preview, runtime)
        )
    except (KeyError, OSError, RuntimeError, TypeError, ValueError):
        raise ValueError(STORED_SESSION_WINDOW_STOP_EXECUTION_PREFLIGHT_ERROR) from None


def _build_preflight_payload(
    session_id: str,
    stop_preview: dict[str, object],
    runtime: dict[str, object],
) -> dict[str, object]:
    runtime_state = _runtime_state(runtime["lifecycle_status"])
    start_count = _non_negative_int(runtime["start_receipt_count"])
    stop_count = _non_negative_int(runtime["stop_receipt_count"])
    source_kind = _source_kind(stop_preview["source_kind"])

    if not _bool_value(stop_preview["enabled"]):
        ready_to_stop = False
        decision = "block"
        reason = "disabled_stop_preview"
    elif runtime_state == "missing":
        ready_to_stop = False
        decision = "block"
        reason = "missing_runtime"
    elif runtime_state == "not_started":
        ready_to_stop = False
        decision = "block"
        reason = "not_started_runtime"
    elif runtime_state == "stopped":
        ready_to_stop = False
        decision = "block"
        reason = "already_stopped_runtime"
    elif runtime_state == "inconsistent":
        ready_to_stop = False
        decision = "block"
        reason = "inconsistent_runtime"
    elif runtime["last_source_kind"] != source_kind:
        ready_to_stop = False
        decision = "block"
        reason = "source_mismatch"
    else:
        ready_to_stop = True
        decision = "allow"
        reason = "ready_to_stop"

    return {
        "preflight_kind": _PREFLIGHT_KIND,
        "session_id": session_id,
        "course_id": stop_preview["course_id"],
        "source_kind": source_kind,
        "selected_class_time_index": stop_preview["selected_class_time_index"],
        "scheduled_day_of_week": stop_preview["scheduled_day_of_week"],
        "scheduled_local_start_time": stop_preview["scheduled_local_start_time"],
        "stop_after_minutes": stop_preview["stop_after_minutes"],
        "runtime_state": runtime_state,
        "start_receipt_count": start_count,
        "stop_receipt_count": stop_count,
        "ready_to_stop": ready_to_stop,
        "decision": decision,
        "reason": reason,
    }


def _runtime_summary_or_missing(
    archive_root: str | Path,
    session_id: str,
) -> dict[str, object]:
    archive_root_path = _existing_safe_archive_root(archive_root)
    session_dir = archive_root_path / session_id
    _ensure_candidate_inside(session_dir, archive_root_path)
    try:
        if session_dir.is_symlink():
            _fail()
        if not session_dir.exists():
            return _missing_runtime_summary(session_id)
        if not session_dir.is_dir():
            _fail()
        safe_session_dir = session_dir.resolve(strict=True)
    except (OSError, RuntimeError):
        _fail()
    _ensure_inside(safe_session_dir, archive_root_path)

    runtime_path = safe_session_dir / _RUNTIME_FILENAME
    _ensure_candidate_inside(runtime_path, safe_session_dir)
    _ensure_candidate_inside(runtime_path, archive_root_path)
    try:
        if runtime_path.is_symlink():
            _fail()
        if not runtime_path.exists():
            return _missing_runtime_summary(session_id)
        if not runtime_path.is_file():
            _fail()
        safe_runtime_path = runtime_path.resolve(strict=True)
    except (OSError, RuntimeError):
        _fail()
    _ensure_inside(safe_runtime_path, safe_session_dir)
    _ensure_inside(safe_runtime_path, archive_root_path)

    return _runtime_summary_safe_summary(
        build_stored_session_window_runtime_summary(archive_root_path, session_id),
        allow_missing=False,
        expected_session_id=session_id,
    )


def _missing_runtime_summary(session_id: str) -> dict[str, object]:
    return _runtime_summary_safe_summary(
        {
            "summary_kind": _RUNTIME_SUMMARY_KIND,
            "session_id": session_id,
            "runtime_record_count": 0,
            "start_receipt_count": 0,
            "stop_receipt_count": 0,
            "lifecycle_status": "missing",
            "session_active": False,
            "session_stopped": False,
            "last_receipt_kind": "none",
            "last_source_kind": "none",
        },
        allow_missing=True,
        expected_session_id=session_id,
    )


def _stop_preview_safe_summary(
    payload: dict[str, object],
    *,
    expected_course_id: str,
    expected_class_time_index: int,
    expected_source_kind: str,
) -> dict[str, object]:
    if type(payload) is not dict or tuple(payload) != _STOP_PREVIEW_KEYS:
        _fail()
    status = _preview_status(payload["status"])
    enabled = _bool_value(payload["enabled"])
    if (status == "enabled") is not enabled:
        _fail()
    stop_preview = {
        "status": status,
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
        "enabled": enabled,
    }
    if (
        stop_preview["course_id"] != expected_course_id
        or stop_preview["selected_class_time_index"] != expected_class_time_index
        or stop_preview["source_kind"] != expected_source_kind
    ):
        _fail()
    return stop_preview


def _runtime_summary_safe_summary(
    payload: dict[str, object],
    *,
    allow_missing: bool,
    expected_session_id: str,
) -> dict[str, object]:
    if type(payload) is not dict or tuple(payload) != _RUNTIME_SUMMARY_KEYS:
        _fail()
    runtime = {
        "summary_kind": _exact_text(payload["summary_kind"], _RUNTIME_SUMMARY_KIND),
        "session_id": _safe_session_id(payload["session_id"]),
        "runtime_record_count": _non_negative_int(payload["runtime_record_count"]),
        "start_receipt_count": _non_negative_int(payload["start_receipt_count"]),
        "stop_receipt_count": _non_negative_int(payload["stop_receipt_count"]),
        "lifecycle_status": _runtime_state(payload["lifecycle_status"]),
        "session_active": _bool_value(payload["session_active"]),
        "session_stopped": _bool_value(payload["session_stopped"]),
        "last_receipt_kind": _receipt_kind(payload["last_receipt_kind"]),
        "last_source_kind": _runtime_source_kind(payload["last_source_kind"]),
    }
    if runtime["session_id"] != expected_session_id:
        _fail()
    _validate_runtime_policy(runtime, allow_missing=allow_missing)
    return runtime


def _validate_runtime_policy(
    runtime: dict[str, object],
    *,
    allow_missing: bool,
) -> None:
    lifecycle = runtime["lifecycle_status"]
    record_count = _non_negative_int(runtime["runtime_record_count"])
    start_count = _non_negative_int(runtime["start_receipt_count"])
    stop_count = _non_negative_int(runtime["stop_receipt_count"])
    active = _bool_value(runtime["session_active"])
    stopped = _bool_value(runtime["session_stopped"])
    last_kind = _receipt_kind(runtime["last_receipt_kind"])
    last_source = _runtime_source_kind(runtime["last_source_kind"])

    if record_count != start_count + stop_count:
        _fail()
    if lifecycle == "missing":
        if (
            not allow_missing
            or record_count != 0
            or start_count != 0
            or stop_count != 0
            or active
            or stopped
            or last_kind != "none"
            or last_source != "none"
        ):
            _fail()
    elif lifecycle == "not_started":
        if (
            record_count != 0
            or start_count != 0
            or stop_count != 0
            or active
            or stopped
            or last_kind != "none"
            or last_source != "none"
        ):
            _fail()
    elif lifecycle == "started":
        if (
            record_count != 1
            or start_count != 1
            or stop_count != 0
            or not active
            or stopped
            or last_kind != _START_RECEIPT_KIND
            or last_source not in _SOURCE_KINDS
        ):
            _fail()
    elif lifecycle == "stopped":
        if (
            record_count != 2
            or start_count != 1
            or stop_count != 1
            or active
            or not stopped
            or last_kind != _STOP_RECEIPT_KIND
            or last_source not in _SOURCE_KINDS
        ):
            _fail()
    elif active or stopped:
        _fail()


def _preflight_safe_summary(payload: dict[str, object]) -> dict[str, object]:
    if type(payload) is not dict or tuple(payload) != _PREFLIGHT_KEYS:
        _fail()
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
        "decision": _decision(payload["decision"]),
        "reason": _reason(payload["reason"]),
    }
    if preflight["ready_to_stop"] is not (
        preflight["decision"] == "allow" and preflight["reason"] == "ready_to_stop"
    ):
        _fail()
    return preflight


def _existing_safe_archive_root(archive_root: object) -> Path:
    raw_archive_root = _safe_path_text(archive_root)
    archive_root_path = Path(raw_archive_root)
    try:
        if (
            archive_root_path.is_symlink()
            or not archive_root_path.exists()
            or not archive_root_path.is_dir()
        ):
            _fail()
        safe_archive_root = archive_root_path.resolve(strict=True)
    except (OSError, RuntimeError):
        _fail()
    if not safe_archive_root.is_dir():
        _fail()
    return safe_archive_root


def _safe_path_text(path: object) -> str:
    if not isinstance(path, (str, Path)):
        _fail()
    raw_path = str(path)
    if (
        not raw_path
        or raw_path.strip() != raw_path
        or _has_control_character(raw_path)
        or _has_forbidden_uri_or_unc(raw_path)
        or _has_traversal_part(raw_path)
    ):
        _fail()
    return raw_path


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


def _runtime_source_kind(value: object) -> str:
    source_kind = _required_text(value)
    if source_kind != "none" and source_kind not in _SOURCE_KINDS:
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


def _preview_status(value: object) -> str:
    status = _required_text(value)
    if status not in _PREVIEW_STATUSES:
        _fail()
    return status


def _runtime_state(value: object) -> str:
    runtime_state = _required_text(value)
    if runtime_state not in _RUNTIME_STATES:
        _fail()
    return runtime_state


def _receipt_kind(value: object) -> str:
    receipt_kind = _required_text(value)
    if receipt_kind not in _RECEIPT_KINDS:
        _fail()
    return receipt_kind


def _decision(value: object) -> str:
    decision = _required_text(value)
    if decision not in _DECISIONS:
        _fail()
    return decision


def _reason(value: object) -> str:
    reason = _required_text(value)
    if reason not in _REASONS:
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


def _ensure_candidate_inside(path: Path, parent: Path) -> None:
    try:
        candidate_parent = path.parent.resolve(strict=True)
    except (OSError, RuntimeError):
        _fail()
    _ensure_inside(candidate_parent / path.name, parent)


def _ensure_inside(path: Path, parent: Path) -> None:
    try:
        path.relative_to(parent)
    except ValueError:
        _fail()


def _fail() -> NoReturn:
    raise ValueError(STORED_SESSION_WINDOW_STOP_EXECUTION_PREFLIGHT_ERROR)
