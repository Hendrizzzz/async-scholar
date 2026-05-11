from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from async_scholar.archive_delete_audit import build_archive_delete_audit_event
from async_scholar.archive_delete_blocked_receipt import (
    ARCHIVE_DELETE_BLOCK_REASON,
    ARCHIVE_DELETE_BLOCKED_RECEIPT_ARTIFACT_ACTION,
    ARCHIVE_DELETE_BLOCKED_RECEIPT_ARTIFACT_STATUS,
    ARCHIVE_DELETE_BLOCKED_RECEIPT_AUDIT_SCOPE,
    ARCHIVE_DELETE_BLOCKED_RECEIPT_KIND,
    ARCHIVE_DELETE_BLOCKED_RECEIPT_STATUS,
    ArchiveDeleteBlockedReceipt,
    ArchiveDeleteBlockedReceiptArtifact,
    build_archive_delete_blocked_receipt,
    export_archive_delete_blocked_receipt,
    summarize_archive_delete_blocked_receipt,
)
from async_scholar.archive_delete_confirmation import (
    ARCHIVE_DELETE_CONFIRMATION_PHRASE,
    ArchiveDeleteConfirmationArtifact,
    ArchiveDeleteConfirmationPreview,
)
from async_scholar.archive_delete_confirmation_response import (
    build_archive_delete_confirmation_response,
)
from async_scholar.archive_delete_dry_run import build_archive_delete_dry_run_request
from async_scholar.archive_delete_dry_run_result import (
    build_archive_delete_dry_run_result,
)
from async_scholar.archive_delete_gate import (
    ARCHIVE_DELETE_GATE_KIND,
    ARCHIVE_DELETE_GATE_STATUS,
    ArchiveDeleteFinalGate,
    ArchiveDeleteGateArtifact,
    build_archive_delete_final_gate,
)
from async_scholar.archive_delete_review import build_archive_delete_review_snapshot


def _preview() -> ArchiveDeleteConfirmationPreview:
    return ArchiveDeleteConfirmationPreview(
        session_id="session-001",
        artifact_count=3,
        artifacts=(
            ArchiveDeleteConfirmationArtifact(
                kind="transcript_jsonl",
                filename="transcript.jsonl",
            ),
            ArchiveDeleteConfirmationArtifact(
                kind="events_jsonl",
                filename="events.jsonl",
            ),
            ArchiveDeleteConfirmationArtifact(
                kind="reviewer_markdown",
                filename="reviewer.md",
            ),
        ),
    )


def _gate() -> ArchiveDeleteFinalGate:
    response = build_archive_delete_confirmation_response(
        _preview(),
        ARCHIVE_DELETE_CONFIRMATION_PHRASE,
    )
    request = build_archive_delete_dry_run_request(response)
    result = build_archive_delete_dry_run_result(request)
    event = build_archive_delete_audit_event(result)
    snapshot = build_archive_delete_review_snapshot(event)
    return build_archive_delete_final_gate(snapshot)


def _receipt() -> ArchiveDeleteBlockedReceipt:
    return build_archive_delete_blocked_receipt(_gate())


