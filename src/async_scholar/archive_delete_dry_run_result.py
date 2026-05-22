from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

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

from async_scholar.archive_delete_dry_run import (
    ArchiveDeleteDryRunRequest,
    ArchiveDeleteDryRunRequestArtifact,
)
from async_scholar.archive_export import (
    ARCHIVE_ARTIFACT_FILENAMES_BY_KIND,
    ArchiveArtifactKind,
)

ARCHIVE_DELETE_DRY_RUN_RESULT_KIND: Literal["archive_delete_dry_run_result"] = (
    "archive_delete_dry_run_result"
)
ARCHIVE_DELETE_DRY_RUN_RESULT_STATUS: Literal["dry_run_completed"] = "dry_run_completed"
ARCHIVE_DELETE_DRY_RUN_ARTIFACT_ACTION: Literal["would_delete"] = "would_delete"
ARCHIVE_DELETE_DRY_RUN_ARTIFACT_STATUS: Literal["not_deleted"] = "not_deleted"
ARCHIVE_DELETE_DRY_RUN_LOCAL_ERROR = "archive delete dry run could not be built"

_SAFE_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_WINDOWS_RESERVED_SESSION_NAMES = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{index}" for index in range(1, 10)),
        *(f"LPT{index}" for index in range(1, 10)),
    }
)


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


def _validate_safe_session_id(value: str) -> str:
    safe_value = _validate_safe_token(value, label="session_id")
    reserved_candidate = safe_value.split(".", maxsplit=1)[0].upper()
    if reserved_candidate in _WINDOWS_RESERVED_SESSION_NAMES:
        raise ValueError("session_id must not use a reserved device name")
    return safe_value


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
        return _validate_safe_session_id(value)

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


class ArchiveDeleteDryRunLocalArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: ArchiveArtifactKind
    filename: StrictStr
    exists: StrictBool
    size_bytes: StrictInt | None = None
    action: Literal["would_delete"] = ARCHIVE_DELETE_DRY_RUN_ARTIFACT_ACTION
    status: Literal["not_deleted"] = ARCHIVE_DELETE_DRY_RUN_ARTIFACT_STATUS

    @field_validator("filename")
    @classmethod
    def _validate_filename(cls, value: str) -> str:
        _validate_safe_token(value, label="artifact filename")
        return value

    @field_validator("size_bytes")
    @classmethod
    def _validate_size_bytes(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("size_bytes must be non-negative")
        return value

    @model_validator(mode="after")
    def _validate_artifact_metadata(self) -> ArchiveDeleteDryRunLocalArtifact:
        expected_filename = ARCHIVE_ARTIFACT_FILENAMES_BY_KIND[self.kind]
        if self.filename != expected_filename:
            raise ValueError("artifact kind and filename do not match")
        if self.exists and self.size_bytes is None:
            raise ValueError("existing artifacts must include size_bytes")
        if not self.exists and self.size_bytes is not None:
            raise ValueError("missing artifacts must not include size_bytes")
        return self

    def to_json_ready(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "kind": self.kind.value,
            "filename": self.filename,
            "exists": self.exists,
            "action": self.action,
            "status": self.status,
        }
        if self.size_bytes is not None:
            payload["size_bytes"] = self.size_bytes
        return payload


class ArchiveDeleteDryRunLocalResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: StrictStr
    session_dir: StrictStr
    result_kind: Literal["archive_delete_dry_run_result"] = (
        ARCHIVE_DELETE_DRY_RUN_RESULT_KIND
    )
    status: Literal["dry_run_completed"] = ARCHIVE_DELETE_DRY_RUN_RESULT_STATUS
    dry_run_only: bool = True
    deletion_performed: bool = False
    artifact_count: StrictInt = Field(ge=1)
    existing_artifact_count: StrictInt = Field(ge=0)
    total_existing_size_bytes: StrictInt = Field(ge=0)
    artifacts: tuple[ArchiveDeleteDryRunLocalArtifact, ...] = Field(min_length=1)

    @field_validator("session_id", "session_dir")
    @classmethod
    def _validate_session_identifier(cls, value: str) -> str:
        return _validate_safe_session_id(value)

    @field_validator("dry_run_only", mode="before")
    @classmethod
    def _validate_dry_run_only(cls, value: object) -> object:
        return _validate_true(value, label="dry_run_only")

    @field_validator("deletion_performed", mode="before")
    @classmethod
    def _validate_deletion_performed(cls, value: object) -> object:
        return _validate_false(value, label="deletion_performed")

    @model_validator(mode="after")
    def _validate_result_metadata(self) -> ArchiveDeleteDryRunLocalResult:
        if self.session_dir != self.session_id:
            raise ValueError("session_dir must match session_id")
        expected_kinds = tuple(ARCHIVE_ARTIFACT_FILENAMES_BY_KIND)
        artifact_kinds = tuple(artifact.kind for artifact in self.artifacts)
        if artifact_kinds != expected_kinds:
            raise ValueError("dry-run artifacts must match the archive allowlist")
        existing_count = sum(1 for artifact in self.artifacts if artifact.exists)
        total_size = sum(
            artifact.size_bytes or 0 for artifact in self.artifacts if artifact.exists
        )
        if self.artifact_count != len(self.artifacts):
            raise ValueError("artifact_count must match artifacts")
        if self.existing_artifact_count != existing_count:
            raise ValueError("existing_artifact_count must match artifacts")
        if self.total_existing_size_bytes != total_size:
            raise ValueError("total_existing_size_bytes must match artifacts")
        return self

    def to_json_ready(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "session_dir": self.session_dir,
            "result_kind": self.result_kind,
            "status": self.status,
            "dry_run_only": self.dry_run_only,
            "deletion_performed": self.deletion_performed,
            "artifact_count": self.artifact_count,
            "existing_artifact_count": self.existing_artifact_count,
            "total_existing_size_bytes": self.total_existing_size_bytes,
            "artifacts": [artifact.to_json_ready() for artifact in self.artifacts],
        }


def _path_is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _require_path_inside(path: Path, root: Path, message: str) -> None:
    if not _path_is_relative_to(path, root):
        raise ValueError(message)


def _archive_root_is_network_or_device_path(archive_root: str | Path) -> bool:
    root_text = "".join(
        "\\" if character == "/" else character for character in str(archive_root)
    )
    return root_text.startswith("\\\\")


def _resolve_existing_archive_root(archive_root: str | Path) -> Path:
    if isinstance(archive_root, str) and archive_root != archive_root.strip():
        raise ValueError("archive_root must be an explicit existing directory")
    if isinstance(archive_root, str) and not archive_root:
        raise ValueError("archive_root must be an explicit existing directory")
    if _archive_root_is_network_or_device_path(archive_root):
        raise ValueError("archive_root must be a local directory")
    candidate_root = Path(archive_root)
    if (
        not candidate_root.exists()
        or not candidate_root.is_dir()
        or candidate_root.is_symlink()
    ):
        raise ValueError("archive_root must be an explicit existing directory")
    return candidate_root.resolve(strict=False)


def _resolve_local_session_dir(resolved_archive_root: Path, session_id: str) -> Path:
    session_dir = resolved_archive_root / session_id
    if session_dir.is_symlink():
        raise ValueError("session directory must not be a symlink")
    if session_dir.exists() and not session_dir.is_dir():
        raise ValueError("session directory must be a directory")
    resolved_session_dir = session_dir.resolve(strict=False)
    _require_path_inside(
        resolved_session_dir,
        resolved_archive_root,
        "session directory must stay inside the archive root",
    )
    return resolved_session_dir


def _local_artifact_from_path(
    *,
    resolved_archive_root: Path,
    resolved_session_dir: Path,
    kind: ArchiveArtifactKind,
    filename: str,
) -> ArchiveDeleteDryRunLocalArtifact:
    artifact_path = resolved_session_dir / filename
    if artifact_path.is_symlink():
        raise ValueError("archive artifact must not be a symlink")

    resolved_artifact_path = artifact_path.resolve(strict=False)
    _require_path_inside(
        resolved_artifact_path,
        resolved_archive_root,
        "archive artifact path must stay inside the archive root",
    )
    _require_path_inside(
        resolved_artifact_path,
        resolved_session_dir,
        "archive artifact path must stay inside the session directory",
    )

    if not artifact_path.exists():
        return ArchiveDeleteDryRunLocalArtifact(
            kind=kind,
            filename=filename,
            exists=False,
        )
    if not artifact_path.is_file():
        raise ValueError("archive artifact must be a file")
    return ArchiveDeleteDryRunLocalArtifact(
        kind=kind,
        filename=filename,
        exists=True,
        size_bytes=artifact_path.stat().st_size,
    )


def build_archive_delete_dry_run_local_result(
    archive_root: str | Path,
    session_id: str,
) -> ArchiveDeleteDryRunLocalResult:
    try:
        safe_session_id = _validate_safe_session_id(session_id)
        resolved_archive_root = _resolve_existing_archive_root(archive_root)
        resolved_session_dir = _resolve_local_session_dir(
            resolved_archive_root,
            safe_session_id,
        )
        artifacts = tuple(
            _local_artifact_from_path(
                resolved_archive_root=resolved_archive_root,
                resolved_session_dir=resolved_session_dir,
                kind=kind,
                filename=filename,
            )
            for kind, filename in ARCHIVE_ARTIFACT_FILENAMES_BY_KIND.items()
        )
        return ArchiveDeleteDryRunLocalResult(
            session_id=safe_session_id,
            session_dir=safe_session_id,
            artifact_count=len(artifacts),
            existing_artifact_count=sum(1 for artifact in artifacts if artifact.exists),
            total_existing_size_bytes=sum(
                artifact.size_bytes or 0 for artifact in artifacts if artifact.exists
            ),
            artifacts=artifacts,
        )
    except (OSError, RuntimeError, TypeError, ValidationError, ValueError):
        raise ValueError(ARCHIVE_DELETE_DRY_RUN_LOCAL_ERROR) from None


def export_archive_delete_dry_run_local_result(
    result: ArchiveDeleteDryRunLocalResult,
) -> dict[str, object]:
    if type(result) is not ArchiveDeleteDryRunLocalResult:
        raise TypeError("result must be an ArchiveDeleteDryRunLocalResult")
    safe_result = ArchiveDeleteDryRunLocalResult.model_validate(result.model_dump())
    return safe_result.to_json_ready()
