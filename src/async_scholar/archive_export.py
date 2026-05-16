from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
)


class ArchiveArtifactKind(StrEnum):
    TRANSCRIPT_JSONL = "transcript_jsonl"
    TRANSCRIPT_MARKDOWN = "transcript_markdown"
    EVENTS_JSONL = "events_jsonl"
    ALERTS_LOG = "alerts_log"
    REVIEWER_MARKDOWN = "reviewer_markdown"
    RUNTIME_LOG = "runtime_log"
    BENCHMARK_REPORT = "benchmark_report"


_SAFE_SESSION_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")

_ARCHIVE_ARTIFACT_FILENAMES = {
    ArchiveArtifactKind.TRANSCRIPT_JSONL: "transcript.jsonl",
    ArchiveArtifactKind.TRANSCRIPT_MARKDOWN: "transcript.md",
    ArchiveArtifactKind.EVENTS_JSONL: "events.jsonl",
    ArchiveArtifactKind.ALERTS_LOG: "alerts.log",
    ArchiveArtifactKind.REVIEWER_MARKDOWN: "reviewer.md",
    ArchiveArtifactKind.RUNTIME_LOG: "runtime.jsonl",
    ArchiveArtifactKind.BENCHMARK_REPORT: "benchmark-report.json",
}

ARCHIVE_ARTIFACT_FILENAMES_BY_KIND = MappingProxyType(_ARCHIVE_ARTIFACT_FILENAMES)
ALLOWED_ARCHIVE_ARTIFACT_FILENAMES = tuple(_ARCHIVE_ARTIFACT_FILENAMES.values())
_ARCHIVE_ARTIFACT_KINDS_BY_FILENAME = {
    filename: kind for kind, filename in _ARCHIVE_ARTIFACT_FILENAMES.items()
}
_WINDOWS_RESERVED_SESSION_NAMES = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{index}" for index in range(1, 10)),
        *(f"LPT{index}" for index in range(1, 10)),
    }
)


