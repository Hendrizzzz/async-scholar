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

from async_scholar.archive_delete_confirmation import (
    ARCHIVE_DELETE_CONFIRMATION_BODY,
    ARCHIVE_DELETE_CONFIRMATION_PHRASE,
    ARCHIVE_DELETE_CONFIRMATION_TITLE,
    ArchiveDeleteConfirmationPreview,
)

ARCHIVE_DELETE_CONFIRMATION_RESPONSE_STATUS: Literal["confirmation_verified"] = (
    "confirmation_verified"
)

_SAFE_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_ARTIFACT_FILENAME_BY_KIND = {
    "transcript_jsonl": "transcript.jsonl",
    "transcript_markdown": "transcript.md",
    "events_jsonl": "events.jsonl",
    "alerts_log": "alerts.log",
    "reviewer_markdown": "reviewer.md",
    "runtime_log": "runtime.jsonl",
    "benchmark_report": "benchmark-report.json",
}
_ALLOWED_ARTIFACT_FILENAMES = frozenset(_ARTIFACT_FILENAME_BY_KIND.values())


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


class ArchiveDeleteConfirmationResponseArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: StrictStr
    filename: StrictStr

    @field_validator("kind")
    @classmethod
    def _validate_kind(cls, value: str) -> str:
        _validate_safe_token(value, label="artifact kind")
        if value not in _ARTIFACT_FILENAME_BY_KIND:
            raise ValueError("artifact kind is not allowed")
        return value

    @field_validator("filename")
    @classmethod
    def _validate_filename(cls, value: str) -> str:
        _validate_safe_token(value, label="artifact filename")
        if value not in _ALLOWED_ARTIFACT_FILENAMES:
            raise ValueError("artifact filename is not allowed")
        return value

    @model_validator(mode="after")
    def _validate_kind_filename_pair(self) -> ArchiveDeleteConfirmationResponseArtifact:
        if _ARTIFACT_FILENAME_BY_KIND[self.kind] != self.filename:
            raise ValueError("artifact kind and filename do not match")
        return self


class ArchiveDeleteConfirmationResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: StrictStr
    requires_confirmation: bool = True
    confirmation_verified: bool = True
    status: Literal["confirmation_verified"] = (
        ARCHIVE_DELETE_CONFIRMATION_RESPONSE_STATUS
    )
    artifact_count: StrictInt = Field(ge=1)
    artifacts: tuple[ArchiveDeleteConfirmationResponseArtifact, ...] = Field(
        min_length=1
    )

    @field_validator("session_id")
    @classmethod
    def _validate_session_id(cls, value: str) -> str:
        return _validate_safe_token(value, label="session_id")

    @field_validator("requires_confirmation", "confirmation_verified", mode="before")
    @classmethod
    def _validate_confirmation_flags(cls, value: object) -> object:
        return _validate_true(value, label="confirmation flag")

    @field_validator("artifact_count", mode="before")
    @classmethod
    def _validate_artifact_count(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("artifact_count must be an integer")
        return value

    @model_validator(mode="after")
    def _validate_artifacts(self) -> ArchiveDeleteConfirmationResponse:
        if self.artifact_count != len(self.artifacts):
            raise ValueError("artifact_count must match artifacts")
        pairs = {(artifact.kind, artifact.filename) for artifact in self.artifacts}
        if len(pairs) != len(self.artifacts):
            raise ValueError("artifacts must be unique")
        return self


def build_archive_delete_confirmation_response(
    preview: ArchiveDeleteConfirmationPreview, confirmation_phrase: str
) -> ArchiveDeleteConfirmationResponse:
    if type(preview) is not ArchiveDeleteConfirmationPreview:
        raise TypeError("preview must be an ArchiveDeleteConfirmationPreview")
    _ensure_controlled_preview(preview)
    if type(confirmation_phrase) is not str:
        raise TypeError("confirmation phrase must be a string")
    if confirmation_phrase != ARCHIVE_DELETE_CONFIRMATION_PHRASE:
        raise ValueError("confirmation phrase does not match the preview")

    artifacts = tuple(
        ArchiveDeleteConfirmationResponseArtifact(
            kind=artifact.kind,
            filename=artifact.filename,
        )
        for artifact in preview.artifacts
    )
    return ArchiveDeleteConfirmationResponse(
        session_id=preview.session_id,
        artifact_count=preview.artifact_count,
        artifacts=artifacts,
    )


def summarize_archive_delete_confirmation_response(
    response: ArchiveDeleteConfirmationResponse,
) -> dict[str, object]:
    safe_response = _ensure_response(response)
    return {
        "session_id": safe_response.session_id,
        "requires_confirmation": safe_response.requires_confirmation,
        "confirmation_verified": safe_response.confirmation_verified,
        "status": safe_response.status,
        "artifact_count": safe_response.artifact_count,
    }


def export_archive_delete_confirmation_response(
    response: ArchiveDeleteConfirmationResponse,
) -> dict[str, Any]:
    safe_response = _ensure_response(response)
    return {
        "session_id": safe_response.session_id,
        "requires_confirmation": safe_response.requires_confirmation,
        "confirmation_verified": safe_response.confirmation_verified,
        "status": safe_response.status,
        "artifact_count": safe_response.artifact_count,
        "artifacts": [
            {"kind": artifact.kind, "filename": artifact.filename}
            for artifact in safe_response.artifacts
        ],
    }


def _ensure_response(
    response: ArchiveDeleteConfirmationResponse,
) -> ArchiveDeleteConfirmationResponse:
    if type(response) is not ArchiveDeleteConfirmationResponse:
        raise TypeError("response must be an ArchiveDeleteConfirmationResponse")
    return ArchiveDeleteConfirmationResponse.model_validate(response.model_dump())


def _ensure_controlled_preview(preview: ArchiveDeleteConfirmationPreview) -> None:
    if (
        preview.title != ARCHIVE_DELETE_CONFIRMATION_TITLE
        or preview.body != ARCHIVE_DELETE_CONFIRMATION_BODY
        or preview.confirmation_phrase != ARCHIVE_DELETE_CONFIRMATION_PHRASE
        or preview.requires_confirmation is not True
    ):
        raise ValueError("preview confirmation controls are invalid")
