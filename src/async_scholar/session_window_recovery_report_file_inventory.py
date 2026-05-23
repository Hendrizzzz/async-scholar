from __future__ import annotations

import stat
from pathlib import Path
from typing import NoReturn

STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_INVENTORY_ERROR = (
    "stored session window recovery report file inventory could not be built"
)

_REPORT_FILENAME = "stored-session-window-recovery-report.md"
_INVENTORY_KIND = "stored_session_window_recovery_report_file_inventory"


def build_stored_session_window_recovery_report_file_inventory(
    archive_root: str | Path,
    output_root: str | Path,
) -> dict[str, object]:
    try:
        archive_root_path = _existing_directory(archive_root)
        output_root_path = _existing_directory(output_root)
        if _is_relative_to(output_root_path, archive_root_path):
            _fail()

        report_path = output_root_path / _REPORT_FILENAME
        try:
            report_stat = report_path.lstat()
        except FileNotFoundError:
            return {
                "inventory_kind": _INVENTORY_KIND,
                "relative_path": _REPORT_FILENAME,
                "exists": False,
                "size_bytes": 0,
            }
        if stat.S_ISLNK(report_stat.st_mode) or not stat.S_ISREG(report_stat.st_mode):
            _fail()
        resolved_report_path = report_path.resolve(strict=True)
        if not _is_relative_to(
            resolved_report_path, output_root_path
        ) or _is_relative_to(
            resolved_report_path,
            archive_root_path,
        ):
            _fail()
        return {
            "inventory_kind": _INVENTORY_KIND,
            "relative_path": _REPORT_FILENAME,
            "exists": True,
            "size_bytes": report_stat.st_size,
        }
    except Exception:
        raise ValueError(
            STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_INVENTORY_ERROR
        ) from None


def _existing_directory(root: str | Path) -> Path:
    if not isinstance(root, (str, Path)):
        _fail()
    raw_root_text = str(root)
    if (
        not raw_root_text
        or raw_root_text.strip() != raw_root_text
        or _has_control_character(raw_root_text)
        or _has_forbidden_uri_or_unc(raw_root_text)
        or _has_traversal_part(raw_root_text)
    ):
        _fail()
    raw_root = Path(root)
    if raw_root.is_symlink():
        _fail()
    root_path = raw_root.resolve(strict=True)
    if not root_path.is_dir():
        _fail()
    return root_path


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


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
    raise ValueError(STORED_SESSION_WINDOW_RECOVERY_REPORT_FILE_INVENTORY_ERROR)
