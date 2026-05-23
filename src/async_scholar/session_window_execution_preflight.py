"""Read-only one-shot stored session-window execution preflight."""

from __future__ import annotations

import re
import stat
from pathlib import Path
from typing import NoReturn

from async_scholar.archive_export import ARCHIVE_ARTIFACT_FILENAMES_BY_KIND
from async_scholar.schedule_store import list_course_schedule_session_window_inputs
from async_scholar.scheduled_start import ScheduledStartClock
from async_scholar.session_window_confirmation_preflight import (
    build_session_window_confirmation_preflight_summary,
)
from async_scholar.session_window_confirmation_response import (
    build_session_window_confirmation_response_summary,
)
from async_scholar.session_window_recovery_review import (
    build_stored_session_window_recovery_review,
)
from async_scholar.session_window_runtime_summary import (
    build_stored_session_window_runtime_summary,
)
from async_scholar.session_window_start_authorization import (
    build_session_window_start_authorization_summary,
    session_window_start_authorization_safe_summary,
)

STORED_SESSION_WINDOW_EXECUTION_PREFLIGHT_ERROR = (
    "stored session window execution preflight could not be built"
)

StoredSessionWindowExecutionPreflight = dict[str, object]

_PREFLIGHT_KIND = "stored_session_window_execution_preflight"
_RUNTIME_FILENAME = "runtime.jsonl"
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
_CONFIRMATION_STATUSES = frozenset(("required", "not_required", "disabled"))
_CONFIRMATION_RESPONSES = frozenset(("confirmed", "declined"))
_RUNTIME_STATES = frozenset(("not_started", "started", "stopped", "inconsistent"))
_REVIEW_STATUSES = frozenset(("not_required", "required"))
_DECISIONS = frozenset(("allow", "block"))
_REASONS = frozenset(
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
_RECOVERY_REVIEW_KEYS = (
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
_NON_RUNTIME_ARTIFACT_FILENAMES = tuple(
    filename
    for filename in ARCHIVE_ARTIFACT_FILENAMES_BY_KIND.values()
    if filename != _RUNTIME_FILENAME
)


def build_stored_session_window_execution_preflight_from_store(
    db_path: str | Path,
    archive_root: str | Path,
    session_id: str,
    source_kind: str,
    clock: ScheduledStartClock,
    confirmation_response: str,
    *,
    enabled: bool = True,
) -> StoredSessionWindowExecutionPreflight:
    """Build metadata-only readiness for a future explicit one-shot execution."""

    try:
        safe_session_id = _safe_session_id(session_id)
        safe_archive_root = _existing_safe_archive_root(archive_root)
        safe_session_dir = _existing_safe_session_dir(
            safe_archive_root,
            safe_session_id,
        )
        preflight_summary = build_session_window_confirmation_preflight_summary(
            list_course_schedule_session_window_inputs(db_path),
            safe_archive_root,
            safe_session_id,
            source_kind,
            clock,
            enabled=enabled,
        )
        response_summary = build_session_window_confirmation_response_summary(
            preflight_summary,
            confirmation_response,
        )
        authorization = _authorization_safe_summary(
            build_session_window_start_authorization_summary(response_summary),
            expected_context=_expected_authorization_context(response_summary),
        )
        runtime_state, recovery_review_status = _runtime_and_recovery_status(
            safe_archive_root,
            safe_session_dir,
            safe_session_id,
        )
        return _execution_preflight_safe_summary(
            _build_decision_payload(
                authorization,
                runtime_state,
                recovery_review_status,
            )
        )
    except (KeyError, OSError, RuntimeError, TypeError, ValueError):
        raise ValueError(STORED_SESSION_WINDOW_EXECUTION_PREFLIGHT_ERROR) from None


def _build_decision_payload(
    authorization: dict[str, object],
    runtime_state: str,
    recovery_review_status: str,
) -> dict[str, object]:
    due_count = _non_negative_int(authorization["due_count"])
    authorization_status = _authorization_status(authorization["status"])
    authorized = _bool_value(authorization["authorized"])
    authorized_start_count = _non_negative_int(authorization["authorized_start_count"])

    if due_count == 0:
        ready_to_execute = False
        decision = "block"
        reason = "no_due_session"
    elif authorization_status == "blocked":
        ready_to_execute = False
        decision = "block"
        reason = "confirmation_declined"
    elif not authorized or authorization_status != "authorized":
        ready_to_execute = False
        decision = "block"
        reason = "authorization_not_granted"
    elif runtime_state == "started":
        ready_to_execute = False
        decision = "block"
        reason = "partial_runtime"
    elif runtime_state in ("stopped", "inconsistent"):
        ready_to_execute = False
        decision = "block"
        reason = "existing_conflicting_receipt"
    elif recovery_review_status == "required":
        ready_to_execute = False
        decision = "block"
        reason = "recovery_review_required"
    else:
        ready_to_execute = True
        decision = "allow"
        reason = "ready_to_execute"

    return {
        "preflight_kind": _PREFLIGHT_KIND,
        "session_id": authorization["session_id"],
        "source_kind": authorization["source_kind"],
        "clock_day_of_week": authorization["clock_day_of_week"],
        "clock_local_time": authorization["clock_local_time"],
        "due_count": due_count,
        "authorization_status": authorization_status,
        "authorized": authorized,
        "authorized_start_count": authorized_start_count,
        "runtime_state": runtime_state,
        "recovery_review_status": recovery_review_status,
        "ready_to_execute": ready_to_execute,
        "decision": decision,
        "reason": reason,
    }


def _runtime_and_recovery_status(
    archive_root: Path,
    session_dir: Path,
    session_id: str,
) -> tuple[str, str]:
    runtime_path = session_dir / _RUNTIME_FILENAME
    _ensure_candidate_inside(runtime_path, session_dir)
    _ensure_candidate_inside(runtime_path, archive_root)
    try:
        if (
            runtime_path.is_symlink()
            or runtime_path.exists()
            and (
                not runtime_path.is_file()
                or not stat.S_ISREG(runtime_path.stat().st_mode)
            )
        ):
            _fail()
    except OSError:
        _fail()

    if not runtime_path.exists():
        return "not_started", _missing_runtime_recovery_review_status(session_dir)

    runtime = _runtime_summary_safe_summary(
        build_stored_session_window_runtime_summary(archive_root, session_id)
    )
    runtime_state = _runtime_state(runtime["lifecycle_status"])
    recovery_review = _recovery_review_safe_summary(
        build_stored_session_window_recovery_review(archive_root, session_id)
    )
    if recovery_review["runtime_lifecycle_status"] != runtime_state:
        _fail()
    return runtime_state, _recovery_review_status(recovery_review["review_status"])


def _missing_runtime_recovery_review_status(session_dir: Path) -> str:
    for filename in _NON_RUNTIME_ARTIFACT_FILENAMES:
        artifact_path = session_dir / filename
        _ensure_candidate_inside(artifact_path, session_dir)
        try:
            if artifact_path.is_symlink():
                _fail()
            if artifact_path.exists():
                if not artifact_path.is_file() or not stat.S_ISREG(
                    artifact_path.stat().st_mode
                ):
                    _fail()
                return "required"
        except OSError:
            _fail()
    return "not_required"


def _expected_authorization_context(
    response_summary: dict[str, object],
) -> dict[str, object]:
    return {
        "session_id": _safe_session_id(response_summary["session_id"]),
        "source_kind": _source_kind(response_summary["source_kind"]),
        "clock_day_of_week": _day_of_week(response_summary["clock_day_of_week"]),
        "clock_local_time": _local_time(response_summary["clock_local_time"]),
        "course_count": _non_negative_int(response_summary["course_count"]),
        "due_count": _non_negative_int(response_summary["due_count"]),
        "ready_to_start": _bool_value(response_summary["ready_to_start"]),
        "confirmation_required": _bool_value(response_summary["confirmation_required"]),
        "confirmation_status": _confirmation_status(
            response_summary["confirmation_status"]
        ),
        "confirmation_response": _confirmation_response(
            response_summary["confirmation_response"]
        ),
        "confirmation_verified": _bool_value(response_summary["confirmation_verified"]),
    }


def _authorization_safe_summary(
    payload: dict[str, object],
    *,
    expected_context: dict[str, object],
) -> dict[str, object]:
    if type(payload) is not dict or tuple(payload) != _AUTHORIZATION_KEYS:
        _fail()
    try:
        safe_payload = session_window_start_authorization_safe_summary(payload)
    except (KeyError, TypeError, ValueError):
        _fail()
    if type(safe_payload) is not dict or tuple(safe_payload) != _AUTHORIZATION_KEYS:
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
    safe_payload["confirmation_status"] = _confirmation_status(
        safe_payload["confirmation_status"]
    )
    safe_payload["confirmation_response"] = _confirmation_response(
        safe_payload["confirmation_response"]
    )
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
    if (
        safe_payload["session_id"] != expected_context["session_id"]
        or safe_payload["source_kind"] != expected_context["source_kind"]
        or safe_payload["clock_day_of_week"] != expected_context["clock_day_of_week"]
        or safe_payload["clock_local_time"] != expected_context["clock_local_time"]
        or safe_payload["course_count"] != expected_context["course_count"]
        or safe_payload["due_count"] != expected_context["due_count"]
        or safe_payload["ready_to_start"] != expected_context["ready_to_start"]
        or safe_payload["confirmation_required"]
        != expected_context["confirmation_required"]
        or safe_payload["confirmation_status"]
        != expected_context["confirmation_status"]
        or safe_payload["confirmation_response"]
        != expected_context["confirmation_response"]
        or safe_payload["confirmation_verified"]
        != expected_context["confirmation_verified"]
    ):
        _fail()
    if safe_payload["status"] == "authorized" and (
        safe_payload["authorized"] is not True
        or safe_payload["authorized_start_count"] != safe_payload["due_count"]
        or safe_payload["blocked_start_count"] != 0
    ):
        _fail()
    return safe_payload


def _runtime_summary_safe_summary(payload: dict[str, object]) -> dict[str, object]:
    if type(payload) is not dict or tuple(payload) != _RUNTIME_SUMMARY_KEYS:
        _fail()
    safe_payload = {key: payload[key] for key in _RUNTIME_SUMMARY_KEYS}
    if _exact_text(safe_payload["summary_kind"]) != (
        "stored_session_window_runtime_summary"
    ):
        _fail()
    safe_payload["session_id"] = _safe_session_id(safe_payload["session_id"])
    safe_payload["runtime_record_count"] = _non_negative_int(
        safe_payload["runtime_record_count"]
    )
    safe_payload["start_receipt_count"] = _non_negative_int(
        safe_payload["start_receipt_count"]
    )
    safe_payload["stop_receipt_count"] = _non_negative_int(
        safe_payload["stop_receipt_count"]
    )
    safe_payload["lifecycle_status"] = _runtime_state(safe_payload["lifecycle_status"])
    safe_payload["session_active"] = _bool_value(safe_payload["session_active"])
    safe_payload["session_stopped"] = _bool_value(safe_payload["session_stopped"])
    _exact_text(safe_payload["last_receipt_kind"])
    _exact_text(safe_payload["last_source_kind"])
    return safe_payload


def _recovery_review_safe_summary(payload: dict[str, object]) -> dict[str, object]:
    if type(payload) is not dict or tuple(payload) != _RECOVERY_REVIEW_KEYS:
        _fail()
    safe_payload = {key: payload[key] for key in _RECOVERY_REVIEW_KEYS}
    if _exact_text(safe_payload["review_kind"]) != (
        "stored_session_window_recovery_review"
    ):
        _fail()
    safe_payload["session_id"] = _safe_session_id(safe_payload["session_id"])
    safe_payload["runtime_lifecycle_status"] = _runtime_state(
        safe_payload["runtime_lifecycle_status"]
    )
    _exact_text(safe_payload["archive_recovery_status"])
    safe_payload["archive_existing_count"] = _non_negative_int(
        safe_payload["archive_existing_count"]
    )
    safe_payload["archive_missing_count"] = _non_negative_int(
        safe_payload["archive_missing_count"]
    )
    _exact_text(safe_payload["recovery_decision"])
    safe_payload["manual_review_required"] = _bool_value(
        safe_payload["manual_review_required"]
    )
    safe_payload["review_status"] = _recovery_review_status(
        safe_payload["review_status"]
    )
    _exact_text(safe_payload["review_reason"])
    _exact_text(safe_payload["safe_next_review_action"])
    if safe_payload["manual_review_required"] != (
        safe_payload["review_status"] == "required"
    ):
        _fail()
    return safe_payload


def _execution_preflight_safe_summary(
    payload: dict[str, object],
) -> StoredSessionWindowExecutionPreflight:
    if type(payload) is not dict or tuple(payload) != _PREFLIGHT_KEYS:
        _fail()
    safe_payload = {key: payload[key] for key in _PREFLIGHT_KEYS}
    if _exact_text(safe_payload["preflight_kind"]) != _PREFLIGHT_KIND:
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
    safe_payload["decision"] = _decision(safe_payload["decision"])
    safe_payload["reason"] = _reason(safe_payload["reason"])
    return safe_payload


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
    except (OSError, RuntimeError):
        _fail()
    if not archive_root_resolved.is_dir():
        _fail()
    return archive_root_resolved


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
    except (OSError, RuntimeError):
        _fail()
    _ensure_inside(session_dir_resolved, archive_root)
    return session_dir_resolved


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
    session_id = _exact_text(value)
    if (
        session_id in {".", ".."}
        or "/" in session_id
        or "\\" in session_id
        or ":" in session_id
        or _SESSION_ID_PATTERN.fullmatch(session_id) is None
    ):
        _fail()
    return session_id


def _authorization_status(value: object) -> str:
    status = _exact_text(value)
    if status not in _AUTHORIZATION_STATUSES:
        _fail()
    return status


def _confirmation_status(value: object) -> str:
    status = _exact_text(value)
    if status not in _CONFIRMATION_STATUSES:
        _fail()
    return status


def _confirmation_response(value: object) -> str:
    response = _exact_text(value)
    if response not in _CONFIRMATION_RESPONSES:
        _fail()
    return response


def _runtime_state(value: object) -> str:
    runtime_state = _exact_text(value)
    if runtime_state not in _RUNTIME_STATES:
        _fail()
    return runtime_state


def _source_kind(value: object) -> str:
    source_kind = _exact_text(value)
    if source_kind not in _SOURCE_KINDS:
        _fail()
    return source_kind


def _day_of_week(value: object) -> str:
    day_of_week = _exact_text(value)
    if day_of_week not in _DAYS_OF_WEEK:
        _fail()
    return day_of_week


def _local_time(value: object) -> str:
    local_time = _exact_text(value)
    if _LOCAL_TIME_PATTERN.fullmatch(local_time) is None:
        _fail()
    hour_text, minute_text = local_time.split(":")
    if int(hour_text) > 23 or int(minute_text) > 59:
        _fail()
    return local_time


def _recovery_review_status(value: object) -> str:
    review_status = _exact_text(value)
    if review_status not in _REVIEW_STATUSES:
        _fail()
    return review_status


def _decision(value: object) -> str:
    decision = _exact_text(value)
    if decision not in _DECISIONS:
        _fail()
    return decision


def _reason(value: object) -> str:
    reason = _exact_text(value)
    if reason not in _REASONS:
        _fail()
    return reason


def _bool_value(value: object) -> bool:
    if not isinstance(value, bool):
        _fail()
    return value


def _non_negative_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        _fail()
    return value


def _exact_text(value: object) -> str:
    if type(value) is not str:
        _fail()
    if (
        not value
        or value.strip() != value
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
    raise ValueError(STORED_SESSION_WINDOW_EXECUTION_PREFLIGHT_ERROR)
