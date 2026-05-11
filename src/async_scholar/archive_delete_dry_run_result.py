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

from async_scholar.archive_delete_dry_run import (
    ArchiveDeleteDryRunRequest,
    ArchiveDeleteDryRunRequestArtifact,
)

ARCHIVE_DELETE_DRY_RUN_RESULT_KIND: Literal["archive_delete_dry_run_result"] = (
    "archive_delete_dry_run_result"
)
ARCHIVE_DELETE_DRY_RUN_RESULT_STATUS: Literal["dry_run_completed"] = "dry_run_completed"
ARCHIVE_DELETE_DRY_RUN_ARTIFACT_ACTION: Literal["would_delete"] = "would_delete"
ARCHIVE_DELETE_DRY_RUN_ARTIFACT_STATUS: Literal["not_deleted"] = "not_deleted"

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


class ArchiveDeleteDryRunResultArtifact(BaseModel):
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
    def _validate_dry_run_request_artifact(
        self,
    ) -> ArchiveDeleteDryRunResultArtifact:
        ArchiveDeleteDryRunRequestArtifact(
            kind=self.kind,
            filename=self.filename,
        )
        return self


class ArchiveDeleteDryRunResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: StrictStr
    result_kind: Literal["archive_delete_dry_run_result"] = (
        ARCHIVE_DELETE_DRY_RUN_RESULT_KIND
    )
    status: Literal["dry_run_completed"] = ARCHIVE_DELETE_DRY_RUN_RESULT_STATUS
    requires_confirmation: bool = True
    confirmation_verified: bool = True
    dry_run_only: bool = True
    deletion_performed: bool = False
    artifact_count: StrictInt = Field(ge=1)
    artifacts: tuple[ArchiveDeleteDryRunResultArtifact, ...] = Field(min_length=1)

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
        return _validate_true(value, label="dry-run result flag")

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
    def _validate_artifacts(self) -> ArchiveDeleteDryRunResult:
        if self.artifact_count != len(self.artifacts):
            raise ValueError("artifact_count must match artifacts")
        pairs = {(artifact.kind, artifact.filename) for artifact in self.artifacts}
        if len(pairs) != len(self.artifacts):
            raise ValueError("artifacts must be unique")
        return self


def build_archive_delete_dry_run_result(
    request: ArchiveDeleteDryRunRequest,
) -> ArchiveDeleteDryRunResult:
    safe_request = _ensure_request(request)
    artifacts = tuple(
        ArchiveDeleteDryRunResultArtifact(
            kind=artifact.kind,
            filename=artifact.filename,
        )
        for artifact in safe_request.artifacts
    )
    return ArchiveDeleteDryRunResult(
        session_id=safe_request.session_id,
        artifact_count=safe_request.artifact_count,
        artifacts=artifacts,
    )


def summarize_archive_delete_dry_run_result(
    result: ArchiveDeleteDryRunResult,
) -> dict[str, object]:
    safe_result = _ensure_result(result)
    return {
        "session_id": safe_result.session_id,
        "result_kind": safe_result.result_kind,
        "status": safe_result.status,
        "requires_confirmation": safe_result.requires_confirmation,
        "confirmation_verified": safe_result.confirmation_verified,
        "dry_run_only": safe_result.dry_run_only,
        "deletion_performed": safe_result.deletion_performed,
        "artifact_count": safe_result.artifact_count,
    }


def export_archive_delete_dry_run_result(
    result: ArchiveDeleteDryRunResult,
) -> dict[str, Any]:
    safe_result = _ensure_result(result)
    return {
        "session_id": safe_result.session_id,
        "result_kind": safe_result.result_kind,
        "status": safe_result.status,
        "requires_confirmation": safe_result.requires_confirmation,
        "confirmation_verified": safe_result.confirmation_verified,
        "dry_run_only": safe_result.dry_run_only,
        "deletion_performed": safe_result.deletion_performed,
        "artifact_count": safe_result.artifact_count,
        "artifacts": [
            {
                "kind": artifact.kind,
                "filename": artifact.filename,
                "action": artifact.action,
                "status": artifact.status,
            }
            for artifact in safe_result.artifacts
        ],
    }


def _ensure_request(
    request: ArchiveDeleteDryRunRequest,
) -> ArchiveDeleteDryRunRequest:
    if type(request) is not ArchiveDeleteDryRunRequest:
        raise TypeError("request must be an ArchiveDeleteDryRunRequest")
    return ArchiveDeleteDryRunRequest.model_validate(request.model_dump())


def _ensure_result(
    result: ArchiveDeleteDryRunResult,
) -> ArchiveDeleteDryRunResult:
    if type(result) is not ArchiveDeleteDryRunResult:
        raise TypeError("result must be an ArchiveDeleteDryRunResult")
    return ArchiveDeleteDryRunResult.model_validate(result.model_dump())
