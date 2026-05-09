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

from async_scholar.archive_delete_confirmation_response import (
    ArchiveDeleteConfirmationResponse,
    ArchiveDeleteConfirmationResponseArtifact,
)

ARCHIVE_DELETE_DRY_RUN_REQUEST_KIND: Literal["archive_delete_dry_run"] = (
    "archive_delete_dry_run"
)
ARCHIVE_DELETE_DRY_RUN_STATUS: Literal["dry_run_requested"] = "dry_run_requested"

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


class ArchiveDeleteDryRunRequestArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: StrictStr
    filename: StrictStr

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
    def _validate_confirmation_response_artifact(
        self,
    ) -> ArchiveDeleteDryRunRequestArtifact:
        ArchiveDeleteConfirmationResponseArtifact(
            kind=self.kind,
            filename=self.filename,
        )
        return self


class ArchiveDeleteDryRunRequest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: StrictStr
    request_kind: Literal["archive_delete_dry_run"] = (
        ARCHIVE_DELETE_DRY_RUN_REQUEST_KIND
    )
    status: Literal["dry_run_requested"] = ARCHIVE_DELETE_DRY_RUN_STATUS
    requires_confirmation: bool = True
    confirmation_verified: bool = True
    dry_run_only: bool = True
    artifact_count: StrictInt = Field(ge=1)
    artifacts: tuple[ArchiveDeleteDryRunRequestArtifact, ...] = Field(min_length=1)

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
        return _validate_true(value, label="dry-run request flag")

    @field_validator("artifact_count", mode="before")
    @classmethod
    def _validate_artifact_count(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("artifact_count must be an integer")
        return value

    @model_validator(mode="after")
    def _validate_artifacts(self) -> ArchiveDeleteDryRunRequest:
        if self.artifact_count != len(self.artifacts):
            raise ValueError("artifact_count must match artifacts")
        pairs = {(artifact.kind, artifact.filename) for artifact in self.artifacts}
        if len(pairs) != len(self.artifacts):
            raise ValueError("artifacts must be unique")
        return self


def build_archive_delete_dry_run_request(
    response: ArchiveDeleteConfirmationResponse,
) -> ArchiveDeleteDryRunRequest:
    safe_response = _ensure_response(response)
    artifacts = tuple(
        ArchiveDeleteDryRunRequestArtifact(
            kind=artifact.kind,
            filename=artifact.filename,
        )
        for artifact in safe_response.artifacts
    )
    return ArchiveDeleteDryRunRequest(
        session_id=safe_response.session_id,
        artifact_count=safe_response.artifact_count,
        artifacts=artifacts,
    )


def summarize_archive_delete_dry_run_request(
    request: ArchiveDeleteDryRunRequest,
) -> dict[str, object]:
    safe_request = _ensure_request(request)
    return {
        "session_id": safe_request.session_id,
        "request_kind": safe_request.request_kind,
        "status": safe_request.status,
        "requires_confirmation": safe_request.requires_confirmation,
        "confirmation_verified": safe_request.confirmation_verified,
        "dry_run_only": safe_request.dry_run_only,
        "artifact_count": safe_request.artifact_count,
    }


def export_archive_delete_dry_run_request(
    request: ArchiveDeleteDryRunRequest,
) -> dict[str, Any]:
    safe_request = _ensure_request(request)
    return {
        "session_id": safe_request.session_id,
        "request_kind": safe_request.request_kind,
        "status": safe_request.status,
        "requires_confirmation": safe_request.requires_confirmation,
        "confirmation_verified": safe_request.confirmation_verified,
        "dry_run_only": safe_request.dry_run_only,
        "artifact_count": safe_request.artifact_count,
        "artifacts": [
            {"kind": artifact.kind, "filename": artifact.filename}
            for artifact in safe_request.artifacts
        ],
    }


def _ensure_response(
    response: ArchiveDeleteConfirmationResponse,
) -> ArchiveDeleteConfirmationResponse:
    if type(response) is not ArchiveDeleteConfirmationResponse:
        raise TypeError("response must be an ArchiveDeleteConfirmationResponse")
    return ArchiveDeleteConfirmationResponse.model_validate(response.model_dump())


def _ensure_request(
    request: ArchiveDeleteDryRunRequest,
) -> ArchiveDeleteDryRunRequest:
    if type(request) is not ArchiveDeleteDryRunRequest:
        raise TypeError("request must be an ArchiveDeleteDryRunRequest")
    return ArchiveDeleteDryRunRequest.model_validate(request.model_dump())
