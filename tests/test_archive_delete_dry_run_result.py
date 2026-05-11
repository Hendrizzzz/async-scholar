from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from async_scholar.archive_delete_confirmation import (
    ARCHIVE_DELETE_CONFIRMATION_PHRASE,
    ArchiveDeleteConfirmationArtifact,
    ArchiveDeleteConfirmationPreview,
)
from async_scholar.archive_delete_confirmation_response import (
    build_archive_delete_confirmation_response,
)
from async_scholar.archive_delete_dry_run import (
    ARCHIVE_DELETE_DRY_RUN_REQUEST_KIND,
    ARCHIVE_DELETE_DRY_RUN_STATUS,
    ArchiveDeleteDryRunRequest,
    ArchiveDeleteDryRunRequestArtifact,
    build_archive_delete_dry_run_request,
)
from async_scholar.archive_delete_dry_run_result import (
    ARCHIVE_DELETE_DRY_RUN_ARTIFACT_ACTION,
    ARCHIVE_DELETE_DRY_RUN_ARTIFACT_STATUS,
    ARCHIVE_DELETE_DRY_RUN_RESULT_KIND,
    ARCHIVE_DELETE_DRY_RUN_RESULT_STATUS,
    ArchiveDeleteDryRunResult,
    ArchiveDeleteDryRunResultArtifact,
    build_archive_delete_dry_run_result,
    export_archive_delete_dry_run_result,
    summarize_archive_delete_dry_run_result,
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


def _request() -> ArchiveDeleteDryRunRequest:
    response = build_archive_delete_confirmation_response(
        _preview(),
        ARCHIVE_DELETE_CONFIRMATION_PHRASE,
    )
    return build_archive_delete_dry_run_request(response)


def _result() -> ArchiveDeleteDryRunResult:
    return build_archive_delete_dry_run_result(_request())


def test_build_result_from_actual_request_copies_only_safe_metadata() -> None:
    request = _request()

    result = build_archive_delete_dry_run_result(request)

    assert result.session_id == "session-001"
    assert result.result_kind == ARCHIVE_DELETE_DRY_RUN_RESULT_KIND
    assert result.status == ARCHIVE_DELETE_DRY_RUN_RESULT_STATUS
    assert result.requires_confirmation is True
    assert result.confirmation_verified is True
    assert result.dry_run_only is True
    assert result.deletion_performed is False
    assert result.artifact_count == 3
    assert result.artifacts == (
        ArchiveDeleteDryRunResultArtifact(
            kind="transcript_jsonl",
            filename="transcript.jsonl",
        ),
        ArchiveDeleteDryRunResultArtifact(
            kind="events_jsonl",
            filename="events.jsonl",
        ),
        ArchiveDeleteDryRunResultArtifact(
            kind="reviewer_markdown",
            filename="reviewer.md",
        ),
    )
    assert result.artifacts[0] is not request.artifacts[0]
    assert result.artifacts[0].action == ARCHIVE_DELETE_DRY_RUN_ARTIFACT_ACTION
    assert result.artifacts[0].status == ARCHIVE_DELETE_DRY_RUN_ARTIFACT_STATUS
    assert set(result.model_dump()) == {
        "session_id",
        "result_kind",
        "status",
        "requires_confirmation",
        "confirmation_verified",
        "dry_run_only",
        "deletion_performed",
        "artifact_count",
        "artifacts",
    }


def test_builder_rejects_non_request_inputs() -> None:
    class RequestSubclass(ArchiveDeleteDryRunRequest):
        pass

    class DuckRequest:
        session_id = "session-001"
        request_kind = ARCHIVE_DELETE_DRY_RUN_REQUEST_KIND
        status = ARCHIVE_DELETE_DRY_RUN_STATUS
        requires_confirmation = True
        confirmation_verified = True
        dry_run_only = True
        artifact_count = 1
        artifacts = (
            ArchiveDeleteDryRunRequestArtifact(
                kind="transcript_jsonl",
                filename="transcript.jsonl",
            ),
        )

    subclassed_request = RequestSubclass.model_validate(_request().model_dump())

    for value in (
        None,
        {},
        _request().model_dump(),
        [],
        "request",
        b"request",
        object(),
        DuckRequest(),
        subclassed_request,
    ):
        with pytest.raises(TypeError):
            build_archive_delete_dry_run_result(value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "tampered_request",
    [
        ArchiveDeleteDryRunRequest.model_construct(
            session_id="session..001",
            request_kind=ARCHIVE_DELETE_DRY_RUN_REQUEST_KIND,
            status=ARCHIVE_DELETE_DRY_RUN_STATUS,
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteDryRunRequestArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                ),
            ),
        ),
        ArchiveDeleteDryRunRequest.model_construct(
            session_id="session-001",
            request_kind=ARCHIVE_DELETE_DRY_RUN_REQUEST_KIND,
            status=ARCHIVE_DELETE_DRY_RUN_STATUS,
            requires_confirmation=False,
            confirmation_verified=True,
            dry_run_only=True,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteDryRunRequestArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                ),
            ),
        ),
        ArchiveDeleteDryRunRequest.model_construct(
            session_id="session-001",
            request_kind=ARCHIVE_DELETE_DRY_RUN_REQUEST_KIND,
            status=ARCHIVE_DELETE_DRY_RUN_STATUS,
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=False,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteDryRunRequestArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                ),
            ),
        ),
        ArchiveDeleteDryRunRequest.model_construct(
            session_id="session-001",
            request_kind="archive_delete",
            status=ARCHIVE_DELETE_DRY_RUN_STATUS,
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteDryRunRequestArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                ),
            ),
        ),
        ArchiveDeleteDryRunRequest.model_construct(
            session_id="session-001",
            request_kind=ARCHIVE_DELETE_DRY_RUN_REQUEST_KIND,
            status="deleted",
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteDryRunRequestArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                ),
            ),
        ),
        ArchiveDeleteDryRunRequest.model_construct(
            session_id="session-001",
            request_kind=ARCHIVE_DELETE_DRY_RUN_REQUEST_KIND,
            status=ARCHIVE_DELETE_DRY_RUN_STATUS,
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            artifact_count=2,
            artifacts=(
                ArchiveDeleteDryRunRequestArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                ),
            ),
        ),
        ArchiveDeleteDryRunRequest.model_construct(
            session_id="session-001",
            request_kind=ARCHIVE_DELETE_DRY_RUN_REQUEST_KIND,
            status=ARCHIVE_DELETE_DRY_RUN_STATUS,
            requires_confirmation=True,
            confirmation_verified=True,
            dry_run_only=True,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteDryRunRequestArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="C:\\Users\\student\\transcript.jsonl",
                ),
            ),
        ),
    ],
)
def test_builder_revalidates_constructed_requests_before_copy(
    tampered_request: ArchiveDeleteDryRunRequest,
) -> None:
    with pytest.raises(ValidationError):
        build_archive_delete_dry_run_result(tampered_request)


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
def test_result_rejects_false_or_non_true_flags(
    field_name: str,
    value: object,
) -> None:
    data = _result().model_dump()
    data[field_name] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteDryRunResult(**data)


