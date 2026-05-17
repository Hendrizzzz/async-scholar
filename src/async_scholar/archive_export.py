from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    StrictStr,
    ValidationError,
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
ARCHIVE_EXPORT_ARTIFACT_STATUS: Literal["exported"] = "exported"


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


class ArchiveExportPreflightArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: ArchiveArtifactKind
    filename: StrictStr
    exists: StrictBool
    size_bytes: StrictInt | None = None

    @field_validator("filename")
    @classmethod
    def _filename_is_safe(cls, value: str) -> str:
        return _validate_safe_filename(value)

    @field_validator("size_bytes")
    @classmethod
    def _size_is_non_negative(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("size_bytes must be non-negative")
        return value

    @model_validator(mode="after")
    def _metadata_is_consistent(self) -> ArchiveExportPreflightArtifact:
        expected_filename = ARCHIVE_ARTIFACT_FILENAMES_BY_KIND[self.kind]
        if self.filename != expected_filename:
            raise ValueError("archive artifact kind and filename do not match")
        if self.exists and self.size_bytes is None:
            raise ValueError("existing artifacts must include size_bytes")
        if not self.exists and self.size_bytes is not None:
            raise ValueError("missing artifacts must not include size_bytes")
        return self

    def to_json_ready(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "kind": self.kind.value,
            "filename": self.filename,
            "exists": self.exists,
        }
        if self.size_bytes is not None:
            payload["size_bytes"] = self.size_bytes
        return payload


class ArchiveExportPreflightSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    session_id: StrictStr
    session_dir: StrictStr
    existing_count: StrictInt = Field(ge=0)
    missing_count: StrictInt = Field(ge=0)
    total_existing_size_bytes: StrictInt = Field(ge=0)
    artifacts: tuple[ArchiveExportPreflightArtifact, ...] = Field(min_length=1)

    @field_validator("session_id", "session_dir")
    @classmethod
    def _session_directory_is_safe(cls, value: str) -> str:
        return _validate_safe_session_directory_name(value)

    @model_validator(mode="after")
    def _metadata_is_consistent(self) -> ArchiveExportPreflightSummary:
        if self.session_dir != self.session_id:
            raise ValueError("session_dir must match the safe session_id")

        expected_kinds = tuple(ARCHIVE_ARTIFACT_FILENAMES_BY_KIND)
        artifact_kinds = tuple(artifact.kind for artifact in self.artifacts)
        if artifact_kinds != expected_kinds:
            raise ValueError("preflight artifacts must match the archive allowlist")

        existing_count = sum(1 for artifact in self.artifacts if artifact.exists)
        missing_count = len(self.artifacts) - existing_count
        total_existing_size_bytes = sum(
            artifact.size_bytes or 0 for artifact in self.artifacts if artifact.exists
        )

        if self.existing_count != existing_count:
            raise ValueError("existing_count must match artifacts")
        if self.missing_count != missing_count:
            raise ValueError("missing_count must match artifacts")
        if self.total_existing_size_bytes != total_existing_size_bytes:
            raise ValueError("total_existing_size_bytes must match artifacts")
        return self

    def to_json_ready(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "session_dir": self.session_dir,
            "existing_count": self.existing_count,
            "missing_count": self.missing_count,
            "total_existing_size_bytes": self.total_existing_size_bytes,
            "artifacts": [artifact.to_json_ready() for artifact in self.artifacts],
        }

    def safe_summary(self) -> dict[str, object]:
        return self.to_json_ready()


class ArchiveExportedArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: ArchiveArtifactKind
    filename: StrictStr
    size_bytes: StrictInt
    status: Literal["exported"] = ARCHIVE_EXPORT_ARTIFACT_STATUS

    @field_validator("filename")
    @classmethod
    def _filename_is_safe(cls, value: str) -> str:
        return _validate_safe_filename(value)

    @field_validator("size_bytes")
    @classmethod
    def _size_is_non_negative(cls, value: int) -> int:
        if value < 0:
            raise ValueError("size_bytes must be non-negative")
        return value

    @model_validator(mode="after")
    def _metadata_is_consistent(self) -> ArchiveExportedArtifact:
        expected_filename = ARCHIVE_ARTIFACT_FILENAMES_BY_KIND[self.kind]
        if self.filename != expected_filename:
            raise ValueError("archive artifact kind and filename do not match")
        return self

    def to_json_ready(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "filename": self.filename,
            "size_bytes": self.size_bytes,
            "status": self.status,
        }


class ArchiveExportExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    session_id: StrictStr
    session_dir: StrictStr
    export_dir: StrictStr
    artifact_count: StrictInt = Field(ge=1)
    total_exported_size_bytes: StrictInt = Field(ge=0)
    artifacts: tuple[ArchiveExportedArtifact, ...] = Field(min_length=1)

    @field_validator("session_id", "session_dir", "export_dir")
    @classmethod
    def _session_directory_is_safe(cls, value: str) -> str:
        return _validate_safe_session_directory_name(value)

    @model_validator(mode="after")
    def _metadata_is_consistent(self) -> ArchiveExportExecutionResult:
        if self.session_dir != self.session_id:
            raise ValueError("session_dir must match the safe session_id")
        if self.export_dir != self.session_id:
            raise ValueError("export_dir must match the safe session_id")
        if self.artifact_count != len(self.artifacts):
            raise ValueError("artifact_count must match artifacts")
        total_size = sum(artifact.size_bytes for artifact in self.artifacts)
        if self.total_exported_size_bytes != total_size:
            raise ValueError("total_exported_size_bytes must match artifacts")

        seen_kinds: set[ArchiveArtifactKind] = set()
        seen_filenames: set[str] = set()
        expected_order = tuple(ARCHIVE_ARTIFACT_FILENAMES_BY_KIND)
        artifact_kinds = tuple(artifact.kind for artifact in self.artifacts)
        artifact_kind_set = set(artifact_kinds)
        expected_exported_order = tuple(
            kind for kind in expected_order if kind in artifact_kind_set
        )
        if artifact_kinds != expected_exported_order:
            raise ValueError("exported artifacts must preserve archive allowlist order")
        for artifact in self.artifacts:
            if artifact.kind in seen_kinds or artifact.filename in seen_filenames:
                raise ValueError("exported artifacts must be unique")
            seen_kinds.add(artifact.kind)
            seen_filenames.add(artifact.filename)
        return self

    def to_json_ready(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "session_dir": self.session_dir,
            "export_dir": self.export_dir,
            "artifact_count": self.artifact_count,
            "total_exported_size_bytes": self.total_exported_size_bytes,
            "artifacts": [artifact.to_json_ready() for artifact in self.artifacts],
        }

    def safe_summary(self) -> dict[str, object]:
        return self.to_json_ready()


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


def _resolve_existing_export_root(export_root: str | Path) -> Path:
    if isinstance(export_root, str) and export_root != export_root.strip():
        raise ValueError("export_root must be an explicit existing directory")
    if isinstance(export_root, str) and not export_root:
        raise ValueError("export_root must be an explicit existing directory")
    candidate_root = Path(export_root)
    resolved_root = candidate_root.resolve(strict=False)
    if not candidate_root.exists() or not candidate_root.is_dir():
        raise ValueError("export_root must be an explicit existing directory")
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


def _require_path_outside(path: Path, root: Path, message: str) -> None:
    if _path_is_relative_to(path, root):
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


def build_archive_export_manifest_from_inventory(
    inventory: ArchiveSessionInventory,
) -> ArchiveExportManifest:
    if type(inventory) is not ArchiveSessionInventory:
        raise TypeError("inventory must be an ArchiveSessionInventory")

    try:
        revalidated_inventory = ArchiveSessionInventory.model_validate(
            inventory.model_dump(),
        )
    except ValidationError:
        raise ValueError("inventory metadata failed validation") from None

    existing_filenames = [
        artifact.filename
        for artifact in revalidated_inventory.artifacts
        if artifact.exists is True
    ]
    if not existing_filenames:
        raise ValueError("inventory must contain at least one existing artifact")

    return build_archive_export_manifest(
        revalidated_inventory.session_id,
        existing_filenames,
    )


def build_archive_export_manifest_from_root(
    archive_root: str | Path,
    session_id: str,
) -> ArchiveExportManifest:
    try:
        inventory = build_archive_session_inventory(archive_root, session_id)
        return build_archive_export_manifest_from_inventory(inventory)
    except (OSError, RuntimeError, ValueError):
        raise ValueError("archive export manifest could not be built") from None


def build_archive_export_preflight_summary_from_root(
    archive_root: str | Path,
    session_id: str,
) -> ArchiveExportPreflightSummary:
    try:
        inventory = build_archive_session_inventory(archive_root, session_id)
        artifacts = tuple(
            ArchiveExportPreflightArtifact(
                kind=artifact.kind,
                filename=artifact.filename,
                exists=artifact.exists,
                size_bytes=artifact.size_bytes,
            )
            for artifact in inventory.artifacts
        )
        existing_count = sum(1 for artifact in artifacts if artifact.exists)
        return ArchiveExportPreflightSummary(
            session_id=inventory.session_id,
            session_dir=inventory.session_dir,
            existing_count=existing_count,
            missing_count=len(artifacts) - existing_count,
            total_existing_size_bytes=sum(
                artifact.size_bytes or 0 for artifact in artifacts if artifact.exists
            ),
            artifacts=artifacts,
        )
    except (OSError, RuntimeError, TypeError, ValidationError, ValueError):
        raise ValueError(
            "archive export preflight summary could not be built"
        ) from None


def _copy_file_exclusive(source_path: Path, destination_path: Path) -> None:
    with (
        source_path.open("rb") as source_file,
        destination_path.open("xb") as destination_file,
    ):
        while chunk := source_file.read(1024 * 1024):
            destination_file.write(chunk)


def execute_archive_export_to_local_root(
    archive_root: str | Path,
    export_root: str | Path,
    session_id: str,
) -> ArchiveExportExecutionResult:
    try:
        inventory = build_archive_session_inventory(archive_root, session_id)
        manifest = build_archive_export_manifest_from_root(archive_root, session_id)
        preflight = build_archive_export_preflight_summary_from_root(
            archive_root,
            session_id,
        )
        resolved_archive_root = _resolve_archive_root(archive_root)
        resolved_export_root = _resolve_existing_export_root(export_root)
        _require_path_outside(
            resolved_export_root,
            resolved_archive_root,
            "export_root must stay outside the archive root",
        )

        resolved_source_session_dir = _resolve_session_archive_dir_from_root(
            resolved_archive_root,
            inventory.session_id,
        )
        destination_session_dir = resolved_export_root / inventory.session_id
        resolved_destination_session_dir = destination_session_dir.resolve(strict=False)
        _require_path_inside(
            resolved_destination_session_dir,
            resolved_export_root,
            "export session directory must stay inside the export root",
        )
        _require_path_outside(
            resolved_destination_session_dir,
            resolved_archive_root,
            "export session directory must stay outside the archive root",
        )
        if destination_session_dir.exists() and not destination_session_dir.is_dir():
            raise ValueError("export session destination must be a directory")
        if destination_session_dir.is_symlink():
            raise ValueError("export session destination must not be a symlink")

        preflight_artifacts = {
            artifact.filename: artifact for artifact in preflight.artifacts
        }
        export_plan: list[tuple[ArchiveArtifactKind, str, int, Path, Path]] = []
        for artifact in manifest.artifacts:
            preflight_artifact = preflight_artifacts[artifact.filename]
            if (
                preflight_artifact.exists is not True
                or preflight_artifact.size_bytes is None
            ):
                raise ValueError("manifest and preflight metadata disagree")

            source_path = resolved_source_session_dir / artifact.filename
            resolved_source_path = source_path.resolve(strict=False)
            _require_path_inside(
                resolved_source_path,
                resolved_archive_root,
                "source artifact path must stay inside the archive root",
            )
            _require_path_inside(
                resolved_source_path,
                resolved_source_session_dir,
                "source artifact path must stay inside the session directory",
            )
            if not source_path.is_file():
                raise ValueError("source artifact must exist before export")
            source_size = source_path.stat().st_size
            if source_size != preflight_artifact.size_bytes:
                raise ValueError("source artifact size changed before export")

            destination_path = destination_session_dir / artifact.filename
            resolved_destination_path = destination_path.resolve(strict=False)
            _require_path_inside(
                resolved_destination_path,
                resolved_export_root,
                "destination artifact path must stay inside the export root",
            )
            _require_path_outside(
                resolved_destination_path,
                resolved_archive_root,
                "destination artifact path must stay outside the archive root",
            )
            if destination_path.exists() or destination_path.is_symlink():
                raise ValueError("destination artifact must not already exist")
            export_plan.append(
                (
                    artifact.kind,
                    artifact.filename,
                    source_size,
                    source_path,
                    destination_path,
                )
            )

        if not export_plan:
            raise ValueError("archive export must contain existing artifacts")

        destination_session_dir.mkdir(parents=False, exist_ok=True)
        resolved_destination_session_dir = destination_session_dir.resolve(strict=False)
        _require_path_inside(
            resolved_destination_session_dir,
            resolved_export_root,
            "export session directory must stay inside the export root",
        )
        _require_path_outside(
            resolved_destination_session_dir,
            resolved_archive_root,
            "export session directory must stay outside the archive root",
        )

        exported_artifacts: list[ArchiveExportedArtifact] = []
        for kind, filename, size_bytes, source_path, destination_path in export_plan:
            resolved_source_path = source_path.resolve(strict=False)
            resolved_destination_path = destination_path.resolve(strict=False)
            _require_path_inside(
                resolved_source_path,
                resolved_archive_root,
                "source artifact path must stay inside the archive root",
            )
            _require_path_inside(
                resolved_source_path,
                resolved_source_session_dir,
                "source artifact path must stay inside the session directory",
            )
            _require_path_inside(
                resolved_destination_path,
                resolved_export_root,
                "destination artifact path must stay inside the export root",
            )
            _require_path_outside(
                resolved_destination_path,
                resolved_archive_root,
                "destination artifact path must stay outside the archive root",
            )
            if not source_path.is_file() or source_path.stat().st_size != size_bytes:
                raise ValueError("source artifact changed before export")
            if destination_path.exists() or destination_path.is_symlink():
                raise ValueError("destination artifact must not already exist")

            _copy_file_exclusive(source_path, destination_path)
            exported_artifacts.append(
                ArchiveExportedArtifact(
                    kind=kind,
                    filename=filename,
                    size_bytes=size_bytes,
                )
            )

        return ArchiveExportExecutionResult(
            session_id=inventory.session_id,
            session_dir=inventory.session_dir,
            export_dir=inventory.session_id,
            artifact_count=len(exported_artifacts),
            total_exported_size_bytes=sum(
                artifact.size_bytes for artifact in exported_artifacts
            ),
            artifacts=tuple(exported_artifacts),
        )
    except (OSError, RuntimeError, TypeError, ValidationError, ValueError):
        raise ValueError("archive export could not be executed") from None


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


def archive_export_preflight_summary_to_json_ready(
    summary: ArchiveExportPreflightSummary,
) -> dict[str, object]:
    return summary.to_json_ready()


def archive_export_preflight_summary_safe_summary(
    summary: ArchiveExportPreflightSummary,
) -> dict[str, object]:
    return summary.safe_summary()


def archive_export_execution_result_to_json_ready(
    result: ArchiveExportExecutionResult,
) -> dict[str, object]:
    return result.to_json_ready()


def archive_export_execution_result_safe_summary(
    result: ArchiveExportExecutionResult,
) -> dict[str, object]:
    return result.safe_summary()
