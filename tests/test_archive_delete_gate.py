from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from async_scholar.archive_delete_audit import build_archive_delete_audit_event
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
    export_archive_delete_final_gate,
    summarize_archive_delete_final_gate,
)
from async_scholar.archive_delete_review import (
    ARCHIVE_DELETE_REVIEW_SNAPSHOT_KIND,
    ARCHIVE_DELETE_REVIEW_STATUS,
    ArchiveDeleteReviewArtifact,
    ArchiveDeleteReviewSnapshot,
    build_archive_delete_review_snapshot,
)


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


def _snapshot() -> ArchiveDeleteReviewSnapshot:
    response = build_archive_delete_confirmation_response(
        _preview(),
        ARCHIVE_DELETE_CONFIRMATION_PHRASE,
    )
    request = build_archive_delete_dry_run_request(response)
    result = build_archive_delete_dry_run_result(request)
    event = build_archive_delete_audit_event(result)
    return build_archive_delete_review_snapshot(event)


def _gate() -> ArchiveDeleteFinalGate:
    return build_archive_delete_final_gate(_snapshot())


def test_build_gate_from_actual_snapshot_copies_only_safe_metadata() -> None:
    snapshot = _snapshot()

    gate = build_archive_delete_final_gate(snapshot)

    assert gate.session_id == "session-001"
    assert gate.gate_kind == ARCHIVE_DELETE_GATE_KIND
    assert gate.status == ARCHIVE_DELETE_GATE_STATUS
    assert gate.audit_scope == "metadata_only"
    assert gate.requires_confirmation is True
    assert gate.review_completed is True
    assert gate.dry_run_only is True
    assert gate.deletion_performed is False
    assert gate.execution_allowed is False
    assert gate.artifact_count == 3
    assert gate.artifacts == (
        ArchiveDeleteGateArtifact(
            kind="transcript_jsonl",
            filename="transcript.jsonl",
        ),
        ArchiveDeleteGateArtifact(
            kind="events_jsonl",
            filename="events.jsonl",
        ),
        ArchiveDeleteGateArtifact(
            kind="reviewer_markdown",
            filename="reviewer.md",
        ),
    )
    assert gate.artifacts[0] is not snapshot.artifacts[0]
    assert gate.artifacts[0].action == "would_delete"
    assert gate.artifacts[0].status == "not_deleted"
    assert set(gate.model_dump()) == {
        "session_id",
        "gate_kind",
        "status",
        "audit_scope",
        "requires_confirmation",
        "review_completed",
        "dry_run_only",
        "deletion_performed",
        "execution_allowed",
        "artifact_count",
        "artifacts",
    }