@pytest.mark.parametrize("value", [True, 0, 1, "false", None])
def test_result_rejects_non_false_deletion_performed(value: object) -> None:
    data = _result().model_dump()
    data["deletion_performed"] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteDryRunResult(**data)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("result_kind", ""),
        ("result_kind", "archive_delete"),
        ("result_kind", "archive_delete_dry_run"),
        ("status", ""),
        ("status", "pending"),
        ("status", "deleted"),
    ],
)
def test_result_rejects_arbitrary_result_kind_or_status(
    field_name: str,
    value: str,
) -> None:
    data = _result().model_dump()
    data[field_name] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteDryRunResult(**data)


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
    data = ArchiveDeleteDryRunResultArtifact(
        kind="transcript_jsonl",
        filename="transcript.jsonl",
    ).model_dump()
    data[field_name] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteDryRunResultArtifact(**data)


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
def test_result_rejects_unsafe_session_ids(session_id: str) -> None:
    data = _result().model_dump()
    data["session_id"] = session_id

    with pytest.raises(ValidationError):
        ArchiveDeleteDryRunResult(**data)


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
        ArchiveDeleteDryRunResultArtifact(kind=kind, filename=filename)


def test_result_rejects_extra_fields_count_mismatch_empty_and_duplicates() -> None:
    result = _result()

    with pytest.raises(ValidationError):
        ArchiveDeleteDryRunResult(**result.model_dump(), extra="blocked")

    with pytest.raises(ValidationError):
        ArchiveDeleteDryRunResultArtifact(
            kind="transcript_jsonl",
            filename="transcript.jsonl",
            private_path="C:\\Users\\student\\secret.txt",
        )

    data = result.model_dump()
    data["artifact_count"] = 2
    with pytest.raises(ValidationError):
        ArchiveDeleteDryRunResult(**data)

    data = result.model_dump()
    data["artifacts"] = []
    data["artifact_count"] = 0
    with pytest.raises(ValidationError):
        ArchiveDeleteDryRunResult(**data)

    duplicate_artifact = {
        "kind": "transcript_jsonl",
        "filename": "transcript.jsonl",
        "action": "would_delete",
        "status": "not_deleted",
    }
    data = result.model_dump()
    data["artifacts"] = [duplicate_artifact, duplicate_artifact]
    data["artifact_count"] = 2
    with pytest.raises(ValidationError):
        ArchiveDeleteDryRunResult(**data)


