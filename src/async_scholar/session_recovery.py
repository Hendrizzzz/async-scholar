"""Read-only crash-recovery session inventory preflight models."""

from __future__ import annotations

from pathlib import Path
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

from async_scholar.archive_export import (
    ARCHIVE_ARTIFACT_FILENAMES_BY_KIND,
    ArchiveArtifactKind,
    ArchiveSessionInventory,
    _validate_safe_session_directory_name,
    build_archive_session_inventory,
)

RECOVERY_PREFLIGHT_KIND: Literal["crash_recovery_session_preflight"] = (
    "crash_recovery_session_preflight"
)
RECOVERY_STATUS_EMPTY: Literal["empty"] = "empty"
RECOVERY_STATUS_PARTIAL: Literal["partial"] = "partial"
RECOVERY_STATUS_COMPLETE: Literal["complete"] = "complete"
RECOVERY_STATUS_VALUES = (
    RECOVERY_STATUS_EMPTY,
    RECOVERY_STATUS_PARTIAL,
    RECOVERY_STATUS_COMPLETE,
)
CRASH_RECOVERY_PREFLIGHT_ERROR = "crash recovery session preflight could not be built"


class CrashRecoveryPreflightArtifact(BaseModel):
    """Safe metadata for one allowlisted session artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: ArchiveArtifactKind
    filename: StrictStr
    exists: StrictBool
    size_bytes: StrictInt | None = None

    @field_validator("filename")
    @classmethod
    def _filename_matches_allowlist(cls, value: str) -> str:
        allowed_filenames = set(ARCHIVE_ARTIFACT_FILENAMES_BY_KIND.values())
        if value not in allowed_filenames:
            raise ValueError("filename must be an allowlisted session artifact")
        return value

    @field_validator("size_bytes")
    @classmethod
    def _size_is_non_negative(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("size_bytes must be non-negative")
        return value

    @model_validator(mode="after")
    def _metadata_is_consistent(self) -> CrashRecoveryPreflightArtifact:
        expected_filename = ARCHIVE_ARTIFACT_FILENAMES_BY_KIND[self.kind]
        if self.filename != expected_filename:
            raise ValueError("artifact kind and filename must match")
        if self.exists and self.size_bytes is None:
            raise ValueError("existing artifacts must include size_bytes")
        if not self.exists and self.size_bytes is not None:
            raise ValueError("missing artifacts must not include size_bytes")
        return self

    def to_json_ready(self) -> dict[str, object]:
        return _artifact_to_json_ready(_revalidate_artifact(self))


class CrashRecoverySessionPreflight(BaseModel):
    """Metadata-only crash-recovery preflight for one explicit session."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    preflight_kind: Literal["crash_recovery_session_preflight"] = (
        RECOVERY_PREFLIGHT_KIND
    )
    session_id: StrictStr
    session_dir: StrictStr
    recovery_status: Literal["empty", "partial", "complete"]
    existing_count: StrictInt = Field(ge=0)
    missing_count: StrictInt = Field(ge=0)
    total_existing_size_bytes: StrictInt = Field(ge=0)
    artifacts: tuple[CrashRecoveryPreflightArtifact, ...] = Field(min_length=1)

    @field_validator("session_id", "session_dir")
    @classmethod
    def _session_directory_is_safe(cls, value: str) -> str:
        return _validate_safe_session_directory_name(value)

    @model_validator(mode="after")
    def _metadata_is_consistent(self) -> CrashRecoverySessionPreflight:
        if self.session_dir != self.session_id:
            raise ValueError("session_dir must match session_id")

        expected_kinds = tuple(ARCHIVE_ARTIFACT_FILENAMES_BY_KIND)
        artifact_kinds = tuple(artifact.kind for artifact in self.artifacts)
        if artifact_kinds != expected_kinds:
            raise ValueError("artifacts must preserve the session artifact allowlist")

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

        expected_status = _recovery_status_from_counts(
            existing_count,
            len(self.artifacts),
        )
        if self.recovery_status != expected_status:
            raise ValueError("recovery_status must match artifact counts")
        return self

    def to_json_ready(self) -> dict[str, object]:
        return _preflight_to_json_ready(_revalidate_preflight(self))

    def safe_summary(self) -> dict[str, object]:
        return self.to_json_ready()


