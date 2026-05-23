from __future__ import annotations

from pathlib import Path
from typing import NoReturn

from async_scholar.session_recovery import build_crash_recovery_session_preflight
from async_scholar.session_window_runtime_summary import (
    build_stored_session_window_runtime_summary,
)

STORED_SESSION_WINDOW_RECOVERY_DECISION_ERROR = (
    "stored session window recovery decision could not be built"
)

_DECISION_KIND = "stored_session_window_recovery_decision"
_RUNTIME_FILENAME = "runtime.jsonl"
_LIFECYCLE_VALUES = frozenset(("not_started", "started", "stopped", "inconsistent"))


def build_stored_session_window_recovery_decision(
    archive_root: str | Path,
    session_id: str,
) -> dict[str, object]:
    try:
        runtime_summary = build_stored_session_window_runtime_summary(
            archive_root,
            session_id,
        )
        recovery_preflight = build_crash_recovery_session_preflight(
            archive_root,
            session_id,
        ).to_json_ready()
        lifecycle_status = _runtime_lifecycle_status(runtime_summary)
        recovery_status, existing_count, missing_count = _archive_status_counts(
            recovery_preflight,
        )
        decision = _recovery_decision(lifecycle_status, recovery_status)

        return {
            "decision_kind": _DECISION_KIND,
            "session_id": _matching_session_id(runtime_summary, recovery_preflight),
            "runtime_lifecycle_status": lifecycle_status,
            "runtime_record_count": _non_negative_int(
                runtime_summary.get("runtime_record_count")
            ),
            "start_receipt_count": _non_negative_int(
                runtime_summary.get("start_receipt_count")
            ),
            "stop_receipt_count": _non_negative_int(
                runtime_summary.get("stop_receipt_count")
            ),
            "session_active": _bool_value(runtime_summary.get("session_active")),
            "session_stopped": _bool_value(runtime_summary.get("session_stopped")),
            "archive_recovery_status": recovery_status,
            "archive_existing_count": existing_count,
            "archive_missing_count": missing_count,
            "recovery_decision": decision,
            "manual_review_required": decision != "no_action",
        }
    except (KeyError, OSError, RuntimeError, TypeError, ValueError):
        raise ValueError(STORED_SESSION_WINDOW_RECOVERY_DECISION_ERROR) from None


def _runtime_lifecycle_status(runtime_summary: dict[str, object]) -> str:
    lifecycle_status = runtime_summary.get("lifecycle_status")
    if (
        not isinstance(lifecycle_status, str)
        or lifecycle_status not in _LIFECYCLE_VALUES
    ):
        _fail()
    return lifecycle_status


def _matching_session_id(
    runtime_summary: dict[str, object],
    recovery_preflight: dict[str, object],
) -> str:
    runtime_session_id = runtime_summary.get("session_id")
    recovery_session_id = recovery_preflight.get("session_id")
    if (
        not isinstance(runtime_session_id, str)
        or runtime_session_id != recovery_session_id
    ):
        _fail()
    return runtime_session_id


def _archive_status_counts(
    recovery_preflight: dict[str, object],
) -> tuple[str, int, int]:
    artifacts = recovery_preflight.get("artifacts")
    if not isinstance(artifacts, list):
        _fail()

    non_runtime_artifacts = [
        artifact
        for artifact in artifacts
        if _artifact_filename(artifact) != _RUNTIME_FILENAME
    ]
    if not non_runtime_artifacts:
        _fail()

    existing_count = sum(1 for artifact in non_runtime_artifacts if _exists(artifact))
    missing_count = len(non_runtime_artifacts) - existing_count
    if existing_count == 0:
        recovery_status = "empty"
    elif missing_count == 0:
        recovery_status = "complete"
    else:
        recovery_status = "partial"
    return recovery_status, existing_count, missing_count


def _artifact_filename(artifact: object) -> str:
    if not isinstance(artifact, dict):
        _fail()
    filename = artifact.get("filename")
    if not isinstance(filename, str):
        _fail()
    return filename


def _exists(artifact: object) -> bool:
    if not isinstance(artifact, dict):
        _fail()
    exists = artifact.get("exists")
    if not isinstance(exists, bool):
        _fail()
    return exists


def _recovery_decision(lifecycle_status: str, recovery_status: str) -> str:
    if lifecycle_status == "inconsistent":
        return "manual_review"
    if lifecycle_status == "started":
        return "inspect_active_session"
    if lifecycle_status == "stopped" and recovery_status == "complete":
        return "no_action"
    if lifecycle_status == "not_started" and recovery_status == "empty":
        return "no_action"
    return "inspect_partial_archive"


def _non_negative_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        _fail()
    return value


def _bool_value(value: object) -> bool:
    if not isinstance(value, bool):
        _fail()
    return value


def _fail() -> NoReturn:
    raise ValueError(STORED_SESSION_WINDOW_RECOVERY_DECISION_ERROR)