def _contains_control_character(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _validate_safe_session_id(value: str) -> str:
    if value != value.strip() or not value.strip():
        raise ValueError("session_id must be a nonblank safe identifier")
    if _contains_control_character(value):
        raise ValueError("session_id must not contain control characters")
    if ".." in value:
        raise ValueError("session_id must not contain traversal markers")
    if not _SAFE_SESSION_ID_PATTERN.fullmatch(value):
        raise ValueError(
            "session_id must contain only letters, numbers, dots, underscores, "
            "and hyphens",
        )
    return value


def _validate_safe_session_directory_name(value: str) -> str:
    safe_value = _validate_safe_session_id(value)
    reserved_candidate = safe_value.split(".", maxsplit=1)[0].upper()
    if reserved_candidate in _WINDOWS_RESERVED_SESSION_NAMES:
        raise ValueError("session_id must not use a reserved device name")
    return safe_value


def _validate_safe_filename(value: str) -> str:
    if value != value.strip() or not value.strip():
        raise ValueError("filename must be a nonblank safe base filename")
    if _contains_control_character(value):
        raise ValueError("filename must not contain control characters")
    if "/" in value or "\\" in value:
        raise ValueError("filename must not contain separators")
    if ":" in value or "://" in value:
        raise ValueError("filename must not contain URL or drive syntax")
    if value in {".", ".."} or ".." in value:
        raise ValueError("filename must not contain traversal markers")
    if value not in _ARCHIVE_ARTIFACT_KINDS_BY_FILENAME:
        raise ValueError("filename is not an allowed archive artifact")
    return value


class ArchiveArtifactEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: ArchiveArtifactKind
    filename: StrictStr

    @field_validator("filename")
    @classmethod
    def _filename_is_safe(cls, value: str) -> str:
        return _validate_safe_filename(value)

    @model_validator(mode="after")
    def _filename_matches_kind(self) -> ArchiveArtifactEntry:
        expected_filename = ARCHIVE_ARTIFACT_FILENAMES_BY_KIND[self.kind]
        if self.filename != expected_filename:
            raise ValueError("archive artifact kind and filename do not match")
        return self

    def to_json_ready(self) -> dict[str, str]:
        return {"kind": self.kind.value, "filename": self.filename}


class ArchiveExportManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    session_id: StrictStr
    artifacts: tuple[ArchiveArtifactEntry, ...] = Field(min_length=1)

    @field_validator("session_id")
    @classmethod
    def _session_id_is_safe(cls, value: str) -> str:
        return _validate_safe_session_id(value)

    @model_validator(mode="after")
    def _artifact_entries_are_unique(self) -> ArchiveExportManifest:
        seen_kinds: set[ArchiveArtifactKind] = set()
        seen_filenames: set[str] = set()
        for artifact in self.artifacts:
            if artifact.kind in seen_kinds or artifact.filename in seen_filenames:
                raise ValueError("archive artifact entries must be unique")
            seen_kinds.add(artifact.kind)
            seen_filenames.add(artifact.filename)
        return self

    def to_json_ready(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "artifacts": [artifact.to_json_ready() for artifact in self.artifacts],
        }

    def safe_export(self) -> dict[str, object]:
        return self.to_json_ready()

    def safe_summary(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "artifact_count": len(self.artifacts),
            "artifacts": [artifact.to_json_ready() for artifact in self.artifacts],
        }


class ArchiveInventoryArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: ArchiveArtifactKind
    filename: StrictStr
    relative_path: StrictStr
    exists: StrictBool
    size_bytes: StrictInt | None = None

    @field_validator("filename", "relative_path")
    @classmethod
    def _artifact_path_is_safe(cls, value: str) -> str:
        return _validate_safe_filename(value)

    @field_validator("size_bytes")
    @classmethod
    def _size_is_non_negative(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("size_bytes must be non-negative")
        return value

    @model_validator(mode="after")
    def _metadata_is_consistent(self) -> ArchiveInventoryArtifact:
        expected_filename = ARCHIVE_ARTIFACT_FILENAMES_BY_KIND[self.kind]
        if self.filename != expected_filename:
            raise ValueError("archive artifact kind and filename do not match")
        if self.relative_path != self.filename:
            raise ValueError("relative_path must stay within the session directory")
        if self.exists and self.size_bytes is None:
            raise ValueError("existing artifacts must include size_bytes")
        if not self.exists and self.size_bytes is not None:
            raise ValueError("missing artifacts must not include size_bytes")
        return self

    def to_json_ready(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "kind": self.kind.value,
            "filename": self.filename,
            "relative_path": self.relative_path,
            "exists": self.exists,
        }
        if self.size_bytes is not None:
            payload["size_bytes"] = self.size_bytes
        return payload


class ArchiveSessionInventory(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    session_id: StrictStr
    session_dir: StrictStr
    artifacts: tuple[ArchiveInventoryArtifact, ...] = Field(min_length=1)

    @field_validator("session_id", "session_dir")
    @classmethod
    def _session_directory_is_safe(cls, value: str) -> str:
        return _validate_safe_session_directory_name(value)

    @model_validator(mode="after")
    def _session_directory_matches_session_id(self) -> ArchiveSessionInventory:
        if self.session_dir != self.session_id:
            raise ValueError("session_dir must match the safe session_id")
        expected_kinds = tuple(ARCHIVE_ARTIFACT_FILENAMES_BY_KIND)
        artifact_kinds = tuple(artifact.kind for artifact in self.artifacts)
        if artifact_kinds != expected_kinds:
            raise ValueError("inventory artifacts must match the archive allowlist")
        return self

    def to_json_ready(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "session_dir": self.session_dir,
            "artifacts": [artifact.to_json_ready() for artifact in self.artifacts],
        }

    def safe_summary(self) -> dict[str, object]:
        existing_artifacts = [
            artifact.to_json_ready() for artifact in self.artifacts if artifact.exists
        ]
        return {
            "session_id": self.session_id,
            "session_dir": self.session_dir,
            "artifact_count": len(self.artifacts),
            "existing_artifact_count": len(existing_artifacts),
            "artifacts": [artifact.to_json_ready() for artifact in self.artifacts],
        }


def _artifact_entry_from_filename(filename: str) -> ArchiveArtifactEntry:
    if not isinstance(filename, str):
        raise TypeError("archive artifact filenames must be strings")
    safe_filename = _validate_safe_filename(filename)
    return ArchiveArtifactEntry(
        kind=_ARCHIVE_ARTIFACT_KINDS_BY_FILENAME[safe_filename],
        filename=safe_filename,
    )


def build_archive_export_manifest(
    session_id: str,
    artifact_filenames: Iterable[str],
) -> ArchiveExportManifest:
    if isinstance(artifact_filenames, (str, bytes, Mapping)):
        raise TypeError("artifact_filenames must be an iterable of filename strings")
    return ArchiveExportManifest(
        session_id=session_id,
        artifacts=tuple(
            _artifact_entry_from_filename(filename) for filename in artifact_filenames
        ),
    )


def _resolve_archive_root(archive_root: str | Path) -> Path:
    if isinstance(archive_root, str) and archive_root != archive_root.strip():
        raise ValueError("archive_root must be an explicit nonblank path")
    if isinstance(archive_root, str) and not archive_root:
        raise ValueError("archive_root must be an explicit nonblank path")
    candidate_root = Path(archive_root)
    resolved_root = candidate_root.resolve(strict=False)
    if candidate_root.exists() and not candidate_root.is_dir():
        raise ValueError("archive_root must be a directory")
    return resolved_root


def _path_is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _require_path_inside(path: Path, root: Path, message: str) -> None:
    if not _path_is_relative_to(path, root):
        raise ValueError(message)


def _resolve_session_archive_dir_from_root(
    resolved_archive_root: Path,
    session_id: str,
) -> Path:
    safe_session_id = _validate_safe_session_directory_name(session_id)
    resolved_session_dir = (resolved_archive_root / safe_session_id).resolve(
        strict=False
    )
    _require_path_inside(
        resolved_session_dir,
        resolved_archive_root,
        "session archive directory must stay inside the archive root",
    )
    return resolved_session_dir


def resolve_session_archive_dir(archive_root: str | Path, session_id: str) -> Path:
    resolved_archive_root = _resolve_archive_root(archive_root)
    return _resolve_session_archive_dir_from_root(resolved_archive_root, session_id)


def _inventory_artifact_from_path(
    *,
    resolved_archive_root: Path,
    resolved_session_dir: Path,
    kind: ArchiveArtifactKind,
    filename: str,
) -> ArchiveInventoryArtifact:
    artifact_path = resolved_session_dir / filename
    resolved_artifact_path = artifact_path.resolve(strict=False)
    _require_path_inside(
        resolved_artifact_path,
        resolved_archive_root,
        "archive artifact path must stay inside the archive root",
    )
    _require_path_inside(
        resolved_artifact_path,
        resolved_session_dir,
        "archive artifact path must stay inside the session directory",
    )

    if not artifact_path.is_file():
        return ArchiveInventoryArtifact(
            kind=kind,
            filename=filename,
            relative_path=filename,
            exists=False,
        )

    _require_path_inside(
        artifact_path.resolve(strict=False),
        resolved_session_dir,
        "archive artifact path must stay inside the session directory",
    )
    return ArchiveInventoryArtifact(
        kind=kind,
        filename=filename,
        relative_path=filename,
        exists=True,
        size_bytes=artifact_path.stat().st_size,
    )


def build_archive_session_inventory(
    archive_root: str | Path,
    session_id: str,
) -> ArchiveSessionInventory:
    safe_session_id = _validate_safe_session_directory_name(session_id)
    resolved_archive_root = _resolve_archive_root(archive_root)
    resolved_session_dir = _resolve_session_archive_dir_from_root(
        resolved_archive_root,
        safe_session_id,
    )

    return ArchiveSessionInventory(
        session_id=safe_session_id,
        session_dir=safe_session_id,
        artifacts=tuple(
            _inventory_artifact_from_path(
                resolved_archive_root=resolved_archive_root,
                resolved_session_dir=resolved_session_dir,
                kind=kind,
                filename=filename,
            )
            for kind, filename in ARCHIVE_ARTIFACT_FILENAMES_BY_KIND.items()
        ),
    )


def archive_export_manifest_to_json_ready(
    manifest: ArchiveExportManifest,
) -> dict[str, object]:
    return manifest.to_json_ready()


def archive_export_manifest_safe_summary(
    manifest: ArchiveExportManifest,
) -> dict[str, object]:
    return manifest.safe_summary()


def archive_session_inventory_to_json_ready(
    inventory: ArchiveSessionInventory,
) -> dict[str, object]:
    return inventory.to_json_ready()


def archive_session_inventory_safe_summary(
    inventory: ArchiveSessionInventory,
) -> dict[str, object]:
    return inventory.safe_summary()
