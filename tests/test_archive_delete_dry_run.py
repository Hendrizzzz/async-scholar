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
    ARCHIVE_DELETE_CONFIRMATION_RESPONSE_STATUS,
    ArchiveDeleteConfirmationResponse,
    ArchiveDeleteConfirmationResponseArtifact,
    build_archive_delete_confirmation_response,
)
from async_scholar.archive_delete_dry_run import (
    ARCHIVE_DELETE_DRY_RUN_REQUEST_KIND,
    ARCHIVE_DELETE_DRY_RUN_STATUS,
    ArchiveDeleteDryRunRequest,
    ArchiveDeleteDryRunRequestArtifact,
    build_archive_delete_dry_run_request,
    export_archive_delete_dry_run_request,
    summarize_archive_delete_dry_run_request,
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


def _response() -> ArchiveDeleteConfirmationResponse:
    return build_archive_delete_confirmation_response(
        _preview(),
        ARCHIVE_DELETE_CONFIRMATION_PHRASE,
    )


def _request() -> ArchiveDeleteDryRunRequest:
    return build_archive_delete_dry_run_request(_response())


def test_build_request_from_actual_response_copies_only_safe_metadata() -> None:
    response = _response()

    request = build_archive_delete_dry_run_request(response)

    assert request.session_id == "session-001"
    assert request.request_kind == ARCHIVE_DELETE_DRY_RUN_REQUEST_KIND
    assert request.status == ARCHIVE_DELETE_DRY_RUN_STATUS
    assert request.requires_confirmation is True
    assert request.confirmation_verified is True
    assert request.dry_run_only is True
    assert request.artifact_count == 3
    assert request.artifacts == (
        ArchiveDeleteDryRunRequestArtifact(
            kind="transcript_jsonl",
            filename="transcript.jsonl",
        ),
        ArchiveDeleteDryRunRequestArtifact(
            kind="events_jsonl",
            filename="events.jsonl",
        ),
        ArchiveDeleteDryRunRequestArtifact(
            kind="reviewer_markdown",
            filename="reviewer.md",
        ),
    )
    assert request.artifacts[0] is not response.artifacts[0]
    assert set(request.model_dump()) == {
        "session_id",
        "request_kind",
        "status",
        "requires_confirmation",
        "confirmation_verified",
        "dry_run_only",
        "artifact_count",
        "artifacts",
    }


def test_builder_rejects_non_response_inputs() -> None:
    class ResponseSubclass(ArchiveDeleteConfirmationResponse):
        pass

    class DuckResponse:
        session_id = "session-001"
        requires_confirmation = True
        confirmation_verified = True
        status = ARCHIVE_DELETE_CONFIRMATION_RESPONSE_STATUS
        artifact_count = 1
        artifacts = (
            ArchiveDeleteConfirmationResponseArtifact(
                kind="transcript_jsonl",
                filename="transcript.jsonl",
            ),
        )

    subclassed_response = ResponseSubclass.model_validate(_response().model_dump())

    for value in (
        None,
        {},
        _response().model_dump(),
        [],
        "response",
        b"response",
        object(),
        DuckResponse(),
        subclassed_response,
    ):
        with pytest.raises(TypeError):
            build_archive_delete_dry_run_request(value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "tampered_response",
    [
        ArchiveDeleteConfirmationResponse.model_construct(
            session_id="session..001",
            requires_confirmation=True,
            confirmation_verified=True,
            status=ARCHIVE_DELETE_CONFIRMATION_RESPONSE_STATUS,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteConfirmationResponseArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                ),
            ),
        ),
        ArchiveDeleteConfirmationResponse.model_construct(
            session_id="session-001",
            requires_confirmation=False,
            confirmation_verified=True,
            status=ARCHIVE_DELETE_CONFIRMATION_RESPONSE_STATUS,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteConfirmationResponseArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                ),
            ),
        ),
        ArchiveDeleteConfirmationResponse.model_construct(
            session_id="session-001",
            requires_confirmation=True,
            confirmation_verified=False,
            status=ARCHIVE_DELETE_CONFIRMATION_RESPONSE_STATUS,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteConfirmationResponseArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                ),
            ),
        ),
        ArchiveDeleteConfirmationResponse.model_construct(
            session_id="session-001",
            requires_confirmation=True,
            confirmation_verified=True,
            status="deleted",
            artifact_count=1,
            artifacts=(
                ArchiveDeleteConfirmationResponseArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                ),
            ),
        ),
        ArchiveDeleteConfirmationResponse.model_construct(
            session_id="session-001",
            requires_confirmation=True,
            confirmation_verified=True,
            status=ARCHIVE_DELETE_CONFIRMATION_RESPONSE_STATUS,
            artifact_count=2,
            artifacts=(
                ArchiveDeleteConfirmationResponseArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="transcript.jsonl",
                ),
            ),
        ),
        ArchiveDeleteConfirmationResponse.model_construct(
            session_id="session-001",
            requires_confirmation=True,
            confirmation_verified=True,
            status=ARCHIVE_DELETE_CONFIRMATION_RESPONSE_STATUS,
            artifact_count=1,
            artifacts=(
                ArchiveDeleteConfirmationResponseArtifact.model_construct(
                    kind="transcript_jsonl",
                    filename="C:\\Users\\student\\transcript.jsonl",
                ),
            ),
        ),
    ],
)
def test_builder_revalidates_constructed_responses_before_copy(
    tampered_response: ArchiveDeleteConfirmationResponse,
) -> None:
    with pytest.raises(ValidationError):
        build_archive_delete_dry_run_request(tampered_response)


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
def test_request_rejects_false_or_non_true_flags(
    field_name: str,
    value: object,
) -> None:
    data = _request().model_dump()
    data[field_name] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteDryRunRequest(**data)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("request_kind", ""),
        ("request_kind", "archive_delete"),
        ("request_kind", "delete_dry_run"),
        ("status", ""),
        ("status", "pending"),
        ("status", "deleted"),
    ],
)
def test_request_rejects_arbitrary_request_kind_or_status(
    field_name: str,
    value: str,
) -> None:
    data = _request().model_dump()
    data[field_name] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteDryRunRequest(**data)


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
def test_request_rejects_unsafe_session_ids(session_id: str) -> None:
    data = _request().model_dump()
    data["session_id"] = session_id

    with pytest.raises(ValidationError):
        ArchiveDeleteDryRunRequest(**data)


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
        ArchiveDeleteDryRunRequestArtifact(kind=kind, filename=filename)


