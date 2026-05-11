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

from async_scholar.archive_delete_dry_run_result import (
    ARCHIVE_DELETE_DRY_RUN_ARTIFACT_ACTION,
    ARCHIVE_DELETE_DRY_RUN_ARTIFACT_STATUS,
    ArchiveDeleteDryRunResult,
    ArchiveDeleteDryRunResultArtifact,
)

ARCHIVE_DELETE_AUDIT_EVENT_KIND: Literal["archive_delete_dry_run_audit"] = (
    "archive_delete_dry_run_audit"
)
ARCHIVE_DELETE_AUDIT_STATUS: Literal["dry_run_audited"] = "dry_run_audited"
ARCHIVE_DELETE_AUDIT_SCOPE: Literal["metadata_only"] = "metadata_only"

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


class ArchiveDeleteAuditArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: StrictStr
    filename: StrictStr
    action: Literal["would_delete"] = ARCHIVE_DELETE_DRY_RUN_ARTIFACT_ACTION
    status: Literal["not_deleted"] = ARCHIVE_DELETE_DRY_RUN_ARTIFACT_STATUS

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
    def _validate_dry_run_result_artifact(self) -> ArchiveDeleteAuditArtifact:
        ArchiveDeleteDryRunResultArtifact(
            kind=self.kind,
            filename=self.filename,
            action=self.action,
            status=self.status,
        )
        return self


class ArchiveDeleteAuditEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: StrictStr
    event_kind: Literal["archive_delete_dry_run_audit"] = (
        ARCHIVE_DELETE_AUDIT_EVENT_KIND
    )
    status: Literal["dry_run_audited"] = ARCHIVE_DELETE_AUDIT_STATUS
    audit_scope: Literal["metadata_only"] = ARCHIVE_DELETE_AUDIT_SCOPE
    requires_confirmation: bool = True
    confirmation_verified: bool = True
    dry_run_only: bool = True
    deletion_performed: bool = False
    artifact_count: StrictInt = Field(ge=1)
    artifacts: tuple[ArchiveDeleteAuditArtifact, ...] = Field(min_length=1)

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
        return _validate_true(value, label="audit event flag")

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
    def _validate_artifacts(self) -> ArchiveDeleteAuditEvent:
        if self.artifact_count != len(self.artifacts):
            raise ValueError("artifact_count must match artifacts")
        pairs = {(artifact.kind, artifact.filename) for artifact in self.artifacts}
        if len(pairs) != len(self.artifacts):
            raise ValueError("artifacts must be unique")
        return self


def build_archive_delete_audit_event(
    result: ArchiveDeleteDryRunResult,
) -> ArchiveDeleteAuditEvent:
    safe_result = _ensure_result(result)
    artifacts = tuple(
        ArchiveDeleteAuditArtifact(
            kind=artifact.kind,
            filename=artifact.filename,
            action=artifact.action,
            status=artifact.status,
        )
        for artifact in safe_result.artifacts
    )
    return ArchiveDeleteAuditEvent(
        session_id=safe_result.session_id,
        artifact_count=safe_result.artifact_count,
        artifacts=artifacts,
    )


def summarize_archive_delete_audit_event(
    event: ArchiveDeleteAuditEvent,
) -> dict[str, object]:
    safe_event = _ensure_event(event)
    return {
        "session_id": safe_event.session_id,
        "event_kind": safe_event.event_kind,
        "status": safe_event.status,
        "audit_scope": safe_event.audit_scope,
        "requires_confirmation": safe_event.requires_confirmation,
        "confirmation_verified": safe_event.confirmation_verified,
        "dry_run_only": safe_event.dry_run_only,
        "deletion_performed": safe_event.deletion_performed,
        "artifact_count": safe_event.artifact_count,
    }


def export_archive_delete_audit_event(
    event: ArchiveDeleteAuditEvent,
) -> dict[str, Any]:
    safe_event = _ensure_event(event)
    return {
        "session_id": safe_event.session_id,
        "event_kind": safe_event.event_kind,
        "status": safe_event.status,
        "audit_scope": safe_event.audit_scope,
        "requires_confirmation": safe_event.requires_confirmation,
        "confirmation_verified": safe_event.confirmation_verified,
        "dry_run_only": safe_event.dry_run_only,
        "deletion_performed": safe_event.deletion_performed,
        "artifact_count": safe_event.artifact_count,
        "artifacts": [
            {
                "kind": artifact.kind,
                "filename": artifact.filename,
                "action": artifact.action,
                "status": artifact.status,
            }
            for artifact in safe_event.artifacts
        ],
    }


def _ensure_result(result: ArchiveDeleteDryRunResult) -> ArchiveDeleteDryRunResult:
    if type(result) is not ArchiveDeleteDryRunResult:
        raise TypeError("result must be an ArchiveDeleteDryRunResult")
    return ArchiveDeleteDryRunResult.model_validate(result.model_dump())


def _ensure_event(event: ArchiveDeleteAuditEvent) -> ArchiveDeleteAuditEvent:
    if type(event) is not ArchiveDeleteAuditEvent:
        raise TypeError("event must be an ArchiveDeleteAuditEvent")
    return ArchiveDeleteAuditEvent.model_validate(event.model_dump())
