from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
)

from async_scholar.archive_delete_review import (
    ArchiveDeleteReviewArtifact,
    ArchiveDeleteReviewSnapshot,
)

ARCHIVE_DELETE_GATE_KIND: Literal["archive_delete_final_gate"] = (
    "archive_delete_final_gate"
)
ARCHIVE_DELETE_GATE_STATUS: Literal["execution_blocked"] = "execution_blocked"

_SAFE_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def _validate_safe_token(value: str, *, label: str) -> str:
    if value != value.strip():
        raise ValueError(f"{label} must not contain surrounding whitespace")
    if not value:
        raise ValueError(f"{label} must not be blank")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError(f"{label} must not contain control characters")
    if ".." in value:
        raise ValueError(f"{label} must not contain traversal markers")
    if not _SAFE_TOKEN_RE.fullmatch(value):
        raise ValueError(f"{label} must be a safe local token")
    return value


def _validate_true(value: object, *, label: str) -> object:
    if value is not True:
        raise ValueError(f"{label} must be true")
    return value


def _validate_false(value: object, *, label: str) -> object:
    if value is not False:
        raise ValueError(f"{label} must be false")
    return value


class ArchiveDeleteGateArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: StrictStr
    filename: StrictStr
    action: Literal["would_delete"] = "would_delete"
    status: Literal["not_deleted"] = "not_deleted"

    @field_validator("kind")
    @classmethod
    def _validate_kind(cls, value: str) -> str:
        _validate_safe_token(value, label="artifact kind")
        return value

    @field_validator("filename")
    @classmethod
    def _validate_filename(cls, value: str) -> str:
        _validate_safe_token(value, label="artifact filename")
        return value

    @model_validator(mode="after")
    def _validate_review_artifact(self) -> ArchiveDeleteGateArtifact:
        ArchiveDeleteReviewArtifact(
            kind=self.kind,
            filename=self.filename,
            action=self.action,
            status=self.status,
        )
        return self


class ArchiveDeleteFinalGate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: StrictStr
    gate_kind: Literal["archive_delete_final_gate"] = ARCHIVE_DELETE_GATE_KIND
    status: Literal["execution_blocked"] = ARCHIVE_DELETE_GATE_STATUS
    audit_scope: Literal["metadata_only"] = "metadata_only"
    requires_confirmation: bool = True
    review_completed: bool = True
    dry_run_only: bool = True
    deletion_performed: bool = False
    execution_allowed: bool = False
    artifact_count: StrictInt = Field(ge=1)
    artifacts: tuple[ArchiveDeleteGateArtifact, ...] = Field(min_length=1)

    @field_validator("session_id")
    @classmethod
    def _validate_session_id(cls, value: str) -> str:
        return _validate_safe_token(value, label="session_id")

    @field_validator(
        "requires_confirmation",
        "review_completed",
        "dry_run_only",
        mode="before",
    )
    @classmethod
    def _validate_true_flags(cls, value: object) -> object:
        return _validate_true(value, label="final gate flag")

    @field_validator("deletion_performed", "execution_allowed", mode="before")
    @classmethod
    def _validate_false_flags(cls, value: object) -> object:
        return _validate_false(value, label="final gate blocking flag")

    @field_validator("artifact_count", mode="before")
    @classmethod
    def _validate_artifact_count(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("artifact_count must be an integer")
        return value

    @model_validator(mode="after")
    def _validate_artifacts(self) -> ArchiveDeleteFinalGate:
        if self.artifact_count != len(self.artifacts):
            raise ValueError("artifact_count must match artifacts")
        pairs = {(artifact.kind, artifact.filename) for artifact in self.artifacts}
        if len(pairs) != len(self.artifacts):
            raise ValueError("artifacts must be unique")
        return self


def build_archive_delete_final_gate(
    snapshot: ArchiveDeleteReviewSnapshot,
) -> ArchiveDeleteFinalGate:
    safe_snapshot = _ensure_snapshot(snapshot)
    artifacts = tuple(
        ArchiveDeleteGateArtifact(
            kind=artifact.kind,
            filename=artifact.filename,
            action=artifact.action,
            status=artifact.status,
        )
        for artifact in safe_snapshot.artifacts
    )
    return ArchiveDeleteFinalGate(
        session_id=safe_snapshot.session_id,
        artifact_count=safe_snapshot.artifact_count,
        artifacts=artifacts,
    )


def summarize_archive_delete_final_gate(
    gate: ArchiveDeleteFinalGate,
) -> dict[str, object]:
    safe_gate = _ensure_gate(gate)
    return {
        "session_id": safe_gate.session_id,
        "gate_kind": safe_gate.gate_kind,
        "status": safe_gate.status,
        "audit_scope": safe_gate.audit_scope,
        "requires_confirmation": safe_gate.requires_confirmation,
        "review_completed": safe_gate.review_completed,
        "dry_run_only": safe_gate.dry_run_only,
        "deletion_performed": safe_gate.deletion_performed,
        "execution_allowed": safe_gate.execution_allowed,
        "artifact_count": safe_gate.artifact_count,
    }


def export_archive_delete_final_gate(
    gate: ArchiveDeleteFinalGate,
) -> dict[str, Any]:
    safe_gate = _ensure_gate(gate)
    return {
        "session_id": safe_gate.session_id,
        "gate_kind": safe_gate.gate_kind,
        "status": safe_gate.status,
        "audit_scope": safe_gate.audit_scope,
        "requires_confirmation": safe_gate.requires_confirmation,
        "review_completed": safe_gate.review_completed,
        "dry_run_only": safe_gate.dry_run_only,
        "deletion_performed": safe_gate.deletion_performed,
        "execution_allowed": safe_gate.execution_allowed,
        "artifact_count": safe_gate.artifact_count,
        "artifacts": [
            {
                "kind": artifact.kind,
                "filename": artifact.filename,
                "action": artifact.action,
                "status": artifact.status,
            }
            for artifact in safe_gate.artifacts
        ],
    }


def _ensure_snapshot(
    snapshot: ArchiveDeleteReviewSnapshot,
) -> ArchiveDeleteReviewSnapshot:
    if type(snapshot) is not ArchiveDeleteReviewSnapshot:
        raise TypeError("snapshot must be an ArchiveDeleteReviewSnapshot")
    return ArchiveDeleteReviewSnapshot.model_validate(snapshot.model_dump())


def _ensure_gate(gate: ArchiveDeleteFinalGate) -> ArchiveDeleteFinalGate:
    if type(gate) is not ArchiveDeleteFinalGate:
        raise TypeError("gate must be an ArchiveDeleteFinalGate")
    return ArchiveDeleteFinalGate.model_validate(gate.model_dump())
