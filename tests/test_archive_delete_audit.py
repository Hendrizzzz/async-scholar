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
    export_archive_delete_audit_event,
    summarize_archive_delete_audit_event,
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
    ARCHIVE_DELETE_DRY_RUN_ARTIFACT_ACTION,
    ARCHIVE_DELETE_DRY_RUN_ARTIFACT_STATUS,
    ARCHIVE_DELETE_DRY_RUN_RESULT_KIND,
    ARCHIVE_DELETE_DRY_RUN_RESULT_STATUS,
    ArchiveDeleteDryRunResult,
    ArchiveDeleteDryRunResultArtifact,
    build_archive_delete_dry_run_result,
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


def _result() -> ArchiveDeleteDryRunResult:
    response = build_archive_delete_confirmation_response(
        _preview(),
        ARCHIVE_DELETE_CONFIRMATION_PHRASE,
    )
    request = build_archive_delete_dry_run_request(response)
    return build_archive_delete_dry_run_result(request)


def _event() -> ArchiveDeleteAuditEvent:
    return build_archive_delete_audit_event(_result())


def test_build_event_from_actual_result_copies_only_safe_metadata() -> None:
    result = _result()

    event = build_archive_delete_audit_event(result)

    assert event.session_id == "session-001"
    assert event.event_kind == ARCHIVE_DELETE_AUDIT_EVENT_KIND
    assert event.status == ARCHIVE_DELETE_AUDIT_STATUS
    assert event.audit_scope == ARCHIVE_DELETE_AUDIT_SCOPE
    assert event.requires_confirmation is True
    assert event.confirmation_verified is True
    assert event.dry_run_only is True
    assert event.deletion_performed is False
    assert event.artifact_count == 3
    assert event.artifacts == (
        ArchiveDeleteAuditArtifact(
            kind="transcript_jsonl",
            filename="transcript.jsonl",
        ),
        ArchiveDeleteAuditArtifact(
            kind="events_jsonl",
            filename="events.jsonl",
        ),
        ArchiveDeleteAuditArtifact(
            kind="reviewer_markdown",
            filename="reviewer.md",
        ),
    )
    assert event.artifacts[0] is not result.artifacts[0]
    assert event.artifacts[0].action == ARCHIVE_DELETE_DRY_RUN_ARTIFACT_ACTION
    assert event.artifacts[0].status == ARCHIVE_DELETE_DRY_RUN_ARTIFACT_STATUS
    assert set(event.model_dump()) == {
        "session_id",
        "event_kind",
        "status",
        "audit_scope",
        "requires_confirmation",
        "confirmation_verified",
        "dry_run_only",
        "deletion_performed",
        "artifact_count",
        "artifacts",
    }


