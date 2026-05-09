"""Privacy-safe archive delete confirmation preview models."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from async_scholar.archive_delete import (
    ArchiveDeleteArtifactCandidate,
    ArchiveDeletePlan,
)

ARCHIVE_DELETE_CONFIRMATION_TITLE = "Archive delete confirmation"
ARCHIVE_DELETE_CONFIRMATION_BODY = (
    "Review the listed archive artifacts before confirming this local archive cleanup."
)
ARCHIVE_DELETE_CONFIRMATION_PHRASE = "DELETE ARCHIVE"

_MAX_SAFE_TEXT_LENGTH = 128
_SAFE_SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


def _validate_safe_text(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be blank")
    if len(value) > _MAX_SAFE_TEXT_LENGTH:
        raise ValueError(f"{field_name} is too long")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError(f"{field_name} must not contain control characters")
    return value


def _validate_safe_session_id(value: Any) -> str:
    session_id = _validate_safe_text(value, field_name="session_id")
    if ".." in session_id:
        raise ValueError("session_id must not contain traversal markers")
    if not _SAFE_SESSION_ID_PATTERN.fullmatch(session_id):
        raise ValueError("session_id contains unsafe characters")
    return session_id


def _reject_collection_scalar(value: Any, *, field_name: str) -> Any:
    if isinstance(value, (str, bytes, bytearray)):
        raise ValueError(f"{field_name} must be a collection, not scalar text")
    return value


class ArchiveDeleteConfirmationArtifact(BaseModel):
    """Safe artifact metadata copied from an archive delete plan."""

    kind: str
    filename: str

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)

    @field_validator("kind", "filename", mode="before")
    @classmethod
    def _validate_text_fields(cls, value: Any, info: Any) -> str:
        return _validate_safe_text(value, field_name=info.field_name)

    @model_validator(mode="after")
    def _validate_delete_plan_candidate(self) -> ArchiveDeleteConfirmationArtifact:
        try:
            ArchiveDeleteArtifactCandidate(kind=self.kind, filename=self.filename)
        except ValidationError as exc:
            raise ValueError(
                "artifact metadata must match a safe archive delete candidate"
            ) from exc
        return self

    def to_safe_metadata(self) -> dict[str, str]:
        return {"kind": self.kind, "filename": self.filename}


class ArchiveDeleteConfirmationPreview(BaseModel):
    """Immutable confirmation preview derived from an archive delete plan."""

    session_id: str
    title: Literal[ARCHIVE_DELETE_CONFIRMATION_TITLE] = (
        ARCHIVE_DELETE_CONFIRMATION_TITLE
    )
    body: Literal[ARCHIVE_DELETE_CONFIRMATION_BODY] = ARCHIVE_DELETE_CONFIRMATION_BODY
    requires_confirmation: bool = True
    confirmation_phrase: Literal[ARCHIVE_DELETE_CONFIRMATION_PHRASE] = (
        ARCHIVE_DELETE_CONFIRMATION_PHRASE
    )
    artifact_count: int = Field(ge=1)
    artifacts: tuple[ArchiveDeleteConfirmationArtifact, ...] = Field(min_length=1)

    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True)

    @field_validator("session_id", mode="before")
    @classmethod
    def _validate_session_id(cls, value: Any) -> str:
        return _validate_safe_session_id(value)

    @field_validator("title", mode="before")
    @classmethod
    def _validate_title(cls, value: Any) -> str:
        if value != ARCHIVE_DELETE_CONFIRMATION_TITLE:
            raise ValueError(
                "title must use the controlled archive delete confirmation text"
            )
        return value

    @field_validator("body", mode="before")
    @classmethod
    def _validate_body(cls, value: Any) -> str:
        if value != ARCHIVE_DELETE_CONFIRMATION_BODY:
            raise ValueError(
                "body must use the controlled archive delete confirmation text"
            )
        return value

    @field_validator("requires_confirmation", mode="before")
    @classmethod
    def _validate_requires_confirmation(cls, value: Any) -> bool:
        if value is not True:
            raise ValueError("requires_confirmation must be exactly true")
        return value

    @field_validator("confirmation_phrase", mode="before")
    @classmethod
    def _validate_confirmation_phrase(cls, value: Any) -> str:
        if value != ARCHIVE_DELETE_CONFIRMATION_PHRASE:
            raise ValueError(
                "confirmation_phrase must use the controlled confirmation phrase"
            )
        return value

    @field_validator("artifact_count", mode="before")
    @classmethod
    def _validate_artifact_count(cls, value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("artifact_count must be an integer")
        return value

    @field_validator("artifacts", mode="before")
    @classmethod
    def _validate_artifacts_collection(cls, value: Any) -> Any:
        return _reject_collection_scalar(value, field_name="artifacts")

    @model_validator(mode="after")
    def _validate_artifact_summary(self) -> ArchiveDeleteConfirmationPreview:
        if self.artifact_count != len(self.artifacts):
            raise ValueError("artifact_count must match artifacts length")

        seen_artifacts: set[tuple[str, str]] = set()
        for artifact in self.artifacts:
            metadata_key = (artifact.kind, artifact.filename)
            if metadata_key in seen_artifacts:
                raise ValueError("artifacts must not contain duplicates")
            seen_artifacts.add(metadata_key)
        return self

    def to_safe_summary(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "title": self.title,
            "body": self.body,
            "requires_confirmation": self.requires_confirmation,
            "confirmation_phrase": self.confirmation_phrase,
            "artifact_count": self.artifact_count,
        }

    def to_safe_export(self) -> dict[str, object]:
        safe_export = self.to_safe_summary()
        safe_export["artifacts"] = [
            artifact.to_safe_metadata() for artifact in self.artifacts
        ]
        return safe_export


def _require_archive_delete_plan(value: Any) -> ArchiveDeletePlan:
    if type(value) is not ArchiveDeletePlan:
        raise TypeError(
            "archive delete confirmation preview requires an ArchiveDeletePlan"
        )
    return value


def _require_confirmation_preview(value: Any) -> ArchiveDeleteConfirmationPreview:
    if type(value) is not ArchiveDeleteConfirmationPreview:
        raise TypeError(
            "safe confirmation helpers require an ArchiveDeleteConfirmationPreview"
        )
    return value


def build_archive_delete_confirmation_preview(
    delete_plan: ArchiveDeletePlan,
) -> ArchiveDeleteConfirmationPreview:
    """Build a confirmation preview by copying safe metadata from a delete plan."""

    plan = _require_archive_delete_plan(delete_plan)
    artifacts = tuple(
        ArchiveDeleteConfirmationArtifact(
            kind=artifact.kind, filename=artifact.filename
        )
        for artifact in plan.artifacts
    )
    return ArchiveDeleteConfirmationPreview(
        session_id=plan.session_id,
        artifact_count=len(artifacts),
        artifacts=artifacts,
    )


def summarize_archive_delete_confirmation(
    preview: ArchiveDeleteConfirmationPreview,
) -> dict[str, object]:
    """Return JSON-ready safe confirmation summary data."""

    return _require_confirmation_preview(preview).to_safe_summary()


def export_archive_delete_confirmation(
    preview: ArchiveDeleteConfirmationPreview,
) -> dict[str, object]:
    """Return JSON-ready safe confirmation preview data."""

    return _require_confirmation_preview(preview).to_safe_export()


__all__ = [
    "ARCHIVE_DELETE_CONFIRMATION_BODY",
    "ARCHIVE_DELETE_CONFIRMATION_PHRASE",
    "ARCHIVE_DELETE_CONFIRMATION_TITLE",
    "ArchiveDeleteConfirmationArtifact",
    "ArchiveDeleteConfirmationPreview",
    "build_archive_delete_confirmation_preview",
    "export_archive_delete_confirmation",
    "summarize_archive_delete_confirmation",
]
