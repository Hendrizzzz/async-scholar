from __future__ import annotations

import json
import re
from pathlib import Path

STORED_SESSION_WINDOW_STOP_RECEIPT_ERROR = (
    "stored session window stop receipt could not be built"
)

_RECEIPT_KIND = "stored_session_window_stop_receipt"
_RUNTIME_FILENAME = "runtime.jsonl"
_STOP_AFTER_MINUTES_MAX = 24 * 60
_TEXT_MAX_LENGTH = 128
_COURSE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")
_LOCAL_START_TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")
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
_SOURCE_KIND_VALUES = frozenset(("file", "mic"))
_STATUS_VALUES = frozenset(("enabled", "disabled"))
_STOP_PREVIEW_KEYS = frozenset(
    (
        "status",
        "course_id",
        "source_kind",
        "selected_class_time_index",
        "scheduled_day_of_week",
        "scheduled_local_start_time",
        "stop_after_minutes",
        "enabled",
    )
)


def write_stored_session_window_stop_receipt(
    stop_preview_summary: dict[str, object],
    archive_root: Path,
    session_id: str,
) -> dict[str, object]:
    safe_preview = _revalidated_stop_preview_summary(stop_preview_summary)
    safe_session_id = _safe_session_id(session_id)
    receipt = _build_receipt_summary(
        safe_preview,
        safe_session_id,
        runtime_record_written=False,
    )
    if safe_preview["enabled"] is False:
        return receipt

    archive_root_path = _existing_safe_archive_root(archive_root)
    session_dir = _existing_safe_session_dir(archive_root_path, safe_session_id)
    runtime_path = _existing_safe_runtime_path(archive_root_path, session_dir)
    receipt["runtime_record_written"] = True

    try:
        with runtime_path.open("r+", encoding="utf-8") as runtime_file:
            runtime_file.seek(0, 2)
            runtime_file.write(_compact_json_line(receipt))
    except OSError as exc:
        raise ValueError(STORED_SESSION_WINDOW_STOP_RECEIPT_ERROR) from exc

    return receipt


def _revalidated_stop_preview_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    if not isinstance(payload, dict) or frozenset(payload) != _STOP_PREVIEW_KEYS:
        _fail()

    status = _clean_status(payload["status"])
    enabled = _clean_bool(payload["enabled"])
    if (status == "enabled") != enabled:
        _fail()

    return {
        "status": status,
        "course_id": _clean_course_id(payload["course_id"]),
        "source_kind": _clean_source_kind(payload["source_kind"]),
        "selected_class_time_index": _clean_non_negative_int(
            payload["selected_class_time_index"]
        ),
        "scheduled_day_of_week": _clean_day_of_week(payload["scheduled_day_of_week"]),
        "scheduled_local_start_time": _clean_local_start_time(
            payload["scheduled_local_start_time"]
        ),
        "stop_after_minutes": _clean_stop_after_minutes(payload["stop_after_minutes"]),
        "enabled": enabled,
    }


def _build_receipt_summary(
    stop_preview_summary: dict[str, object],
    session_id: str,
    *,
    runtime_record_written: bool,
) -> dict[str, object]:
    return {
        "receipt_kind": _RECEIPT_KIND,
        "status": stop_preview_summary["status"],
        "session_id": session_id,
        "course_id": stop_preview_summary["course_id"],
        "source_kind": stop_preview_summary["source_kind"],
        "selected_class_time_index": stop_preview_summary["selected_class_time_index"],
        "scheduled_day_of_week": stop_preview_summary["scheduled_day_of_week"],
        "scheduled_local_start_time": stop_preview_summary[
            "scheduled_local_start_time"
        ],
        "stop_after_minutes": stop_preview_summary["stop_after_minutes"],
        "enabled": stop_preview_summary["enabled"],
        "runtime_record_written": runtime_record_written,
    }


def _clean_status(value: object) -> str:
    status = _clean_required_text(value)
    if status not in _STATUS_VALUES:
        _fail()
    return status


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


def _clean_local_start_time(value: object) -> str:
    local_start_time = _clean_required_text(value)
    if _LOCAL_START_TIME_PATTERN.fullmatch(local_start_time) is None:
        _fail()
    hour_text, minute_text = local_start_time.split(":")
    if int(hour_text) > 23 or int(minute_text) > 59:
        _fail()
    return local_start_time


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


def _clean_bool(value: object) -> bool:
    if not isinstance(value, bool):
        _fail()
    return value


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


def _existing_safe_archive_root(archive_root: Path) -> Path:
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
        raise ValueError(STORED_SESSION_WINDOW_STOP_RECEIPT_ERROR) from exc
    if not archive_root_resolved.is_dir():
        _fail()
    return archive_root_resolved


def _safe_session_id(session_id: object) -> str:
    if not isinstance(session_id, str):
        _fail()
    if (
        not session_id
        or session_id.strip() != session_id
        or _has_control_character(session_id)
        or session_id in {".", ".."}
        or "/" in session_id
        or "\\" in session_id
        or ":" in session_id
        or _has_forbidden_uri_or_unc(session_id)
        or _has_traversal_part(session_id)
        or _SESSION_ID_PATTERN.fullmatch(session_id) is None
    ):
        _fail()
    return session_id


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
        raise ValueError(STORED_SESSION_WINDOW_STOP_RECEIPT_ERROR) from exc
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
        ):
            _fail()
        runtime_resolved = runtime_path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(STORED_SESSION_WINDOW_STOP_RECEIPT_ERROR) from exc
    _ensure_inside(runtime_resolved, session_dir)
    _ensure_inside(runtime_resolved, archive_root)
    return runtime_path


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
        raise ValueError(STORED_SESSION_WINDOW_STOP_RECEIPT_ERROR) from exc
    _ensure_inside(candidate_parent / path.name, parent)


def _ensure_inside(path: Path, parent: Path) -> None:
    try:
        path.relative_to(parent)
    except ValueError as exc:
        raise ValueError(STORED_SESSION_WINDOW_STOP_RECEIPT_ERROR) from exc


def _compact_json_line(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"


def _fail() -> None:
    raise ValueError(STORED_SESSION_WINDOW_STOP_RECEIPT_ERROR)
