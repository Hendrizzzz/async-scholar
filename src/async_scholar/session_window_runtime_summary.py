from __future__ import annotations

import json
import re
import stat
from pathlib import Path
from typing import NoReturn

STORED_SESSION_WINDOW_RUNTIME_SUMMARY_ERROR = (
    "stored session window runtime summary could not be built"
)

_SUMMARY_KIND = "stored_session_window_runtime_summary"
_START_RECEIPT_KIND = "stored_session_window_start_receipt"
_STOP_RECEIPT_KIND = "stored_session_window_stop_receipt"
_RUNTIME_FILENAME = "runtime.jsonl"
_STOP_AFTER_MINUTES_MAX = 24 * 60
_TEXT_MAX_LENGTH = 128
_SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
_COURSE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_LOCAL_TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")
_SOURCE_KIND_VALUES = frozenset(("file", "mic"))
_DAY_OF_WEEK_VALUES = frozenset(
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
_START_RECEIPT_KEYS = frozenset(
    (
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
)
_STOP_RECEIPT_KEYS = frozenset(
    (
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
)


def build_stored_session_window_runtime_summary(
    archive_root: str | Path,
    session_id: str,
) -> dict[str, object]:
    archive_root_path = _existing_safe_archive_root(archive_root)
    safe_session_id = _safe_session_id(session_id)
    session_dir = _existing_safe_session_dir(archive_root_path, safe_session_id)
    runtime_path = _existing_safe_runtime_path(archive_root_path, session_dir)
    records = _read_runtime_records(runtime_path, safe_session_id)
    lifecycle_status = _lifecycle_status(records)
    start_receipt_count = sum(
        1 for record in records if record["receipt_kind"] == _START_RECEIPT_KIND
    )
    stop_receipt_count = sum(
        1 for record in records if record["receipt_kind"] == _STOP_RECEIPT_KIND
    )
    last_record = records[-1] if records else None

    return {
        "summary_kind": _SUMMARY_KIND,
        "session_id": safe_session_id,
        "runtime_record_count": len(records),
        "start_receipt_count": start_receipt_count,
        "stop_receipt_count": stop_receipt_count,
        "lifecycle_status": lifecycle_status,
        "session_active": lifecycle_status == "started",
        "session_stopped": lifecycle_status == "stopped",
        "last_receipt_kind": (
            "none" if last_record is None else last_record["receipt_kind"]
        ),
        "last_source_kind": "none"
        if last_record is None
        else last_record["source_kind"],
    }


def _read_runtime_records(
    runtime_path: Path,
    session_id: str,
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    try:
        with runtime_path.open("r", encoding="utf-8") as runtime_file:
            for raw_line in runtime_file:
                records.append(_validated_runtime_line(raw_line, session_id))
    except (OSError, UnicodeError) as exc:
        raise ValueError(STORED_SESSION_WINDOW_RUNTIME_SUMMARY_ERROR) from exc
    return records


def _validated_runtime_line(raw_line: str, session_id: str) -> dict[str, object]:
    line = raw_line.removesuffix("\n")
    if not line:
        _fail()
    try:
        payload = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(STORED_SESSION_WINDOW_RUNTIME_SUMMARY_ERROR) from exc
    if not isinstance(payload, dict) or _compact_json(payload) != line:
        _fail()
    return _validated_receipt(payload, session_id)


def _validated_receipt(
    payload: dict[str, object],
    session_id: str,
) -> dict[str, object]:
    receipt_kind = payload.get("receipt_kind")
    if receipt_kind == _START_RECEIPT_KIND:
        return _validated_start_receipt(payload, session_id)
    if receipt_kind == _STOP_RECEIPT_KIND:
        return _validated_stop_receipt(payload, session_id)
    _fail()


def _validated_start_receipt(
    payload: dict[str, object],
    session_id: str,
) -> dict[str, object]:
    if frozenset(payload) != _START_RECEIPT_KEYS:
        _fail()
    receipt = {
        "receipt_kind": _clean_exact_text(
            payload["receipt_kind"],
            _START_RECEIPT_KIND,
        ),
        "status": _clean_exact_text(payload["status"], "authorized"),
        "session_id": _clean_session_id(payload["session_id"]),
        "source_kind": _clean_source_kind(payload["source_kind"]),
        "clock_day_of_week": _clean_day_of_week(payload["clock_day_of_week"]),
        "clock_local_time": _clean_local_time(payload["clock_local_time"]),
        "course_count": _clean_non_negative_int(payload["course_count"]),
        "due_count": _clean_positive_int(payload["due_count"]),
        "ready_to_start": _clean_exact_bool(payload["ready_to_start"], True),
        "confirmation_required": _clean_exact_bool(
            payload["confirmation_required"],
            True,
        ),
        "confirmation_status": _clean_exact_text(
            payload["confirmation_status"],
            "required",
        ),
        "confirmation_response": _clean_exact_text(
            payload["confirmation_response"],
            "confirmed",
        ),
        "confirmation_verified": _clean_exact_bool(
            payload["confirmation_verified"],
            True,
        ),
        "authorized": _clean_exact_bool(payload["authorized"], True),
        "authorized_start_count": _clean_positive_int(
            payload["authorized_start_count"]
        ),
        "blocked_start_count": _clean_exact_int(payload["blocked_start_count"], 0),
        "block_reason": _clean_exact_text(payload["block_reason"], "none"),
        "runtime_record_written": _clean_exact_bool(
            payload["runtime_record_written"],
            True,
        ),
    }
    if (
        receipt["session_id"] != session_id
        or receipt["authorized_start_count"] != receipt["due_count"]
        or receipt["course_count"] < receipt["due_count"]
    ):
        _fail()
    return receipt


def _validated_stop_receipt(
    payload: dict[str, object],
    session_id: str,
) -> dict[str, object]:
    if frozenset(payload) != _STOP_RECEIPT_KEYS:
        _fail()
    receipt = {
        "receipt_kind": _clean_exact_text(payload["receipt_kind"], _STOP_RECEIPT_KIND),
        "status": _clean_exact_text(payload["status"], "enabled"),
        "session_id": _clean_session_id(payload["session_id"]),
        "course_id": _clean_course_id(payload["course_id"]),
        "source_kind": _clean_source_kind(payload["source_kind"]),
        "selected_class_time_index": _clean_non_negative_int(
            payload["selected_class_time_index"]
        ),
        "scheduled_day_of_week": _clean_day_of_week(payload["scheduled_day_of_week"]),
        "scheduled_local_start_time": _clean_local_time(
            payload["scheduled_local_start_time"]
        ),
        "stop_after_minutes": _clean_stop_after_minutes(payload["stop_after_minutes"]),
        "enabled": _clean_exact_bool(payload["enabled"], True),
        "runtime_record_written": _clean_exact_bool(
            payload["runtime_record_written"],
            True,
        ),
    }
    if receipt["session_id"] != session_id:
        _fail()
    return receipt


def _lifecycle_status(records: list[dict[str, object]]) -> str:
    receipt_kinds = [record["receipt_kind"] for record in records]
    if not receipt_kinds:
        return "not_started"
    if receipt_kinds == [_START_RECEIPT_KIND]:
        return "started"
    if receipt_kinds == [_START_RECEIPT_KIND, _STOP_RECEIPT_KIND]:
        return "stopped"
    return "inconsistent"


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
        archive_root_resolved = archive_root_path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(STORED_SESSION_WINDOW_RUNTIME_SUMMARY_ERROR) from exc
    if not archive_root_resolved.is_dir():
        _fail()
    return archive_root_resolved


def _safe_session_id(session_id: object) -> str:
    return _clean_session_id(session_id)


def _existing_safe_session_dir(archive_root: Path, session_id: str) -> Path:
    session_dir = archive_root / session_id
    _ensure_candidate_inside(session_dir, archive_root)
    try:
        if (
            session_dir.is_symlink()
            or not session_dir.exists()
            or not session_dir.is_dir()
        ):
            _fail()
        session_dir_resolved = session_dir.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(STORED_SESSION_WINDOW_RUNTIME_SUMMARY_ERROR) from exc
    _ensure_inside(session_dir_resolved, archive_root)
    return session_dir_resolved


def _existing_safe_runtime_path(archive_root: Path, session_dir: Path) -> Path:
    runtime_path = session_dir / _RUNTIME_FILENAME
    _ensure_candidate_inside(runtime_path, session_dir)
    _ensure_candidate_inside(runtime_path, archive_root)
    try:
        if (
            runtime_path.is_symlink()
            or not runtime_path.exists()
            or not runtime_path.is_file()
            or not stat.S_ISREG(runtime_path.stat().st_mode)
        ):
            _fail()
        runtime_resolved = runtime_path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(STORED_SESSION_WINDOW_RUNTIME_SUMMARY_ERROR) from exc
    _ensure_inside(runtime_resolved, session_dir)
    _ensure_inside(runtime_resolved, archive_root)
    return runtime_resolved


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


def _clean_session_id(value: object) -> str:
    session_id = _clean_required_text(value)
    if (
        session_id in {".", ".."}
        or "/" in session_id
        or "\\" in session_id
        or ":" in session_id
        or _SESSION_ID_PATTERN.fullmatch(session_id) is None
    ):
        _fail()
    return session_id


def _clean_course_id(value: object) -> str:
    course_id = _clean_required_text(value)
    if _COURSE_ID_PATTERN.fullmatch(course_id) is None:
        _fail()
    return course_id


def _clean_source_kind(value: object) -> str:
    source_kind = _clean_required_text(value)
    if source_kind not in _SOURCE_KIND_VALUES:
        _fail()
    return source_kind


def _clean_day_of_week(value: object) -> str:
    day_of_week = _clean_required_text(value)
    if day_of_week not in _DAY_OF_WEEK_VALUES:
        _fail()
    return day_of_week


def _clean_local_time(value: object) -> str:
    local_time = _clean_required_text(value)
    if _LOCAL_TIME_PATTERN.fullmatch(local_time) is None:
        _fail()
    hour_text, minute_text = local_time.split(":")
    if int(hour_text) > 23 or int(minute_text) > 59:
        _fail()
    return local_time


def _clean_stop_after_minutes(value: object) -> int:
    stop_after_minutes = _clean_positive_int(value)
    if stop_after_minutes > _STOP_AFTER_MINUTES_MAX:
        _fail()
    return stop_after_minutes


def _clean_positive_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        _fail()
    return value


def _clean_non_negative_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        _fail()
    return value


def _clean_exact_int(value: object, expected: int) -> int:
    clean_value = _clean_non_negative_int(value)
    if clean_value != expected:
        _fail()
    return clean_value


def _clean_exact_bool(value: object, expected: bool) -> bool:
    if not isinstance(value, bool) or value is not expected:
        _fail()
    return value


def _clean_exact_text(value: object, expected: str) -> str:
    clean_value = _clean_required_text(value)
    if clean_value != expected:
        _fail()
    return clean_value


def _clean_required_text(value: object) -> str:
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
    except (OSError, RuntimeError) as exc:
        raise ValueError(STORED_SESSION_WINDOW_RUNTIME_SUMMARY_ERROR) from exc
    _ensure_inside(candidate_parent / path.name, parent)


def _ensure_inside(path: Path, parent: Path) -> None:
    try:
        path.relative_to(parent)
    except ValueError as exc:
        raise ValueError(STORED_SESSION_WINDOW_RUNTIME_SUMMARY_ERROR) from exc


def _compact_json(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _fail() -> NoReturn:
    raise ValueError(STORED_SESSION_WINDOW_RUNTIME_SUMMARY_ERROR)
