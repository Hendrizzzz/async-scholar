"""Local one-shot session-window lifecycle smoke helper."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, NoReturn, TypedDict

from async_scholar.course_metadata import CourseMetadata
from async_scholar.schedule_config import ScheduleConfig
from async_scholar.schedule_store import save_course_schedule
from async_scholar.scheduled_start import ScheduledStartClock
from async_scholar.session_window_execution import (
    build_stored_session_window_execution_from_store,
)
from async_scholar.session_window_stop_execution import (
    build_stored_session_window_stop_execution_from_store,
)

SESSION_WINDOW_LIFECYCLE_SMOKE_ERROR = (
    "session window lifecycle smoke could not be built"
)

LifecycleStatus = Literal["completed", "disabled"]
LifecycleDecision = Literal["executed", "disabled"]

_LIFECYCLE_KIND = "local_session_window_lifecycle_smoke"
_COURSE_ID = "lifecycle101"
_SESSION_ID = "lifecycle-smoke-session"
_SOURCE_KIND = "file"
_DAY_OF_WEEK = "monday"
_LOCAL_START_TIME = "09:00"
_DURATION_MINUTES = 60
_CLASS_TIME_INDEX = 0
_CONFIRMED = "confirmed"
_TEXT_MAX_LENGTH = 260

_START_KEYS = (
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
_STOP_KEYS = (
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


class LocalSessionWindowLifecycleSmokeResult(TypedDict):
    lifecycle_kind: str
    status: LifecycleStatus
    start_decision: LifecycleDecision
    start_reason: str
    start_runtime_record_written: bool
    stop_decision: LifecycleDecision
    stop_reason: str
    stop_runtime_record_written: bool
    gate_d_pass_claimed: bool
    product_promise_alpha_pass_claimed: bool


def build_local_session_window_lifecycle_smoke(
    db_path: str | Path,
    archive_root: str | Path,
    *,
    enabled: bool = True,
) -> LocalSessionWindowLifecycleSmokeResult:
    """Run the bounded fixed local start/stop lifecycle."""

    if enabled is False:
        return _disabled_result()
    if enabled is not True:
        _fail()

    try:
        save_course_schedule(
            db_path,
            CourseMetadata(course_id=_COURSE_ID, title="Synthetic Course"),
            ScheduleConfig(
                course_id=_COURSE_ID,
                class_times=[
                    {
                        "day_of_week": _DAY_OF_WEEK,
                        "local_start_time": _LOCAL_START_TIME,
                        "duration_minutes": _DURATION_MINUTES,
                    }
                ],
            ),
        )
        archive_path = _prepare_archive_session_dir(archive_root)
        clock = ScheduledStartClock(
            day_of_week=_DAY_OF_WEEK,
            local_time=_LOCAL_START_TIME,
        )
        start = _safe_start_execution(
            build_stored_session_window_execution_from_store(
                db_path,
                archive_path,
                _SESSION_ID,
                _SOURCE_KIND,
                clock,
                _CONFIRMED,
                enabled=True,
            )
        )
        stop = _safe_stop_execution(
            build_stored_session_window_stop_execution_from_store(
                db_path,
                archive_path,
                _SESSION_ID,
                _COURSE_ID,
                _CLASS_TIME_INDEX,
                _SOURCE_KIND,
                _CONFIRMED,
                enabled=True,
            )
        )
        return _completed_result(start, stop)
    except (KeyError, OSError, RuntimeError, TypeError, ValueError):
        raise ValueError(SESSION_WINDOW_LIFECYCLE_SMOKE_ERROR) from None


def _disabled_result() -> LocalSessionWindowLifecycleSmokeResult:
    return {
        "lifecycle_kind": _LIFECYCLE_KIND,
        "status": "disabled",
        "start_decision": "disabled",
        "start_reason": "disabled",
        "start_runtime_record_written": False,
        "stop_decision": "disabled",
        "stop_reason": "disabled",
        "stop_runtime_record_written": False,
        "gate_d_pass_claimed": False,
        "product_promise_alpha_pass_claimed": False,
    }


def _completed_result(
    start: dict[str, object],
    stop: dict[str, object],
) -> LocalSessionWindowLifecycleSmokeResult:
    return {
        "lifecycle_kind": _LIFECYCLE_KIND,
        "status": "completed",
        "start_decision": "executed",
        "start_reason": "start_receipt_written",
        "start_runtime_record_written": start["runtime_record_written"],
        "stop_decision": "executed",
        "stop_reason": "stop_receipt_written",
        "stop_runtime_record_written": stop["runtime_record_written"],
        "gate_d_pass_claimed": False,
        "product_promise_alpha_pass_claimed": False,
    }


def _safe_start_execution(payload: dict[str, object]) -> dict[str, object]:
    if type(payload) is not dict or tuple(payload) != _START_KEYS:
        _fail()
    expected = {
        "execution_kind": "stored_session_window_execution",
        "session_id": _SESSION_ID,
        "source_kind": _SOURCE_KIND,
        "clock_day_of_week": _DAY_OF_WEEK,
        "clock_local_time": _LOCAL_START_TIME,
        "due_count": 1,
        "authorization_status": "authorized",
        "authorized": True,
        "authorized_start_count": 1,
        "runtime_state": "not_started",
        "recovery_review_status": "not_required",
        "preflight_decision": "allow",
        "preflight_reason": "ready_to_execute",
        "runtime_record_written": True,
        "decision": "executed",
        "reason": "start_receipt_written",
    }
    if payload != expected:
        _fail()
    return {key: payload[key] for key in _START_KEYS}


def _safe_stop_execution(payload: dict[str, object]) -> dict[str, object]:
    if type(payload) is not dict or tuple(payload) != _STOP_KEYS:
        _fail()
    expected = {
        "execution_kind": "stored_session_window_stop_execution",
        "session_id": _SESSION_ID,
        "course_id": _COURSE_ID,
        "source_kind": _SOURCE_KIND,
        "selected_class_time_index": _CLASS_TIME_INDEX,
        "scheduled_day_of_week": _DAY_OF_WEEK,
        "scheduled_local_start_time": _LOCAL_START_TIME,
        "stop_after_minutes": _DURATION_MINUTES,
        "runtime_state": "started",
        "start_receipt_count": 1,
        "stop_receipt_count": 0,
        "ready_to_stop": True,
        "confirmation_response": _CONFIRMED,
        "preflight_decision": "allow",
        "preflight_reason": "ready_to_stop",
        "runtime_record_written": True,
        "decision": "executed",
        "reason": "stop_receipt_written",
    }
    if payload != expected:
        _fail()
    return {key: payload[key] for key in _STOP_KEYS}


def _prepare_archive_session_dir(archive_root: str | Path) -> Path:
    archive_root_path = _safe_local_archive_root_path(archive_root)
    session_dir = archive_root_path / _SESSION_ID
    _ensure_candidate_inside(session_dir, archive_root_path)
    try:
        if _is_symlink_or_junction(session_dir):
            _fail()
        if session_dir.exists() and not session_dir.is_dir():
            _fail()
        session_dir.mkdir(exist_ok=True)
        resolved_session_dir = session_dir.resolve(strict=True)
    except (OSError, RuntimeError):
        _fail()
    _ensure_inside(resolved_session_dir, archive_root_path)
    return archive_root_path


def _safe_local_archive_root_path(archive_root: str | Path) -> Path:
    raw_archive_root = _safe_path_text(archive_root)
    archive_root_path = Path(raw_archive_root)
    if not archive_root_path.name:
        _fail()
    try:
        parent = archive_root_path.parent
        if (
            not parent.exists()
            or not parent.is_dir()
            or _is_symlink_or_junction(parent)
        ):
            _fail()
        resolved_parent = parent.resolve(strict=True)
        candidate = resolved_parent / archive_root_path.name
        if _is_symlink_or_junction(archive_root_path):
            _fail()
        if archive_root_path.exists() and not archive_root_path.is_dir():
            _fail()
        archive_root_path.mkdir(exist_ok=True)
        resolved_archive_root = archive_root_path.resolve(strict=True)
    except (OSError, RuntimeError):
        _fail()
    if resolved_archive_root != candidate or not resolved_archive_root.is_dir():
        _fail()
    return resolved_archive_root


def _safe_path_text(path: object) -> str:
    if not isinstance(path, (str, Path)):
        _fail()
    raw_path = str(path)
    if (
        not raw_path
        or raw_path.strip() != raw_path
        or len(raw_path) > _TEXT_MAX_LENGTH
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


def _is_symlink_or_junction(path: Path) -> bool:
    is_junction = getattr(path, "is_junction", None)
    return path.is_symlink() or (is_junction is not None and is_junction())


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
    raise ValueError(SESSION_WINDOW_LIFECYCLE_SMOKE_ERROR)


__all__ = [
    "SESSION_WINDOW_LIFECYCLE_SMOKE_ERROR",
    "LocalSessionWindowLifecycleSmokeResult",
    "build_local_session_window_lifecycle_smoke",
]
