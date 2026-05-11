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

from async_scholar.archive_delete_audit import (
    ARCHIVE_DELETE_AUDIT_SCOPE,
    ArchiveDeleteAuditArtifact,
    ArchiveDeleteAuditEvent,
)

ARCHIVE_DELETE_REVIEW_SNAPSHOT_KIND: Literal["archive_delete_review_snapshot"] = (
    "archive_delete_review_snapshot"
)
ARCHIVE_DELETE_REVIEW_STATUS: Literal["review_snapshot_ready"] = "review_snapshot_ready"

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


class ArchiveDeleteReviewArtifact(BaseModel):
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
    def _validate_audit_artifact(self) -> ArchiveDeleteReviewArtifact:
        ArchiveDeleteAuditArtifact(
            kind=self.kind,
            filename=self.filename,
            action=self.action,
            status=self.status,
        )
        return self


class ArchiveDeleteReviewSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: StrictStr
    snapshot_kind: Literal["archive_delete_review_snapshot"] = (
        ARCHIVE_DELETE_REVIEW_SNAPSHOT_KIND
    )
    status: Literal["review_snapshot_ready"] = ARCHIVE_DELETE_REVIEW_STATUS
    audit_scope: Literal["metadata_only"] = ARCHIVE_DELETE_AUDIT_SCOPE
    requires_confirmation: bool = True
    confirmation_verified: bool = True
    dry_run_only: bool = True
    deletion_performed: bool = False
    artifact_count: StrictInt = Field(ge=1)
    artifacts: tuple[ArchiveDeleteReviewArtifact, ...] = Field(min_length=1)

    @field_validator("session_id")
    @classmethod
    def _validate_session_id(cls, value: str) -> str:
        return _validate_safe_token(value, label="session_id")

    @field_validator(
        "requires_confirmation",
        "confirmation_verified",
        "dry_run_only",
        mode="before",
    )
    @classmethod
    def _validate_true_flags(cls, value: object) -> object:
        return _validate_true(value, label="review snapshot flag")

    @field_validator("deletion_performed", mode="before")
    @classmethod
    def _validate_deletion_performed(cls, value: object) -> object:
        return _validate_false(value, label="deletion_performed")

    @field_validator("artifact_count", mode="before")
    @classmethod
    def _validate_artifact_count(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("artifact_count must be an integer")
        return value

    @model_validator(mode="after")
    def _validate_artifacts(self) -> ArchiveDeleteReviewSnapshot:
        if self.artifact_count != len(self.artifacts):
            raise ValueError("artifact_count must match artifacts")
        pairs = {(artifact.kind, artifact.filename) for artifact in self.artifacts}
        if len(pairs) != len(self.artifacts):
            raise ValueError("artifacts must be unique")
        return self


def build_archive_delete_review_snapshot(
    event: ArchiveDeleteAuditEvent,
) -> ArchiveDeleteReviewSnapshot:
    safe_event = _ensure_event(event)
    artifacts = tuple(
        ArchiveDeleteReviewArtifact(
            kind=artifact.kind,
            filename=artifact.filename,
            action=artifact.action,
            status=artifact.status,
        )
        for artifact in safe_event.artifacts
    )
    return ArchiveDeleteReviewSnapshot(
        session_id=safe_event.session_id,
        artifact_count=safe_event.artifact_count,
        artifacts=artifacts,
    )


def summarize_archive_delete_review_snapshot(
    snapshot: ArchiveDeleteReviewSnapshot,
) -> dict[str, object]:
    safe_snapshot = _ensure_snapshot(snapshot)
    return {
        "session_id": safe_snapshot.session_id,
        "snapshot_kind": safe_snapshot.snapshot_kind,
        "status": safe_snapshot.status,
        "audit_scope": safe_snapshot.audit_scope,
        "requires_confirmation": safe_snapshot.requires_confirmation,
        "confirmation_verified": safe_snapshot.confirmation_verified,
        "dry_run_only": safe_snapshot.dry_run_only,
        "deletion_performed": safe_snapshot.deletion_performed,
        "artifact_count": safe_snapshot.artifact_count,
    }


def export_archive_delete_review_snapshot(
    snapshot: ArchiveDeleteReviewSnapshot,
) -> dict[str, Any]:
    safe_snapshot = _ensure_snapshot(snapshot)
    return {
        "session_id": safe_snapshot.session_id,
        "snapshot_kind": safe_snapshot.snapshot_kind,
        "status": safe_snapshot.status,
        "audit_scope": safe_snapshot.audit_scope,
        "requires_confirmation": safe_snapshot.requires_confirmation,
        "confirmation_verified": safe_snapshot.confirmation_verified,
        "dry_run_only": safe_snapshot.dry_run_only,
        "deletion_performed": safe_snapshot.deletion_performed,
        "artifact_count": safe_snapshot.artifact_count,
        "artifacts": [
            {
                "kind": artifact.kind,
                "filename": artifact.filename,
                "action": artifact.action,
                "status": artifact.status,
            }
            for artifact in safe_snapshot.artifacts
        ],
    }


def _ensure_event(event: ArchiveDeleteAuditEvent) -> ArchiveDeleteAuditEvent:
    if type(event) is not ArchiveDeleteAuditEvent:
        raise TypeError("event must be an ArchiveDeleteAuditEvent")
    return ArchiveDeleteAuditEvent.model_validate(event.model_dump())


def _ensure_snapshot(
    snapshot: ArchiveDeleteReviewSnapshot,
) -> ArchiveDeleteReviewSnapshot:
    if type(snapshot) is not ArchiveDeleteReviewSnapshot:
        raise TypeError("snapshot must be an ArchiveDeleteReviewSnapshot")
    return ArchiveDeleteReviewSnapshot.model_validate(snapshot.model_dump())
