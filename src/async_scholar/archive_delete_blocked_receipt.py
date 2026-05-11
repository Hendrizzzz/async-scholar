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

from async_scholar.archive_delete_gate import (
    ArchiveDeleteFinalGate,
    ArchiveDeleteGateArtifact,
)

ARCHIVE_DELETE_BLOCKED_RECEIPT_KIND: Literal["archive_delete_blocked_receipt"] = (
    "archive_delete_blocked_receipt"
)
ARCHIVE_DELETE_BLOCKED_RECEIPT_STATUS: Literal["execution_not_allowed"] = (
    "execution_not_allowed"
)
ARCHIVE_DELETE_BLOCK_REASON: Literal["final_gate_blocks_execution"] = (
    "final_gate_blocks_execution"
)
ARCHIVE_DELETE_BLOCKED_RECEIPT_AUDIT_SCOPE: Literal["metadata_only"] = "metadata_only"
ARCHIVE_DELETE_BLOCKED_RECEIPT_ARTIFACT_ACTION: Literal["would_delete"] = "would_delete"
ARCHIVE_DELETE_BLOCKED_RECEIPT_ARTIFACT_STATUS: Literal["not_deleted"] = "not_deleted"

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


class ArchiveDeleteBlockedReceiptArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: StrictStr
    filename: StrictStr
    action: Literal["would_delete"] = ARCHIVE_DELETE_BLOCKED_RECEIPT_ARTIFACT_ACTION
    status: Literal["not_deleted"] = ARCHIVE_DELETE_BLOCKED_RECEIPT_ARTIFACT_STATUS

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
    def _validate_gate_artifact(self) -> ArchiveDeleteBlockedReceiptArtifact:
        ArchiveDeleteGateArtifact(
            kind=self.kind,
            filename=self.filename,
            action=self.action,
            status=self.status,
        )
        return self


class ArchiveDeleteBlockedReceipt(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: StrictStr
    receipt_kind: Literal["archive_delete_blocked_receipt"] = (
        ARCHIVE_DELETE_BLOCKED_RECEIPT_KIND
    )
    status: Literal["execution_not_allowed"] = ARCHIVE_DELETE_BLOCKED_RECEIPT_STATUS
    block_reason: Literal["final_gate_blocks_execution"] = ARCHIVE_DELETE_BLOCK_REASON
    audit_scope: Literal["metadata_only"] = ARCHIVE_DELETE_BLOCKED_RECEIPT_AUDIT_SCOPE
    requires_confirmation: bool = True
    review_completed: bool = True
    dry_run_only: bool = True
    deletion_performed: bool = False
    execution_allowed: bool = False
    artifact_count: StrictInt = Field(ge=1)
    artifacts: tuple[ArchiveDeleteBlockedReceiptArtifact, ...] = Field(min_length=1)

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
        return _validate_true(value, label="blocked receipt flag")

    @field_validator("deletion_performed", "execution_allowed", mode="before")
    @classmethod
    def _validate_false_flags(cls, value: object) -> object:
        return _validate_false(value, label="blocked receipt blocking flag")

    @field_validator("artifact_count", mode="before")
    @classmethod
    def _validate_artifact_count(cls, value: object) -> object:
        if isinstance(value, bool):
            raise ValueError("artifact_count must be an integer")
        return value

    @model_validator(mode="after")
    def _validate_artifacts(self) -> ArchiveDeleteBlockedReceipt:
        if self.artifact_count != len(self.artifacts):
            raise ValueError("artifact_count must match artifacts")
        pairs = {(artifact.kind, artifact.filename) for artifact in self.artifacts}
        if len(pairs) != len(self.artifacts):
            raise ValueError("artifacts must be unique")
        return self


def build_archive_delete_blocked_receipt(
    gate: ArchiveDeleteFinalGate,
) -> ArchiveDeleteBlockedReceipt:
    safe_gate = _ensure_gate(gate)
    artifacts = tuple(
        ArchiveDeleteBlockedReceiptArtifact(
            kind=artifact.kind,
            filename=artifact.filename,
            action=artifact.action,
            status=artifact.status,
        )
        for artifact in safe_gate.artifacts
    )
    return ArchiveDeleteBlockedReceipt(
        session_id=safe_gate.session_id,
        artifact_count=safe_gate.artifact_count,
        artifacts=artifacts,
    )


def summarize_archive_delete_blocked_receipt(
    receipt: ArchiveDeleteBlockedReceipt,
) -> dict[str, object]:
    safe_receipt = _ensure_receipt(receipt)
    return {
        "session_id": safe_receipt.session_id,
        "receipt_kind": safe_receipt.receipt_kind,
        "status": safe_receipt.status,
        "block_reason": safe_receipt.block_reason,
        "audit_scope": safe_receipt.audit_scope,
        "requires_confirmation": safe_receipt.requires_confirmation,
        "review_completed": safe_receipt.review_completed,
        "dry_run_only": safe_receipt.dry_run_only,
        "deletion_performed": safe_receipt.deletion_performed,
        "execution_allowed": safe_receipt.execution_allowed,
        "artifact_count": safe_receipt.artifact_count,
    }


def export_archive_delete_blocked_receipt(
    receipt: ArchiveDeleteBlockedReceipt,
) -> dict[str, Any]:
    safe_receipt = _ensure_receipt(receipt)
    return {
        "session_id": safe_receipt.session_id,
        "receipt_kind": safe_receipt.receipt_kind,
        "status": safe_receipt.status,
        "block_reason": safe_receipt.block_reason,
        "audit_scope": safe_receipt.audit_scope,
        "requires_confirmation": safe_receipt.requires_confirmation,
        "review_completed": safe_receipt.review_completed,
        "dry_run_only": safe_receipt.dry_run_only,
        "deletion_performed": safe_receipt.deletion_performed,
        "execution_allowed": safe_receipt.execution_allowed,
        "artifact_count": safe_receipt.artifact_count,
        "artifacts": [
            {
                "kind": artifact.kind,
                "filename": artifact.filename,
                "action": artifact.action,
                "status": artifact.status,
            }
            for artifact in safe_receipt.artifacts
        ],
    }


def _ensure_gate(gate: ArchiveDeleteFinalGate) -> ArchiveDeleteFinalGate:
    if type(gate) is not ArchiveDeleteFinalGate:
        raise TypeError("gate must be an ArchiveDeleteFinalGate")
    return ArchiveDeleteFinalGate.model_validate(gate.model_dump())


def _ensure_receipt(
    receipt: ArchiveDeleteBlockedReceipt,
) -> ArchiveDeleteBlockedReceipt:
    if type(receipt) is not ArchiveDeleteBlockedReceipt:
        raise TypeError("receipt must be an ArchiveDeleteBlockedReceipt")
    return ArchiveDeleteBlockedReceipt.model_validate(receipt.model_dump())