def _recovery_status_from_counts(
    existing_count: int,
    artifact_count: int,
) -> Literal["empty", "partial", "complete"]:
    if existing_count == 0:
        return RECOVERY_STATUS_EMPTY
    if existing_count == artifact_count:
        return RECOVERY_STATUS_COMPLETE
    return RECOVERY_STATUS_PARTIAL


def _model_to_primitive(model: BaseModel) -> dict[str, object]:
    return model.model_dump()


def _revalidate_artifact(
    artifact: CrashRecoveryPreflightArtifact,
) -> CrashRecoveryPreflightArtifact:
    if type(artifact) is not CrashRecoveryPreflightArtifact:
        raise ValueError(CRASH_RECOVERY_PREFLIGHT_ERROR)
    try:
        return CrashRecoveryPreflightArtifact(**_model_to_primitive(artifact))
    except (TypeError, ValidationError, ValueError):
        raise ValueError(CRASH_RECOVERY_PREFLIGHT_ERROR) from None


def _revalidate_preflight(
    preflight: CrashRecoverySessionPreflight,
) -> CrashRecoverySessionPreflight:
    if type(preflight) is not CrashRecoverySessionPreflight:
        raise ValueError(CRASH_RECOVERY_PREFLIGHT_ERROR)
    try:
        return CrashRecoverySessionPreflight(**_model_to_primitive(preflight))
    except (TypeError, ValidationError, ValueError):
        raise ValueError(CRASH_RECOVERY_PREFLIGHT_ERROR) from None


def _artifact_to_json_ready(
    artifact: CrashRecoveryPreflightArtifact,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "kind": artifact.kind.value,
        "filename": artifact.filename,
        "exists": artifact.exists,
    }
    if artifact.size_bytes is not None:
        payload["size_bytes"] = artifact.size_bytes
    return payload


def _preflight_to_json_ready(
    preflight: CrashRecoverySessionPreflight,
) -> dict[str, object]:
    return {
        "preflight_kind": preflight.preflight_kind,
        "session_id": preflight.session_id,
        "session_dir": preflight.session_dir,
        "recovery_status": preflight.recovery_status,
        "existing_count": preflight.existing_count,
        "missing_count": preflight.missing_count,
        "total_existing_size_bytes": preflight.total_existing_size_bytes,
        "artifacts": [
            _artifact_to_json_ready(artifact) for artifact in preflight.artifacts
        ],
    }


def _artifact_from_inventory(
    inventory_artifact: object,
) -> CrashRecoveryPreflightArtifact:
    return CrashRecoveryPreflightArtifact(
        kind=inventory_artifact.kind,
        filename=inventory_artifact.filename,
        exists=inventory_artifact.exists,
        size_bytes=inventory_artifact.size_bytes,
    )


def _summary_from_inventory(
    inventory: ArchiveSessionInventory,
) -> CrashRecoverySessionPreflight:
    artifacts = tuple(
        _artifact_from_inventory(artifact) for artifact in inventory.artifacts
    )
    existing_count = sum(1 for artifact in artifacts if artifact.exists)
    return CrashRecoverySessionPreflight(
        session_id=inventory.session_id,
        session_dir=inventory.session_dir,
        recovery_status=_recovery_status_from_counts(existing_count, len(artifacts)),
        existing_count=existing_count,
        missing_count=len(artifacts) - existing_count,
        total_existing_size_bytes=sum(
            artifact.size_bytes or 0 for artifact in artifacts if artifact.exists
        ),
        artifacts=artifacts,
    )


def build_crash_recovery_session_preflight(
    sessions_root: str | Path,
    session_id: str,
) -> CrashRecoverySessionPreflight:
    """Build a read-only metadata preflight for one session root."""

    try:
        inventory = build_archive_session_inventory(sessions_root, session_id)
        return _summary_from_inventory(inventory)
    except (OSError, RuntimeError, TypeError, ValidationError, ValueError):
        raise ValueError(CRASH_RECOVERY_PREFLIGHT_ERROR) from None


def crash_recovery_session_preflight_to_json_ready(
    preflight: CrashRecoverySessionPreflight,
) -> dict[str, object]:
    return _preflight_to_json_ready(_revalidate_preflight(preflight))


def crash_recovery_session_preflight_safe_summary(
    preflight: CrashRecoverySessionPreflight,
) -> dict[str, object]:
    return _preflight_to_json_ready(_revalidate_preflight(preflight))
