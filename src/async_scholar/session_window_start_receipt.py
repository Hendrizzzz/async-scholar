from __future__ import annotations

import json
from pathlib import Path

from async_scholar.session_window_start_authorization import (
    session_window_start_authorization_safe_summary,
)

STORED_SESSION_WINDOW_START_RECEIPT_ERROR = (
    "stored session window start receipt could not be built"
)

_RECEIPT_KIND = "stored_session_window_start_receipt"
_RUNTIME_FILENAME = "runtime.jsonl"


def write_stored_session_window_start_receipt(
    authorization_summary: dict[str, object],
    archive_root: Path,
) -> dict[str, object]:
    safe_authorization = _revalidated_authorization_summary(authorization_summary)
    receipt = _build_receipt_summary(
        safe_authorization,
        runtime_record_written=False,
    )
    if not _requires_runtime_record(safe_authorization):
        return receipt

    archive_root_path = _existing_safe_archive_root(archive_root)
    session_id = _safe_session_id(safe_authorization["session_id"])
    session_dir = _safe_session_dir(archive_root_path, session_id)
    runtime_path = _safe_runtime_path(archive_root_path, session_dir)
    receipt["runtime_record_written"] = True

    try:
        with runtime_path.open("a", encoding="utf-8") as runtime_file:
            runtime_file.write(_compact_json_line(receipt))
    except OSError as exc:
        raise ValueError(STORED_SESSION_WINDOW_START_RECEIPT_ERROR) from exc

    return receipt


def _revalidated_authorization_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    try:
        return session_window_start_authorization_safe_summary(payload)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(STORED_SESSION_WINDOW_START_RECEIPT_ERROR) from exc


def _build_receipt_summary(
    authorization_summary: dict[str, object],
    *,
    runtime_record_written: bool,
) -> dict[str, object]:
    return {
        "receipt_kind": _RECEIPT_KIND,
        "status": authorization_summary["status"],
        "session_id": authorization_summary["session_id"],
        "source_kind": authorization_summary["source_kind"],
        "clock_day_of_week": authorization_summary["clock_day_of_week"],
        "clock_local_time": authorization_summary["clock_local_time"],
        "course_count": authorization_summary["course_count"],
        "due_count": authorization_summary["due_count"],
        "ready_to_start": authorization_summary["ready_to_start"],
        "confirmation_required": authorization_summary["confirmation_required"],
        "confirmation_status": authorization_summary["confirmation_status"],
        "confirmation_response": authorization_summary["confirmation_response"],
        "confirmation_verified": authorization_summary["confirmation_verified"],
        "authorized": authorization_summary["authorized"],
        "authorized_start_count": authorization_summary["authorized_start_count"],
        "blocked_start_count": authorization_summary["blocked_start_count"],
        "block_reason": authorization_summary["block_reason"],
        "runtime_record_written": runtime_record_written,
    }


def _requires_runtime_record(authorization_summary: dict[str, object]) -> bool:
    status = authorization_summary["status"]
    authorized = authorization_summary["authorized"]
    if status == "authorized" or authorized is True:
        if _is_exactly_authorized(authorization_summary):
            return True
        raise ValueError(STORED_SESSION_WINDOW_START_RECEIPT_ERROR)
    return False


def _is_exactly_authorized(authorization_summary: dict[str, object]) -> bool:
    due_count = authorization_summary["due_count"]
    return (
        authorization_summary["status"] == "authorized"
        and authorization_summary["authorized"] is True
        and authorization_summary["confirmation_response"] == "confirmed"
        and authorization_summary["confirmation_verified"] is True
        and authorization_summary["confirmation_required"] is True
        and authorization_summary["confirmation_status"] == "required"
        and authorization_summary["ready_to_start"] is True
        and isinstance(due_count, int)
        and not isinstance(due_count, bool)
        and due_count > 0
        and authorization_summary["authorized_start_count"] == due_count
        and authorization_summary["blocked_start_count"] == 0
        and authorization_summary["block_reason"] == "none"
    )