def test_builder_rejects_non_result_inputs() -> None:
    class ResultSubclass(ArchiveDeleteDryRunResult):
        pass

    class DuckResult:
        session_id = "session-001"
        result_kind = ARCHIVE_DELETE_DRY_RUN_RESULT_KIND
        status = ARCHIVE_DELETE_DRY_RUN_RESULT_STATUS
        requires_confirmation = True
        confirmation_verified = True
        dry_run_only = True
        deletion_performed = False
        artifact_count = 1
        artifacts = (
            ArchiveDeleteDryRunResultArtifact(
                kind="transcript_jsonl",
                filename="transcript.jsonl",
            ),
        )

    subclassed_result = ResultSubclass.model_validate(_result().model_dump())

    for value in (
        None,
        {},
        _result().model_dump(),
        [],
        "result",
        b"result",
        object(),
        DuckResult(),
        subclassed_result,
    ):
        with pytest.raises(TypeError):
            build_archive_delete_audit_event(value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "tampered_result",
    [
        ArchiveDeleteDryRunResult.model_construct(
            session_id="session..001",
            result_kind=ARCHIVE_DELETE_DRY_RUN_RESULT_KIND,
            status=ARCHIVE_DELETE_DRY_RUN_RESULT_STATUS,
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteDryRunResultArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteDryRunResult.model_construct(
            session_id="session-001",
            result_kind=ARCHIVE_DELETE_DRY_RUN_RESULT_KIND,
            status=ARCHIVE_DELETE_DRY_RUN_RESULT_STATUS,
            requires_confirmation=False,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteDryRunResultArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteDryRunResult.model_construct(
            session_id="session-001",
            result_kind=ARCHIVE_DELETE_DRY_RUN_RESULT_KIND,
            status=ARCHIVE_DELETE_DRY_RUN_RESULT_STATUS,
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=False,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteDryRunResultArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteDryRunResult.model_construct(
            session_id="session-001",
            result_kind=ARCHIVE_DELETE_DRY_RUN_RESULT_KIND,
            status=ARCHIVE_DELETE_DRY_RUN_RESULT_STATUS,
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=True,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteDryRunResultArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteDryRunResult.model_construct(
            session_id="session-001",
            result_kind="archive_delete",
            status=ARCHIVE_DELETE_DRY_RUN_RESULT_STATUS,
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteDryRunResultArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteDryRunResult.model_construct(
            session_id="session-001",
            result_kind=ARCHIVE_DELETE_DRY_RUN_RESULT_KIND,
            status="deleted",
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteDryRunResultArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteDryRunResult.model_construct(
            session_id="session-001",
            result_kind=ARCHIVE_DELETE_DRY_RUN_RESULT_KIND,
            status=ARCHIVE_DELETE_DRY_RUN_RESULT_STATUS,
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=2,
            artifacts=(
                ArchiveDeleteDryRunResultArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteDryRunResult.model_construct(
            session_id="session-001",
            result_kind=ARCHIVE_DELETE_DRY_RUN_RESULT_KIND,
            status=ARCHIVE_DELETE_DRY_RUN_RESULT_STATUS,
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteDryRunResultArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                    action="delete",
                    status="not_deleted",
                ),
            ),
        ),
        ArchiveDeleteDryRunResult.model_construct(
            session_id="session-001",
            result_kind=ARCHIVE_DELETE_DRY_RUN_RESULT_KIND,
            status=ARCHIVE_DELETE_DRY_RUN_RESULT_STATUS,
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            deletion_performed=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteDryRunResultArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="C:\\Users\\student\\transcript.jsonl",
                    action="would_delete",
                    status="not_deleted",
                ),
            ),
        ),
    ],
)
def test_builder_revalidates_constructed_results_before_copy(
    tampered_result: ArchiveDeleteDryRunResult,
) -> None:
    with pytest.raises(ValidationError):
        build_archive_delete_audit_event(tampered_result)


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
def test_event_rejects_false_or_non_true_flags(
    field_name: str,
    value: object,
) -> None:
    data = _event().model_dump()
    data[field_name] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteAuditEvent(**data)


@pytest.mark.parametrize("value", [True, 0, 1, "false", None])
def test_event_rejects_non_false_deletion_performed(value: object) -> None:
    data = _event().model_dump()
    data["deletion_performed"] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteAuditEvent(**data)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("event_kind", ""),
        ("event_kind", "archive_delete"),
        ("event_kind", "archive_delete_dry_run_result"),
        ("status", ""),
        ("status", "pending"),
        ("status", "deleted"),
        ("audit_scope", ""),
        ("audit_scope", "full_contents"),
        ("audit_scope", "private_paths"),
    ],
)
def test_event_rejects_arbitrary_event_kind_status_or_scope(
    field_name: str,
    value: str,
) -> None:
    data = _event().model_dump()
    data[field_name] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteAuditEvent(**data)


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
    data = ArchiveDeleteAuditArtifact(
        kind="transcript_jsonl",
        filename="transcript.jsonl",
    ).model_dump()
    data[field_name] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteAuditArtifact(**data)


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
def test_event_rejects_unsafe_session_ids(session_id: str) -> None:
    data = _event().model_dump()
    data["session_id"] = session_id

    with pytest.raises(ValidationError):
        ArchiveDeleteAuditEvent(**data)


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
        ArchiveDeleteAuditArtifact(kind=kind, filename=filename)


def test_event_rejects_extra_fields_count_mismatch_empty_and_duplicates() -> None:
    event = _event()

    with pytest.raises(ValidationError):
        ArchiveDeleteAuditEvent(**event.model_dump(), extra="blocked")

    with pytest.raises(ValidationError):
        ArchiveDeleteAuditArtifact(
            kind="transcript_jsonl",
            filename="transcript.jsonl",
            private_path="C:\\Users\\student\\secret.txt",
        )

    data = event.model_dump()
    data["artifact_count"] = 2
    with pytest.raises(ValidationError):
        ArchiveDeleteAuditEvent(**data)

    data = event.model_dump()
    data["artifacts"] = []
    data["artifact_count"] = 0
    with pytest.raises(ValidationError):
        ArchiveDeleteAuditEvent(**data)

    duplicate_artifact = {
        "kind": "transcript_jsonl",
        "filename": "transcript.jsonl",
        "action": "would_delete",
        "status": "not_deleted",
    }
    data = event.model_dump()
    data["artifacts"] = [duplicate_artifact, duplicate_artifact]
    data["artifact_count"] = 2
    with pytest.raises(ValidationError):
        ArchiveDeleteAuditEvent(**data)


def test_serialization_helpers_return_deterministic_json_ready_safe_data() -> None:
    event = _event()

    assert summarize_archive_delete_audit_event(event) == {
        "session_id": "session-001",
        "event_kind": "archive_delete_dry_run_audit",
        "status": "dry_run_audited",
        "audit_scope": "metadata_only",
        "requires_confirmation": True,
        "confirmation_verified": True,
        "dry_run_only": True,
        "deletion_performed": False,
        "artifact_count": 3,
    }
    assert export_archive_delete_audit_event(event) == {
        "session_id": "session-001",
        "event_kind": "archive_delete_dry_run_audit",
        "status": "dry_run_audited",
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
        json.dumps(export_archive_delete_audit_event(event))
    ) == export_archive_delete_audit_event(event)

    exported_text = json.dumps(export_archive_delete_audit_event(event))
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


def test_helpers_reject_non_event_inputs() -> None:
    class EventSubclass(ArchiveDeleteAuditEvent):
        pass

    subclassed_event = EventSubclass.model_validate(_event().model_dump())

    for value in (
        None,
        {},
        _event().model_dump(),
        [],
        "event",
        b"event",
        object(),
        subclassed_event,
    ):
        with pytest.raises(TypeError):
            summarize_archive_delete_audit_event(value)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            export_archive_delete_audit_event(value)  # type: ignore[arg-type]


def test_helpers_revalidate_constructed_events_before_export() -> None:
    tampered_event = ArchiveDeleteAuditEvent.model_construct(
        session_id="session-001",
        event_kind="archive_delete_dry_run_audit",
        status="dry_run_audited",
        audit_scope="metadata_only",
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
    )

    with pytest.raises(ValidationError):
        summarize_archive_delete_audit_event(tampered_event)
    with pytest.raises(ValidationError):
        export_archive_delete_audit_event(tampered_event)

    private_path_event = ArchiveDeleteAuditEvent.model_construct(
        session_id="session-001",
        event_kind="archive_delete_dry_run_audit",
        status="dry_run_audited",
        audit_scope="metadata_only",
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
    )

    with pytest.raises(ValidationError):
        export_archive_delete_audit_event(private_path_event)

    arbitrary_scope_event = ArchiveDeleteAuditEvent.model_construct(
        session_id="session-001",
        event_kind="archive_delete_dry_run_audit",
        status="dry_run_audited",
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
    )

    with pytest.raises(ValidationError):
        export_archive_delete_audit_event(arbitrary_scope_event)

    arbitrary_action_event = ArchiveDeleteAuditEvent.model_construct(
        session_id="session-001",
        event_kind="archive_delete_dry_run_audit",
        status="dry_run_audited",
        audit_scope="metadata_only",
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
    )

    with pytest.raises(ValidationError):
        export_archive_delete_audit_event(arbitrary_action_event)


def test_models_are_immutable() -> None:
    event = _event()

    with pytest.raises(ValidationError):
        event.session_id = "session-002"

    with pytest.raises(ValidationError):
        event.artifacts[0].filename = "events.jsonl"


def test_source_has_no_execution_or_persistence_behavior() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "async_scholar"
        / "archive_delete_audit.py"
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