def test_build_receipt_from_actual_gate_copies_only_safe_metadata() -> None:
    gate = _gate()

    receipt = build_archive_delete_blocked_receipt(gate)

    assert receipt.session_id == "session-001"
    assert receipt.receipt_kind == ARCHIVE_DELETE_BLOCKED_RECEIPT_KIND
    assert receipt.status == ARCHIVE_DELETE_BLOCKED_RECEIPT_STATUS
    assert receipt.block_reason == ARCHIVE_DELETE_BLOCK_REASON
    assert receipt.audit_scope == ARCHIVE_DELETE_BLOCKED_RECEIPT_AUDIT_SCOPE
    assert receipt.requires_confirmation is True
    assert receipt.review_completed is True
    assert receipt.dry_run_only is True
    assert receipt.deletion_performed is False
    assert receipt.execution_allowed is False
    assert receipt.artifact_count == 3
    assert receipt.artifacts == (
        ArchiveDeleteBlockedReceiptArtifact(
            kind="transcript_jsonl",
            filename="transcript.jsonl",
        ),
        ArchiveDeleteBlockedReceiptArtifact(
            kind="events_jsonl",
            filename="events.jsonl",
        ),
        ArchiveDeleteBlockedReceiptArtifact(
            kind="reviewer_markdown",
            filename="reviewer.md",
        ),
    )
    assert receipt.artifacts[0] is not gate.artifacts[0]
    assert receipt.artifacts[0].action == ARCHIVE_DELETE_BLOCKED_RECEIPT_ARTIFACT_ACTION
    assert receipt.artifacts[0].status == ARCHIVE_DELETE_BLOCKED_RECEIPT_ARTIFACT_STATUS
    assert set(receipt.model_dump()) == {
        "session_id",
        "receipt_kind",
        "status",
        "block_reason",
        "audit_scope",
        "requires_confirmation",
        "review_completed",
        "dry_run_only",
        "deletion_performed",
        "execution_allowed",
        "artifact_count",
        "artifacts",
    }


