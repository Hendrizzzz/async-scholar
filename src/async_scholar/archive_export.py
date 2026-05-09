from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from enum import StrEnum
from types import MappingProxyType

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
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


def archive_export_manifest_to_json_ready(
    manifest: ArchiveExportManifest,
) -> dict[str, object]:
    return manifest.to_json_ready()


def archive_export_manifest_safe_summary(
    manifest: ArchiveExportManifest,
) -> dict[str, object]:
    return manifest.safe_summary()
