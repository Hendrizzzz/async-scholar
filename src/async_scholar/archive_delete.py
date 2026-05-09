"""Inert archive deletion plan models."""

import re
from enum import StrEnum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictStr,
    field_validator,
    model_validator,
)

from async_scholar.archive_export import (
    ArchiveArtifactKind,
    ArchiveExportManifest,
)


class ArchiveDeleteIntent(StrEnum):
    """Controlled archive deletion intent labels."""

    ARCHIVE_ARTIFACT_CANDIDATES = "archive_artifact_candidates"


_SAFE_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SAFE_ARTIFACT_FILENAMES: dict[str, ArchiveArtifactKind] = {
    "transcript.jsonl": ArchiveArtifactKind.TRANSCRIPT_JSONL,
    "transcript.md": ArchiveArtifactKind.TRANSCRIPT_MARKDOWN,
    "events.jsonl": ArchiveArtifactKind.EVENTS_JSONL,
    "alerts.log": ArchiveArtifactKind.ALERTS_LOG,
    "reviewer.md": ArchiveArtifactKind.REVIEWER_MARKDOWN,
    "runtime.jsonl": ArchiveArtifactKind.RUNTIME_LOG,
    "benchmark-report.json": ArchiveArtifactKind.BENCHMARK_REPORT,
}


def _validate_safe_session_id(session_id: str) -> str:
    if not _SAFE_SESSION_ID_RE.fullmatch(session_id) or ".." in session_id:
        raise ValueError("session_id must be a safe local identifier")
    return session_id


def _validate_safe_artifact_filename(filename: str) -> str:
    if not filename or filename.strip() != filename:
        raise ValueError("artifact filename must be a safe allowlisted name")
    if any(ord(character) < 32 or ord(character) == 127 for character in filename):
        raise ValueError("artifact filename must not contain control characters")
    lowered = filename.lower()
    if (
        "://" in filename
        or lowered.startswith(("file:", "http:", "https:"))
        or filename.startswith(("/", "\\"))
        or "/" in filename
        or "\\" in filename
        or (len(filename) >= 2 and filename[1] == ":")
        or ".." in filename
    ):
        raise ValueError("artifact filename must not contain path syntax")
    if filename not in _SAFE_ARTIFACT_FILENAMES:
        raise ValueError("artifact filename is not allowlisted")
    return filename


class ArchiveDeleteArtifactCandidate(BaseModel):
    """Safe local artifact candidate for a future confirmed deletion."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: ArchiveArtifactKind
    filename: StrictStr

    @field_validator("filename")
    @classmethod
    def _filename_is_safe(cls, filename: str) -> str:
        return _validate_safe_artifact_filename(filename)

    @model_validator(mode="after")
    def _kind_matches_filename(self) -> "ArchiveDeleteArtifactCandidate":
        expected_kind = _SAFE_ARTIFACT_FILENAMES[self.filename]
        if self.kind != expected_kind:
            raise ValueError("artifact kind must match filename")
        return self


class ArchiveDeletePlan(BaseModel):
    """Immutable description of archive deletion intent only."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    session_id: StrictStr
    artifacts: tuple[ArchiveDeleteArtifactCandidate, ...] = Field(min_length=1)
    requires_confirmation: Literal[True] = True
    intent: ArchiveDeleteIntent = ArchiveDeleteIntent.ARCHIVE_ARTIFACT_CANDIDATES

    @field_validator("session_id")
    @classmethod
    def _session_id_is_safe(cls, session_id: str) -> str:
        return _validate_safe_session_id(session_id)

    @field_validator("requires_confirmation", mode="before")
    @classmethod
    def _requires_confirmation_is_strict_true(cls, value: object) -> object:
        if value is not True:
            raise ValueError("requires_confirmation must be True")
        return value

    @field_validator("artifacts")
    @classmethod
    def _artifacts_are_unique(
        cls,
        artifacts: tuple[ArchiveDeleteArtifactCandidate, ...],
    ) -> tuple[ArchiveDeleteArtifactCandidate, ...]:
        seen_filenames: set[str] = set()
        for artifact in artifacts:
            if artifact.filename in seen_filenames:
                raise ValueError("artifact candidates must be unique")
            seen_filenames.add(artifact.filename)
        return artifacts

    def safe_summary(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "intent": self.intent.value,
            "requires_confirmation": self.requires_confirmation,
            "artifact_count": len(self.artifacts),
            "artifacts": _json_ready_artifacts(self.artifacts),
        }

    def safe_export(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "intent": self.intent.value,
            "requires_confirmation": self.requires_confirmation,
            "artifacts": _json_ready_artifacts(self.artifacts),
        }

    def to_json_ready(self) -> dict[str, object]:
        return self.safe_export()


def _json_ready_artifacts(
    artifacts: tuple[ArchiveDeleteArtifactCandidate, ...],
) -> list[dict[str, str]]:
    return [
        {"kind": artifact.kind.value, "filename": artifact.filename}
        for artifact in artifacts
    ]


def build_archive_delete_plan(manifest: ArchiveExportManifest) -> ArchiveDeletePlan:
    if not isinstance(manifest, ArchiveExportManifest):
        raise TypeError("manifest must be an ArchiveExportManifest")

    return ArchiveDeletePlan(
        session_id=manifest.session_id,
        artifacts=tuple(
            ArchiveDeleteArtifactCandidate(
                kind=artifact.kind,
                filename=artifact.filename,
            )
            for artifact in manifest.artifacts
        ),
    )