def test_builder_rejects_non_snapshot_inputs() -> None:
    class SnapshotSubclass(ArchiveDeleteReviewSnapshot):
        pass

    class DuckSnapshot:
        session_id = "session-001"
        snapshot_kind = ARCHIVE_DELETE_REVIEW_SNAPSHOT_KIND
        status = ARCHIVE_DELETE_REVIEW_STATUS
        audit_scope = "metadata_only"
        requires_confirmation = True
        confirmation_verified = True
        dry_run_only = True
        deletion_performed = False
        artifact_count = 1
        artifacts = (
            ArchiveDeleteReviewArtifact(
                kind="transcript_jsonl",
                filename="transcript.jsonl",
            ),
        )

    subclassed_snapshot = SnapshotSubclass.model_validate(_snapshot().model_dump())

    for value in (
        None,
        {},
        _snapshot().model_dump(),
        [],
        "snapshot",
        b"snapshot",
        object(),
        DuckSnapshot(),
        subclassed_snapshot,
    ):
        with pytest.raises(TypeError):
            build_archive_delete_final_gate(value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "tampered_snapshot",
    [
        ArchiveDeleteReviewSnapshot.model_construct(
            session_id="session..001",
            snapshot_kind=ARCHIVE_DELETE_REVIEW_SNAPSHOT_KIND,
            status=ARCHIVE_DELETE_REVIEW_STATUS,
            audit_scope="metadata_only",
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteReviewArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteReviewSnapshot.model_construct(
            session_id="session-001",
            snapshot_kind=ARCHIVE_DELETE_REVIEW_SNAPSHOT_KIND,
            status=ARCHIVE_DELETE_REVIEW_STATUS,
            audit_scope="metadata_only",
            requires_confirmation=False,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteReviewArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteReviewSnapshot.model_construct(
            session_id="session-001",
            snapshot_kind=ARCHIVE_DELETE_REVIEW_SNAPSHOT_KIND,
            status=ARCHIVE_DELETE_REVIEW_STATUS,
            audit_scope="metadata_only",
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=False,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteReviewArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteReviewSnapshot.model_construct(
            session_id="session-001",
            snapshot_kind=ARCHIVE_DELETE_REVIEW_SNAPSHOT_KIND,
            status=ARCHIVE_DELETE_REVIEW_STATUS,
            audit_scope="metadata_only",
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=True,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteReviewArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteReviewSnapshot.model_construct(
            session_id="session-001",
            snapshot_kind="archive_delete",
            status=ARCHIVE_DELETE_REVIEW_STATUS,
            audit_scope="metadata_only",
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteReviewArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteReviewSnapshot.model_construct(
            session_id="session-001",
            snapshot_kind=ARCHIVE_DELETE_REVIEW_SNAPSHOT_KIND,
            status="deleted",
            audit_scope="metadata_only",
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteReviewArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteReviewSnapshot.model_construct(
            session_id="session-001",
            snapshot_kind=ARCHIVE_DELETE_REVIEW_SNAPSHOT_KIND,
            status=ARCHIVE_DELETE_REVIEW_STATUS,
            audit_scope="full_contents",
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteReviewArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteReviewSnapshot.model_construct(
            session_id="session-001",
            snapshot_kind=ARCHIVE_DELETE_REVIEW_SNAPSHOT_KIND,
            status=ARCHIVE_DELETE_REVIEW_STATUS,
            audit_scope="metadata_only",
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=2,
            artifacts=(
                ArchiveDeleteReviewArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteReviewSnapshot.model_construct(
            session_id="session-001",
            snapshot_kind=ARCHIVE_DELETE_REVIEW_SNAPSHOT_KIND,
            status=ARCHIVE_DELETE_REVIEW_STATUS,
            audit_scope="metadata_only",
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteReviewArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteReviewSnapshot.model_construct(
            session_id="session-001",
            snapshot_kind=ARCHIVE_DELETE_REVIEW_SNAPSHOT_KIND,
            status=ARCHIVE_DELETE_REVIEW_STATUS,
            audit_scope="metadata_only",
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteReviewArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="C:\\Users\\student\\transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
    ],
)
def test_builder_revalidates_constructed_snapshots_before_copy(
    tampered_snapshot: ArchiveDeleteReviewSnapshot,
) -> None:
    with pytest.raises(ValidationError):
        build_archive_delete_final_gate(tampered_snapshot)


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
def test_gate_rejects_false_or_non_true_flags(
    field_name: str,
    value: object,
) -> None:
    data = _gate().model_dump()
    data[field_name] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteFinalGate(**data)


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
def test_gate_rejects_non_false_blocking_flags(
    field_name: str,
    value: object,
) -> None:
    data = _gate().model_dump()
    data[field_name] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteFinalGate(**data)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("gate_kind", ""),
        ("gate_kind", "archive_delete"),
        ("gate_kind", "archive_delete_review_snapshot"),
        ("status", ""),
        ("status", "pending"),
        ("status", "execution_allowed"),
        ("audit_scope", ""),
        ("audit_scope", "full_contents"),
        ("audit_scope", "private_paths"),
    ],
)
def test_gate_rejects_arbitrary_gate_kind_status_or_scope(
    field_name: str,
    value: str,
) -> None:
    data = _gate().model_dump()
    data[field_name] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteFinalGate(**data)


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
    data = ArchiveDeleteGateArtifact(
        kind="transcript_jsonl",
        filename="transcript.jsonl",
    ).model_dump()
    data[field_name] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteGateArtifact(**data)


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
def test_gate_rejects_unsafe_session_ids(session_id: str) -> None:
    data = _gate().model_dump()
    data["session_id"] = session_id

    with pytest.raises(ValidationError):
        ArchiveDeleteFinalGate(**data)


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
        ArchiveDeleteGateArtifact(kind=kind, filename=filename)


def test_gate_rejects_extra_fields_count_mismatch_empty_and_duplicates() -> None:
    gate = _gate()

    with pytest.raises(ValidationError):
        ArchiveDeleteFinalGate(**gate.model_dump(), extra="blocked")

    with pytest.raises(ValidationError):
        ArchiveDeleteGateArtifact(
            kind="transcript_jsonl",
            filename="transcript.jsonl",
            private_path="C:\\Users\\student\\secret.txt",
        )

    data = gate.model_dump()
    data["artifact_count"] = 2
    with pytest.raises(ValidationError):
        ArchiveDeleteFinalGate(**data)

    data = gate.model_dump()
    data["artifacts"] = []
    data["artifact_count"] = 0
    with pytest.raises(ValidationError):
        ArchiveDeleteFinalGate(**data)

    duplicate_artifact = {
        "kind": "transcript_jsonl",
        "filename": "transcript.jsonl",
        "action": "would_delete",
        "status": "not_deleted",
    }
    data = gate.model_dump()
    data["artifacts"] = [duplicate_artifact, duplicate_artifact]
    data["artifact_count"] = 2
    with pytest.raises(ValidationError):
        ArchiveDeleteFinalGate(**data)


def test_serialization_helpers_return_deterministic_json_ready_safe_data() -> None:
    gate = _gate()

    assert summarize_archive_delete_final_gate(gate) == {
        "session_id": "session-001",
        "gate_kind": "archive_delete_final_gate",
        "status": "execution_blocked",
        "audit_scope": "metadata_only",
        "requires_confirmation": True,
        "review_completed": True,
        "dry_run_only": True,
        "deletion_performed": False,
        "execution_allowed": False,
        "artifact_count": 3,
    }
    assert export_archive_delete_final_gate(gate) == {
        "session_id": "session-001",
        "gate_kind": "archive_delete_final_gate",
        "status": "execution_blocked",
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
        json.dumps(export_archive_delete_final_gate(gate))
    ) == export_archive_delete_final_gate(gate)

    exported_text = json.dumps(export_archive_delete_final_gate(gate))
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


def test_helpers_reject_non_gate_inputs() -> None:
    class GateSubclass(ArchiveDeleteFinalGate):
        pass

    subclassed_gate = GateSubclass.model_validate(_gate().model_dump())

    for value in (
        None,
        {},
        _gate().model_dump(),
        [],
        "gate",
        b"gate",
        object(),
        subclassed_gate,
    ):
        with pytest.raises(TypeError):
            summarize_archive_delete_final_gate(value)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            export_archive_delete_final_gate(value)  # type: ignore[arg-type]


def test_helpers_revalidate_constructed_gates_before_export() -> None:
    tampered_gate = ArchiveDeleteFinalGate.model_construct(
        session_id="session-001",
        gate_kind="archive_delete_final_gate",
        status="execution_blocked",
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
    )

    with pytest.raises(ValidationError):
        summarize_archive_delete_final_gate(tampered_gate)
    with pytest.raises(ValidationError):
        export_archive_delete_final_gate(tampered_gate)

    private_path_gate = ArchiveDeleteFinalGate.model_construct(
        session_id="session-001",
        gate_kind="archive_delete_final_gate",
        status="execution_blocked",
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
    )

    with pytest.raises(ValidationError):
        export_archive_delete_final_gate(private_path_gate)

    arbitrary_status_gate = ArchiveDeleteFinalGate.model_construct(
        session_id="session-001",
        gate_kind="archive_delete_final_gate",
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
    )

    with pytest.raises(ValidationError):
        export_archive_delete_final_gate(arbitrary_status_gate)

    arbitrary_action_gate = ArchiveDeleteFinalGate.model_construct(
        session_id="session-001",
        gate_kind="archive_delete_final_gate",
        status="execution_blocked",
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
    )

    with pytest.raises(ValidationError):
        export_archive_delete_final_gate(arbitrary_action_gate)


def test_models_are_immutable() -> None:
    gate = _gate()

    with pytest.raises(ValidationError):
        gate.session_id = "session-002"

    with pytest.raises(ValidationError):
        gate.artifacts[0].filename = "events.jsonl"


def test_source_has_no_execution_persistence_or_permission_behavior() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "async_scholar"
        / "archive_delete_gate.py"
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