def test_request_rejects_extra_fields_count_mismatch_empty_and_duplicates() -> None:
    request = _request()

    with pytest.raises(ValidationError):
        ArchiveDeleteDryRunRequest(**request.model_dump(), extra="blocked")

    with pytest.raises(ValidationError):
        ArchiveDeleteDryRunRequestArtifact(
            kind="transcript_jsonl",
            filename="transcript.jsonl",
            private_path="C:\\Users\\student\\secret.txt",
        )

    data = request.model_dump()
    data["artifact_count"] = 2
    with pytest.raises(ValidationError):
        ArchiveDeleteDryRunRequest(**data)

    data = request.model_dump()
    data["artifacts"] = []
    data["artifact_count"] = 0
    with pytest.raises(ValidationError):
        ArchiveDeleteDryRunRequest(**data)

    duplicate_artifact = {
        "kind": "transcript_jsonl",
        "filename": "transcript.jsonl",
    }
    data = request.model_dump()
    data["artifacts"] = [duplicate_artifact, duplicate_artifact]
    data["artifact_count"] = 2
    with pytest.raises(ValidationError):
        ArchiveDeleteDryRunRequest(**data)


def test_serialization_helpers_return_deterministic_json_ready_safe_data() -> None:
    request = _request()

    assert summarize_archive_delete_dry_run_request(request) == {
        "session_id": "session-001",
        "request_kind": "archive_delete_dry_run",
        "status": "dry_run_requested",
        "requires_confirmation": True,
        "confirmation_verified": True,
        "dry_run_only": True,
        "artifact_count": 3,
    }
    assert export_archive_delete_dry_run_request(request) == {
        "session_id": "session-001",
        "request_kind": "archive_delete_dry_run",
        "status": "dry_run_requested",
        "requires_confirmation": True,
        "confirmation_verified": True,
        "dry_run_only": True,
        "artifact_count": 3,
        "artifacts": [
            {"kind": "transcript_jsonl", "filename": "transcript.jsonl"},
            {"kind": "events_jsonl", "filename": "events.jsonl"},
            {"kind": "reviewer_markdown", "filename": "reviewer.md"},
        ],
    }
    assert json.loads(
        json.dumps(export_archive_delete_dry_run_request(request))
    ) == export_archive_delete_dry_run_request(request)

    exported_text = json.dumps(export_archive_delete_dry_run_request(request))
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


def test_helpers_reject_non_request_inputs() -> None:
    class RequestSubclass(ArchiveDeleteDryRunRequest):
        pass

    subclassed_request = RequestSubclass.model_validate(_request().model_dump())

    for value in (
        None,
        {},
        _request().model_dump(),
        [],
        "request",
        b"request",
        object(),
        subclassed_request,
    ):
        with pytest.raises(TypeError):
            summarize_archive_delete_dry_run_request(value)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            export_archive_delete_dry_run_request(value)  # type: ignore[arg-type]


def test_helpers_revalidate_constructed_requests_before_export() -> None:
    tampered_request = ArchiveDeleteDryRunRequest.model_construct(
        session_id="session-001",
        request_kind="archive_delete_dry_run",
        status="dry_run_requested",
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
    )

    with pytest.raises(ValidationError):
        summarize_archive_delete_dry_run_request(tampered_request)
    with pytest.raises(ValidationError):
        export_archive_delete_dry_run_request(tampered_request)

    private_path_request = ArchiveDeleteDryRunRequest.model_construct(
        session_id="session-001",
        request_kind="archive_delete_dry_run",
        status="dry_run_requested",
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
    )

    with pytest.raises(ValidationError):
        export_archive_delete_dry_run_request(private_path_request)


def test_models_are_immutable() -> None:
    request = _request()

    with pytest.raises(ValidationError):
        request.session_id = "session-002"

    with pytest.raises(ValidationError):
        request.artifacts[0].filename = "events.jsonl"


def test_source_has_no_execution_or_persistence_behavior() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "async_scholar"
        / "archive_delete_dry_run.py"
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