def test_serialization_helpers_return_deterministic_json_ready_safe_data() -> None:
    result = _result()

    assert summarize_archive_delete_dry_run_result(result) == {
        "session_id": "session-001",
        "result_kind": "archive_delete_dry_run_result",
        "status": "dry_run_completed",
        "requires_confirmation": True,
        "confirmation_verified": True,
        "dry_run_only": True,
        "deletion_performed": False,
        "artifact_count": 3,
    }
    assert export_archive_delete_dry_run_result(result) == {
        "session_id": "session-001",
        "result_kind": "archive_delete_dry_run_result",
        "status": "dry_run_completed",
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
        json.dumps(export_archive_delete_dry_run_result(result))
    ) == export_archive_delete_dry_run_result(result)

    exported_text = json.dumps(export_archive_delete_dry_run_result(result))
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


def test_helpers_reject_non_result_inputs() -> None:
    class ResultSubclass(ArchiveDeleteDryRunResult):
        pass

    subclassed_result = ResultSubclass.model_validate(_result().model_dump())

    for value in (
        None,
        {},
        _result().model_dump(),
        [],
        "result",
        b"result",
        object(),
        subclassed_result,
    ):
        with pytest.raises(TypeError):
            summarize_archive_delete_dry_run_result(value)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            export_archive_delete_dry_run_result(value)  # type: ignore[arg-type]


def test_helpers_revalidate_constructed_results_before_export() -> None:
    tampered_result = ArchiveDeleteDryRunResult.model_construct(
        session_id="session-001",
        result_kind="archive_delete_dry_run_result",
        status="dry_run_completed",
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
    )

    with pytest.raises(ValidationError):
        summarize_archive_delete_dry_run_result(tampered_result)
    with pytest.raises(ValidationError):
        export_archive_delete_dry_run_result(tampered_result)

    private_path_result = ArchiveDeleteDryRunResult.model_construct(
        session_id="session-001",
        result_kind="archive_delete_dry_run_result",
        status="dry_run_completed",
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
    )

    with pytest.raises(ValidationError):
        export_archive_delete_dry_run_result(private_path_result)

    arbitrary_action_result = ArchiveDeleteDryRunResult.model_construct(
        session_id="session-001",
        result_kind="archive_delete_dry_run_result",
        status="dry_run_completed",
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
    )

    with pytest.raises(ValidationError):
        export_archive_delete_dry_run_result(arbitrary_action_result)


def test_models_are_immutable() -> None:
    result = _result()

    with pytest.raises(ValidationError):
        result.session_id = "session-002"

    with pytest.raises(ValidationError):
        result.artifacts[0].filename = "events.jsonl"


def test_source_has_no_execution_or_persistence_behavior() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "async_scholar"
        / "archive_delete_dry_run_result.py"
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