def test_builder_rejects_non_gate_inputs() -> None:
    class GateSubclass(ArchiveDeleteFinalGate):
        pass

    class DuckGate:
        session_id = "session-001"
        gate_kind = ARCHIVE_DELETE_GATE_KIND
        status = ARCHIVE_DELETE_GATE_STATUS
        audit_scope = "metadata_only"
        requires_confirmation = True
        review_completed = True
        dry_run_only = True
        deletion_performed = False
        execution_allowed = False
        artifact_count = 1
        artifacts = (
            ArchiveDeleteGateArtifact(
                kind="transcript_jsonl",
                filename="transcript.jsonl",
            ),
        )

    subclassed_gate = GateSubclass.model_validate(_gate().model_dump())

    for value in (
        None,
        {},
        _gate().model_dump(),
        [],
        "gate",
        b"gate",
        object(),
        DuckGate(),
        subclassed_gate,
    ):
        with pytest.raises(TypeError):
            build_archive_delete_blocked_receipt(value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "tampered_gate",
    [
        ArchiveDeleteFinalGate.model_construct(
            session_id="session..001",
            gate_kind=ARCHIVE_DELETE_GATE_KIND,
            status=ARCHIVE_DELETE_GATE_STATUS,
            audit_scope="metadata_only",
            requires_confirmation=True,
            review_completed=True,
            dry_run_only=True,
            deletion_performed=False,
            execution_allowed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteGateArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteFinalGate.model_construct(
            session_id="session-001",
            gate_kind=ARCHIVE_DELETE_GATE_KIND,
            status=ARCHIVE_DELETE_GATE_STATUS,
            audit_scope="metadata_only",
            requires_confirmation=False,
            review_completed=True,
            dry_run_only=True,
            deletion_performed=False,
            execution_allowed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteGateArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteFinalGate.model_construct(
            session_id="session-001",
            gate_kind=ARCHIVE_DELETE_GATE_KIND,
            status=ARCHIVE_DELETE_GATE_STATUS,
            audit_scope="metadata_only",
            requires_confirmation=True,
            review_completed=True,
            dry_run_only=False,
            deletion_performed=False,
            execution_allowed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteGateArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteFinalGate.model_construct(
            session_id="session-001",
            gate_kind=ARCHIVE_DELETE_GATE_KIND,
            status=ARCHIVE_DELETE_GATE_STATUS,
            audit_scope="metadata_only",
            requires_confirmation=True,
            review_completed=True,
            dry_run_only=True,
            deletion_performed=True,
            execution_allowed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteGateArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteFinalGate.model_construct(
            session_id="session-001",
            gate_kind=ARCHIVE_DELETE_GATE_KIND,
            status=ARCHIVE_DELETE_GATE_STATUS,
            audit_scope="metadata_only",
            requires_confirmation=True,
            review_completed=True,
            dry_run_only=True,
            deletion_performed=False,
            execution_allowed=True,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteGateArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteFinalGate.model_construct(
            session_id="session-001",
            gate_kind="archive_delete",
            status=ARCHIVE_DELETE_GATE_STATUS,
            audit_scope="metadata_only",
            requires_confirmation=True,
            review_completed=True,
            dry_run_only=True,
            deletion_performed=False,
            execution_allowed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteGateArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteFinalGate.model_construct(
            session_id="session-001",
            gate_kind=ARCHIVE_DELETE_GATE_KIND,
            status="execution_allowed",
            audit_scope="metadata_only",
            requires_confirmation=True,
            review_completed=True,
            dry_run_only=True,
            deletion_performed=False,
            execution_allowed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteGateArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteFinalGate.model_construct(
            session_id="session-001",
            gate_kind=ARCHIVE_DELETE_GATE_KIND,
            status=ARCHIVE_DELETE_GATE_STATUS,
            audit_scope="full_contents",
            requires_confirmation=True,
            review_completed=True,
            dry_run_only=True,
            deletion_performed=False,
            execution_allowed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteGateArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteFinalGate.model_construct(
            session_id="session-001",
            gate_kind=ARCHIVE_DELETE_GATE_KIND,
            status=ARCHIVE_DELETE_GATE_STATUS,
            audit_scope="metadata_only",
            requires_confirmation=True,
            review_completed=True,
            dry_run_only=True,
            deletion_performed=False,
            execution_allowed=False,
            artifact_count=2,
            artifacts=(
                ArchiveDeleteGateArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteFinalGate.model_construct(
            session_id="session-001",
            gate_kind=ARCHIVE_DELETE_GATE_KIND,
            status=ARCHIVE_DELETE_GATE_STATUS,
            audit_scope="metadata_only",
            requires_confirmation=True,
            review_completed=True,
            dry_run_only=True,
            deletion_performed=False,
            execution_allowed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteGateArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteFinalGate.model_construct(
            session_id="session-001",
            gate_kind=ARCHIVE_DELETE_GATE_KIND,
            status=ARCHIVE_DELETE_GATE_STATUS,
            audit_scope="metadata_only",
            requires_confirmation=True,
            review_completed=True,
            dry_run_only=True,
            deletion_performed=False,
            execution_allowed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteGateArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="C:\\Users\\student\\transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
    ],
)
def test_builder_revalidates_constructed_gates_before_copy(
    tampered_gate: ArchiveDeleteFinalGate,
) -> None:
    with pytest.raises(ValidationError):
        build_archive_delete_blocked_receipt(tampered_gate)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("requires_confirmation", False),
        ("requires_confirmation", 1),
        ("requires_confirmation", "true"),
        ("review_completed", False),
        ("review_completed", 1),
        ("review_completed", "true"),
        ("dry_run_only", False),
        ("dry_run_only", 1),
        ("dry_run_only", "true"),
    ],
)
def test_receipt_rejects_false_or_non_true_flags(
    field_name: str,
    value: object,
) -> None:
    data = _receipt().model_dump()
    data[field_name] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteBlockedReceipt(**data)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("deletion_performed", True),
        ("deletion_performed", 0),
        ("deletion_performed", 1),
        ("deletion_performed", "false"),
        ("deletion_performed", None),
        ("execution_allowed", True),
        ("execution_allowed", 0),
        ("execution_allowed", 1),
        ("execution_allowed", "false"),
        ("execution_allowed", None),
    ],
)
def test_receipt_rejects_non_false_blocking_flags(
    field_name: str,
    value: object,
) -> None:
    data = _receipt().model_dump()
    data[field_name] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteBlockedReceipt(**data)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("receipt_kind", ""),
        ("receipt_kind", "archive_delete"),
        ("receipt_kind", "archive_delete_final_gate"),
        ("status", ""),
        ("status", "pending"),
        ("status", "execution_allowed"),
        ("block_reason", ""),
        ("block_reason", "user_confirmed"),
        ("block_reason", "delete_permitted"),
        ("audit_scope", ""),
        ("audit_scope", "full_contents"),
        ("audit_scope", "private_paths"),
    ],
)
def test_receipt_rejects_arbitrary_receipt_status_reason_or_scope(
    field_name: str,
    value: str,
) -> None:
    data = _receipt().model_dump()
    data[field_name] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteBlockedReceipt(**data)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("action", ""),
        ("action", "delete"),
        ("action", "deleted"),
        ("status", ""),
        ("status", "pending"),
        ("status", "deleted"),
    ],
)
def test_artifact_rejects_arbitrary_action_or_status(
    field_name: str,
    value: str,
) -> None:
    data = ArchiveDeleteBlockedReceiptArtifact(
        kind="transcript_jsonl",
        filename="transcript.jsonl",
    ).model_dump()
    data[field_name] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteBlockedReceiptArtifact(**data)


@pytest.mark.parametrize(
    "session_id",
    [
        "",
        " ",
        " session-001",
        "session-001 ",
        "session..001",
        "../session-001",
        "session/001",
        "session\\001",
        "C:\\Users\\student\\session-001",
        "\\\\server\\share\\session-001",
        "https://example.test/session-001",
        "session-\n001",
    ],
)
def test_receipt_rejects_unsafe_session_ids(session_id: str) -> None:
    data = _receipt().model_dump()
    data["session_id"] = session_id

    with pytest.raises(ValidationError):
        ArchiveDeleteBlockedReceipt(**data)


@pytest.mark.parametrize(
    ("kind", "filename"),
    [
        ("unknown", "transcript.jsonl"),
        ("transcript_jsonl", "unknown.txt"),
        ("transcript_jsonl", "events.jsonl"),
        ("transcript_jsonl", "../transcript.jsonl"),
        ("transcript_jsonl", "session/transcript.jsonl"),
        ("transcript_jsonl", "session\\transcript.jsonl"),
        ("transcript_jsonl", "C:\\Users\\student\\transcript.jsonl"),
        ("transcript_jsonl", "\\\\server\\share\\transcript.jsonl"),
        ("transcript_jsonl", "https://example.test/transcript.jsonl"),
        ("transcript_jsonl", "transcript\n.jsonl"),
    ],
)
def test_artifact_rejects_unsafe_or_mismatched_metadata(
    kind: str,
    filename: str,
) -> None:
    with pytest.raises(ValidationError):
        ArchiveDeleteBlockedReceiptArtifact(kind=kind, filename=filename)


def test_receipt_rejects_extra_fields_count_mismatch_empty_and_duplicates() -> None:
    receipt = _receipt()

    with pytest.raises(ValidationError):
        ArchiveDeleteBlockedReceipt(**receipt.model_dump(), extra="blocked")

    with pytest.raises(ValidationError):
        ArchiveDeleteBlockedReceiptArtifact(
            kind="transcript_jsonl",
            filename="transcript.jsonl",
            private_path="C:\\Users\\student\\secret.txt",
        )

    data = receipt.model_dump()
    data["artifact_count"] = 2
    with pytest.raises(ValidationError):
        ArchiveDeleteBlockedReceipt(**data)

    data = receipt.model_dump()
    data["artifacts"] = []
    data["artifact_count"] = 0
    with pytest.raises(ValidationError):
        ArchiveDeleteBlockedReceipt(**data)

    duplicate_artifact = {
        "kind": "transcript_jsonl",
        "filename": "transcript.jsonl",
        "action": "would_delete",
        "status": "not_deleted",
    }
    data = receipt.model_dump()
    data["artifacts"] = [duplicate_artifact, duplicate_artifact]
    data["artifact_count"] = 2
    with pytest.raises(ValidationError):
        ArchiveDeleteBlockedReceipt(**data)


def test_serialization_helpers_return_deterministic_json_ready_safe_data() -> None:
    receipt = _receipt()

    assert summarize_archive_delete_blocked_receipt(receipt) == {
        "session_id": "session-001",
        "receipt_kind": "archive_delete_blocked_receipt",
        "status": "execution_not_allowed",
        "block_reason": "final_gate_blocks_execution",
        "audit_scope": "metadata_only",
        "requires_confirmation": True,
        "review_completed": True,
        "dry_run_only": True,
        "deletion_performed": False,
        "execution_allowed": False,
        "artifact_count": 3,
    }
    assert export_archive_delete_blocked_receipt(receipt) == {
        "session_id": "session-001",
        "receipt_kind": "archive_delete_blocked_receipt",
        "status": "execution_not_allowed",
        "block_reason": "final_gate_blocks_execution",
        "audit_scope": "metadata_only",
        "requires_confirmation": True,
        "review_completed": True,
        "dry_run_only": True,
        "deletion_performed": False,
        "execution_allowed": False,
        "artifact_count": 3,
        "artifacts": [
            {
                "kind": "transcript_jsonl",
                "filename": "transcript.jsonl",
                "action": "would_delete",
                "status": "not_deleted",
            },
            {
                "kind": "events_jsonl",
                "filename": "events.jsonl",
                "action": "would_delete",
                "status": "not_deleted",
            },
            {
                "kind": "reviewer_markdown",
                "filename": "reviewer.md",
                "action": "would_delete",
                "status": "not_deleted",
            },
        ],
    }
    assert json.loads(
        json.dumps(export_archive_delete_blocked_receipt(receipt))
    ) == export_archive_delete_blocked_receipt(receipt)

    exported_text = json.dumps(export_archive_delete_blocked_receipt(receipt))
    for forbidden_text in (
        ARCHIVE_DELETE_CONFIRMATION_PHRASE,
        "wrong private phrase",
        "C:\\Users",
        "\\\\server\\share",
        "https://",
        "transcript text",
        "event contents",
        "alert payload",
        "auth",
        "browser",
        "secret",
        "model path",
        "worker",
        "timer",
        "sqlite",
        "scheduler",
        "deletion execution",
        "generated artifact contents",
        'execution_allowed": true',
        "delete permitted",
    ):
        assert forbidden_text not in exported_text


def test_helpers_reject_non_receipt_inputs() -> None:
    class ReceiptSubclass(ArchiveDeleteBlockedReceipt):
        pass

    subclassed_receipt = ReceiptSubclass.model_validate(_receipt().model_dump())

    for value in (
        None,
        {},
        _receipt().model_dump(),
        [],
        "receipt",
        b"receipt",
        object(),
        subclassed_receipt,
    ):
        with pytest.raises(TypeError):
            summarize_archive_delete_blocked_receipt(value)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            export_archive_delete_blocked_receipt(value)  # type: ignore[arg-type]


def test_helpers_revalidate_constructed_receipts_before_export() -> None:
    tampered_receipt = ArchiveDeleteBlockedReceipt.model_construct(
        session_id="session-001",
        receipt_kind="archive_delete_blocked_receipt",
        status="execution_not_allowed",
        block_reason="final_gate_blocks_execution",
        audit_scope="metadata_only",
        requires_confirmation=True,
        review_completed=True,
        dry_run_only=True,
        deletion_performed=False,
        execution_allowed=True,
        artifact_count=1,
        artifacts=(
            ArchiveDeleteBlockedReceiptArtifact.model_construct(
                kind="transcript_jsonl",
                filename="transcript.jsonl",
                action="would_delete",
                status="not_deleted",
            ),
        ),
    )

    with pytest.raises(ValidationError):
        summarize_archive_delete_blocked_receipt(tampered_receipt)
    with pytest.raises(ValidationError):
        export_archive_delete_blocked_receipt(tampered_receipt)

    private_path_receipt = ArchiveDeleteBlockedReceipt.model_construct(
        session_id="session-001",
        receipt_kind="archive_delete_blocked_receipt",
        status="execution_not_allowed",
        block_reason="final_gate_blocks_execution",
        audit_scope="metadata_only",
        requires_confirmation=True,
        review_completed=True,
        dry_run_only=True,
        deletion_performed=False,
        execution_allowed=False,
        artifact_count=1,
        artifacts=(
            ArchiveDeleteBlockedReceiptArtifact.model_construct(
                kind="transcript_jsonl",
                filename="C:\\Users\\student\\transcript.jsonl",
                action="would_delete",
                status="not_deleted",
            ),
        ),
    )

    with pytest.raises(ValidationError):
        export_archive_delete_blocked_receipt(private_path_receipt)

    arbitrary_reason_receipt = ArchiveDeleteBlockedReceipt.model_construct(
        session_id="session-001",
        receipt_kind="archive_delete_blocked_receipt",
        status="execution_not_allowed",
        block_reason="delete_permitted",
        audit_scope="metadata_only",
        requires_confirmation=True,
        review_completed=True,
        dry_run_only=True,
        deletion_performed=False,
        execution_allowed=False,
        artifact_count=1,
        artifacts=(
            ArchiveDeleteBlockedReceiptArtifact.model_construct(
                kind="transcript_jsonl",
                filename="transcript.jsonl",
                action="would_delete",
                status="not_deleted",
            ),
        ),
    )

    with pytest.raises(ValidationError):
        export_archive_delete_blocked_receipt(arbitrary_reason_receipt)

    arbitrary_action_receipt = ArchiveDeleteBlockedReceipt.model_construct(
        session_id="session-001",
        receipt_kind="archive_delete_blocked_receipt",
        status="execution_not_allowed",
        block_reason="final_gate_blocks_execution",
        audit_scope="metadata_only",
        requires_confirmation=True,
        review_completed=True,
        dry_run_only=True,
        deletion_performed=False,
        execution_allowed=False,
        artifact_count=1,
        artifacts=(
            ArchiveDeleteBlockedReceiptArtifact.model_construct(
                kind="transcript_jsonl",
                filename="transcript.jsonl",
                action="delete",
                status="not_deleted",
            ),
        ),
    )

    with pytest.raises(ValidationError):
        export_archive_delete_blocked_receipt(arbitrary_action_receipt)


def test_models_are_immutable() -> None:
    receipt = _receipt()

    with pytest.raises(ValidationError):
        receipt.session_id = "session-002"

    with pytest.raises(ValidationError):
        receipt.artifacts[0].filename = "events.jsonl"


def test_source_has_no_execution_persistence_or_permission_behavior() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "async_scholar"
        / "archive_delete_blocked_receipt.py"
    )
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "asyncio",
        "httpx",
        "os",
        "pathlib",
        "requests",
        "shutil",
        "socket",
        "sqlite3",
        "subprocess",
        "threading",
        "time",
        "urllib",
        "webbrowser",
    }
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(
                alias.name.split(".", maxsplit=1)[0] for alias in node.names
            )
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", maxsplit=1)[0])
    assert imported_roots.isdisjoint(forbidden_import_roots)

    forbidden_call_names = {
        "open",
        "unlink",
        "remove",
        "rmdir",
        "mkdir",
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
        "rename",
        "replace",
        "rmtree",
        "copy",
        "copyfile",
        "move",
        "system",
        "Popen",
        "run",
        "call",
        "check_call",
        "check_output",
        "Thread",
        "Timer",
        "sleep",
    }
    call_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.add(node.func.id)
            if isinstance(node.func, ast.Attribute):
                call_names.add(node.func.attr)
    assert call_names.isdisjoint(forbidden_call_names)

    forbidden_permission_text = (
        "execute_delete",
        "permit_delete",
        "allow_delete",
        "delete_allowed",
        "execution_allowed=True",
        "execution_allowed = True",
    )
    for text in forbidden_permission_text:
        assert text not in source