def _existing_safe_archive_root(archive_root: Path) -> Path:
    raw_archive_root = _safe_path_text(archive_root)
    archive_root_path = Path(raw_archive_root)
    try:
        if (
            archive_root_path.is_symlink()
            or not archive_root_path.exists()
            or not archive_root_path.is_dir()
        ):
            raise ValueError(STORED_SESSION_WINDOW_START_RECEIPT_ERROR)
        archive_root_resolved = archive_root_path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(STORED_SESSION_WINDOW_START_RECEIPT_ERROR) from exc
    if not archive_root_resolved.is_dir():
        raise ValueError(STORED_SESSION_WINDOW_START_RECEIPT_ERROR)
    return archive_root_resolved


def _safe_session_id(session_id: object) -> str:
    if not isinstance(session_id, str):
        raise ValueError(STORED_SESSION_WINDOW_START_RECEIPT_ERROR)
    if (
        not session_id
        or _has_control_character(session_id)
        or session_id in {".", ".."}
        or "/" in session_id
        or "\\" in session_id
        or ":" in session_id
        or _has_traversal_part(session_id)
    ):
        raise ValueError(STORED_SESSION_WINDOW_START_RECEIPT_ERROR)
    return session_id


def _safe_session_dir(archive_root: Path, session_id: str) -> Path:
    session_dir = archive_root / session_id
    _ensure_candidate_inside(session_dir, archive_root)
    try:
        if session_dir.is_symlink():
            raise ValueError(STORED_SESSION_WINDOW_START_RECEIPT_ERROR)
        if session_dir.exists():
            if not session_dir.is_dir():
                raise ValueError(STORED_SESSION_WINDOW_START_RECEIPT_ERROR)
        else:
            session_dir.mkdir(parents=False)
        if session_dir.is_symlink() or not session_dir.is_dir():
            raise ValueError(STORED_SESSION_WINDOW_START_RECEIPT_ERROR)
        session_dir_resolved = session_dir.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(STORED_SESSION_WINDOW_START_RECEIPT_ERROR) from exc
    _ensure_inside(session_dir_resolved, archive_root)
    return session_dir_resolved


def _safe_runtime_path(archive_root: Path, session_dir: Path) -> Path:
    runtime_path = session_dir / _RUNTIME_FILENAME
    _ensure_candidate_inside(runtime_path, session_dir)
    _ensure_candidate_inside(runtime_path, archive_root)
    try:
        if runtime_path.is_symlink():
            raise ValueError(STORED_SESSION_WINDOW_START_RECEIPT_ERROR)
        if runtime_path.exists():
            if not runtime_path.is_file():
                raise ValueError(STORED_SESSION_WINDOW_START_RECEIPT_ERROR)
            runtime_resolved = runtime_path.resolve(strict=True)
            _ensure_inside(runtime_resolved, session_dir)
            _ensure_inside(runtime_resolved, archive_root)
    except (OSError, RuntimeError) as exc:
        raise ValueError(STORED_SESSION_WINDOW_START_RECEIPT_ERROR) from exc
    return runtime_path


def _safe_path_text(path: object) -> str:
    if not isinstance(path, (str, Path)):
        raise ValueError(STORED_SESSION_WINDOW_START_RECEIPT_ERROR)
    raw_path = str(path)
    normalized_path = raw_path.replace("/", "\\")
    lower_path = raw_path.lower()
    if (
        not raw_path.strip()
        or _has_control_character(raw_path)
        or "://" in lower_path
        or lower_path.startswith("file:")
        or normalized_path.startswith("\\\\")
        or _has_traversal_part(raw_path)
    ):
        raise ValueError(STORED_SESSION_WINDOW_START_RECEIPT_ERROR)
    return raw_path


def _has_control_character(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _has_traversal_part(value: str) -> bool:
    return any(part == ".." for part in value.replace("\\", "/").split("/"))


def _ensure_candidate_inside(path: Path, parent: Path) -> None:
    try:
        candidate_parent = path.parent.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(STORED_SESSION_WINDOW_START_RECEIPT_ERROR) from exc
    _ensure_inside(candidate_parent / path.name, parent)


def _ensure_inside(path: Path, parent: Path) -> None:
    try:
        path.relative_to(parent)
    except ValueError as exc:
        raise ValueError(STORED_SESSION_WINDOW_START_RECEIPT_ERROR) from exc


def _compact_json_line(payload: dict[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
