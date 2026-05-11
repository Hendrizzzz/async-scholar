from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from async_scholar.archive_delete_audit import (
    ARCHIVE_DELETE_AUDIT_EVENT_KIND,
    ARCHIVE_DELETE_AUDIT_SCOPE,
    ARCHIVE_DELETE_AUDIT_STATUS,
    ArchiveDeleteAuditArtifact,
    ArchiveDeleteAuditEvent,
    build_archive_delete_audit_event,
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
from async_scholar.archive_delete_review import (
    ARCHIVE_DELETE_REVIEW_SNAPSHOT_KIND,
    ARCHIVE_DELETE_REVIEW_STATUS,
    ArchiveDeleteReviewArtifact,
    ArchiveDeleteReviewSnapshot,
    build_archive_delete_review_snapshot,
    export_archive_delete_review_snapshot,
    summarize_archive_delete_review_snapshot,
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


def _event() -> ArchiveDeleteAuditEvent:
    response = build_archive_delete_confirmation_response(
        _preview(),
        ARCHIVE_DELETE_CONFIRMATION_PHRASE,
    )
    request = build_archive_delete_dry_run_request(response)
    result = build_archive_delete_dry_run_result(request)
    return build_archive_delete_audit_event(result)


def _snapshot() -> ArchiveDeleteReviewSnapshot:
    return build_archive_delete_review_snapshot(_event())


def test_build_snapshot_from_actual_event_copies_only_safe_metadata() -> None:
    event = _event()

    snapshot = build_archive_delete_review_snapshot(event)

    assert snapshot.session_id == "session-001"
    assert snapshot.snapshot_kind == ARCHIVE_DELETE_REVIEW_SNAPSHOT_KIND
    assert snapshot.status == ARCHIVE_DELETE_REVIEW_STATUS
    assert snapshot.audit_scope == ARCHIVE_DELETE_AUDIT_SCOPE
    assert snapshot.requires_confirmation is True
    assert snapshot.confirmation_verified is True
    assert snapshot.dry_run_only is True
    assert snapshot.deletion_performed is False
    assert snapshot.artifact_count == 3
    assert snapshot.artifacts == (
        ArchiveDeleteReviewArtifact(
            kind="transcript_jsonl",
            filename="transcript.jsonl",
        ),
        ArchiveDeleteReviewArtifact(
            kind="events_jsonl",
            filename="events.jsonl",
        ),
        ArchiveDeleteReviewArtifact(
            kind="reviewer_markdown",
            filename="reviewer.md",
        ),
    )
    assert snapshot.artifacts[0] is not event.artifacts[0]
    assert snapshot.artifacts[0].action == "would_delete"
    assert snapshot.artifacts[0].status == "not_deleted"
    assert set(snapshot.model_dump()) == {
        "session_id",
        "snapshot_kind",
        "status",
        "audit_scope",
        "requires_confirmation",
        "confirmation_verified",
        "dry_run_only",
        "deletion_performed",
        "artifact_count",
        "artifacts",
    }


def test_builder_rejects_non_event_inputs() -> None:
    class EventSubclass(ArchiveDeleteAuditEvent):
        pass

    class DuckEvent:
        session_id = "session-001"
        event_kind = ARCHIVE_DELETE_AUDIT_EVENT_KIND
        status = ARCHIVE_DELETE_AUDIT_STATUS
        audit_scope = ARCHIVE_DELETE_AUDIT_SCOPE
        requires_confirmation = True
        confirmation_verified = True
        dry_run_only = True
        deletion_performed = False
        artifact_count = 1
        artifacts = (
            ArchiveDeleteAuditArtifact(
                kind="transcript_jsonl",
                filename="transcript.jsonl",
            ),
        )

    subclassed_event = EventSubclass.model_validate(_event().model_dump())

    for value in (
        None,
        {},
        _event().model_dump(),
        [],
        "event",
        b"event",
        object(),
        DuckEvent(),
        subclassed_event,
    ):
        with pytest.raises(TypeError):
            build_archive_delete_review_snapshot(value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "tampered_event",
    [
        ArchiveDeleteAuditEvent.model_construct(
            session_id="session..001",
            event_kind=ARCHIVE_DELETE_AUDIT_EVENT_KIND,
            status=ARCHIVE_DELETE_AUDIT_STATUS,
            audit_scope=ARCHIVE_DELETE_AUDIT_SCOPE,
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteAuditArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteAuditEvent.model_construct(
            session_id="session-001",
            event_kind=ARCHIVE_DELETE_AUDIT_EVENT_KIND,
            status=ARCHIVE_DELETE_AUDIT_STATUS,
            audit_scope=ARCHIVE_DELETE_AUDIT_SCOPE,
            requires_confirmation=False,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteAuditArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteAuditEvent.model_construct(
            session_id="session-001",
            event_kind=ARCHIVE_DELETE_AUDIT_EVENT_KIND,
            status=ARCHIVE_DELETE_AUDIT_STATUS,
            audit_scope=ARCHIVE_DELETE_AUDIT_SCOPE,
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=False,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteAuditArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteAuditEvent.model_construct(
            session_id="session-001",
            event_kind=ARCHIVE_DELETE_AUDIT_EVENT_KIND,
            status=ARCHIVE_DELETE_AUDIT_STATUS,
            audit_scope=ARCHIVE_DELETE_AUDIT_SCOPE,
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=True,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteAuditArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteAuditEvent.model_construct(
            session_id="session-001",
            event_kind="archive_delete",
            status=ARCHIVE_DELETE_AUDIT_STATUS,
            audit_scope=ARCHIVE_DELETE_AUDIT_SCOPE,
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteAuditArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteAuditEvent.model_construct(
            session_id="session-001",
            event_kind=ARCHIVE_DELETE_AUDIT_EVENT_KIND,
            status="deleted",
            audit_scope=ARCHIVE_DELETE_AUDIT_SCOPE,
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteAuditArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteAuditEvent.model_construct(
            session_id="session-001",
            event_kind=ARCHIVE_DELETE_AUDIT_EVENT_KIND,
            status=ARCHIVE_DELETE_AUDIT_STATUS,
            audit_scope="full_contents",
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteAuditArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteAuditEvent.model_construct(
            session_id="session-001",
            event_kind=ARCHIVE_DELETE_AUDIT_EVENT_KIND,
            status=ARCHIVE_DELETE_AUDIT_STATUS,
            audit_scope=ARCHIVE_DELETE_AUDIT_SCOPE,
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=2,
            artifacts=(
                ArchiveDeleteAuditArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteAuditEvent.model_construct(
            session_id="session-001",
            event_kind=ARCHIVE_DELETE_AUDIT_EVENT_KIND,
            status=ARCHIVE_DELETE_AUDIT_STATUS,
            audit_scope=ARCHIVE_DELETE_AUDIT_SCOPE,
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteAuditArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteAuditEvent.model_construct(
            session_id="session-001",
            event_kind=ARCHIVE_DELETE_AUDIT_EVENT_KIND,
            status=ARCHIVE_DELETE_AUDIT_STATUS,
            audit_scope=ARCHIVE_DELETE_AUDIT_SCOPE,
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteAuditArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="C:\\Users\\student\\transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
    ],
)
def test_builder_revalidates_constructed_events_before_copy(
    tampered_event: ArchiveDeleteAuditEvent,
) -> None:
    with pytest.raises(ValidationError):
        build_archive_delete_review_snapshot(tampered_event)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("requires_confirmation", False),
        ("requires_confirmation", 1),
        ("requires_confirmation", "true"),
        ("confirmation_verified", False),
        ("confirmation_verified", 1),
        ("confirmation_verified", "true"),
        ("dry_run_only", False),
        ("dry_run_only", 1),
        ("dry_run_only", "true"),
    ],
)
def test_snapshot_rejects_false_or_non_true_flags(
    field_name: str,
    value: object,
) -> None:
    data = _snapshot().model_dump()
    data[field_name] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteReviewSnapshot(**data)


@pytest.mark.parametrize("value", [True, 0, 1, "false", None])
def test_snapshot_rejects_non_false_deletion_performed(value: object) -> None:
    data = _snapshot().model_dump()
    data["deletion_performed"] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteReviewSnapshot(**data)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("snapshot_kind", ""),
        ("snapshot_kind", "archive_delete"),
        ("snapshot_kind", "archive_delete_dry_run_audit"),
        ("status", ""),
        ("status", "pending"),
        ("status", "deleted"),
        ("audit_scope", ""),
        ("audit_scope", "full_contents"),
        ("audit_scope", "private_paths"),
    ],
)
def test_snapshot_rejects_arbitrary_snapshot_kind_status_or_scope(
    field_name: str,
    value: str,
) -> None:
    data = _snapshot().model_dump()
    data[field_name] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteReviewSnapshot(**data)


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
    data = ArchiveDeleteReviewArtifact(
        kind="transcript_jsonl",
        filename="transcript.jsonl",
    ).model_dump()
    data[field_name] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteReviewArtifact(**data)


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
def test_snapshot_rejects_unsafe_session_ids(session_id: str) -> None:
    data = _snapshot().model_dump()
    data["session_id"] = session_id

    with pytest.raises(ValidationError):
        ArchiveDeleteReviewSnapshot(**data)


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
        ArchiveDeleteReviewArtifact(kind=kind, filename=filename)


def test_snapshot_rejects_extra_fields_count_mismatch_empty_and_duplicates() -> None:
    snapshot = _snapshot()

    with pytest.raises(ValidationError):
        ArchiveDeleteReviewSnapshot(**snapshot.model_dump(), extra="blocked")

    with pytest.raises(ValidationError):
        ArchiveDeleteReviewArtifact(
            kind="transcript_jsonl",
            filename="transcript.jsonl",
            private_path="C:\\Users\\student\\secret.txt",
        )

    data = snapshot.model_dump()
    data["artifact_count"] = 2
    with pytest.raises(ValidationError):
        ArchiveDeleteReviewSnapshot(**data)

    data = snapshot.model_dump()
    data["artifacts"] = []
    data["artifact_count"] = 0
    with pytest.raises(ValidationError):
        ArchiveDeleteReviewSnapshot(**data)

    duplicate_artifact = {
        "kind": "transcript_jsonl",
        "filename": "transcript.jsonl",
        "action": "would_delete",
        "status": "not_deleted",
    }
    data = snapshot.model_dump()
    data["artifacts"] = [duplicate_artifact, duplicate_artifact]
    data["artifact_count"] = 2
    with pytest.raises(ValidationError):
        ArchiveDeleteReviewSnapshot(**data)


def test_serialization_helpers_return_deterministic_json_ready_safe_data() -> None:
    snapshot = _snapshot()

    assert summarize_archive_delete_review_snapshot(snapshot) == {
        "session_id": "session-001",
        "snapshot_kind": "archive_delete_review_snapshot",
        "status": "review_snapshot_ready",
        "audit_scope": "metadata_only",
        "requires_confirmation": True,
        "confirmation_verified": True,
        "dry_run_only": True,
        "deletion_performed": False,
        "artifact_count": 3,
    }
    assert export_archive_delete_review_snapshot(snapshot) == {
        "session_id": "session-001",
        "snapshot_kind": "archive_delete_review_snapshot",
        "status": "review_snapshot_ready",
        "audit_scope": "metadata_only",
        "requires_confirmation": True,
        "confirmation_verified": True,
        "dry_run_only": True,
        "deletion_performed": False,
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
        json.dumps(export_archive_delete_review_snapshot(snapshot))
    ) == export_archive_delete_review_snapshot(snapshot)

    exported_text = json.dumps(export_archive_delete_review_snapshot(snapshot))
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
    ):
        assert forbidden_text not in exported_text


def test_helpers_reject_non_snapshot_inputs() -> None:
    class SnapshotSubclass(ArchiveDeleteReviewSnapshot):
        pass

    subclassed_snapshot = SnapshotSubclass.model_validate(_snapshot().model_dump())

    for value in (
        None,
        {},
        _snapshot().model_dump(),
        [],
        "snapshot",
        b"snapshot",
        object(),
        subclassed_snapshot,
    ):
        with pytest.raises(TypeError):
            summarize_archive_delete_review_snapshot(value)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            export_archive_delete_review_snapshot(value)  # type: ignore[arg-type]


def test_helpers_revalidate_constructed_snapshots_before_export() -> None:
    tampered_snapshot = ArchiveDeleteReviewSnapshot.model_construct(
        session_id="session-001",
        snapshot_kind="archive_delete_review_snapshot",
        status="review_snapshot_ready",
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
    )

    with pytest.raises(ValidationError):
        summarize_archive_delete_review_snapshot(tampered_snapshot)
    with pytest.raises(ValidationError):
        export_archive_delete_review_snapshot(tampered_snapshot)

    private_path_snapshot = ArchiveDeleteReviewSnapshot.model_construct(
        session_id="session-001",
        snapshot_kind="archive_delete_review_snapshot",
        status="review_snapshot_ready",
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
    )

    with pytest.raises(ValidationError):
        export_archive_delete_review_snapshot(private_path_snapshot)

    arbitrary_scope_snapshot = ArchiveDeleteReviewSnapshot.model_construct(
        session_id="session-001",
        snapshot_kind="archive_delete_review_snapshot",
        status="review_snapshot_ready",
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
    )

    with pytest.raises(ValidationError):
        export_archive_delete_review_snapshot(arbitrary_scope_snapshot)

    arbitrary_action_snapshot = ArchiveDeleteReviewSnapshot.model_construct(
        session_id="session-001",
        snapshot_kind="archive_delete_review_snapshot",
        status="review_snapshot_ready",
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
    )

    with pytest.raises(ValidationError):
        export_archive_delete_review_snapshot(arbitrary_action_snapshot)


def test_models_are_immutable() -> None:
    snapshot = _snapshot()

    with pytest.raises(ValidationError):
        snapshot.session_id = "session-002"

    with pytest.raises(ValidationError):
        snapshot.artifacts[0].filename = "events.jsonl"


def test_source_has_no_execution_or_persistence_behavior() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "async_scholar"
        / "archive_delete_review.py"
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
