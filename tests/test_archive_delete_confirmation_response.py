from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from async_scholar.archive_delete_confirmation import (
    ARCHIVE_DELETE_CONFIRMATION_BODY,
    ARCHIVE_DELETE_CONFIRMATION_PHRASE,
    ARCHIVE_DELETE_CONFIRMATION_TITLE,
    ArchiveDeleteConfirmationArtifact,
    ArchiveDeleteConfirmationPreview,
)
from async_scholar.archive_delete_confirmation_response import (
    ARCHIVE_DELETE_CONFIRMATION_RESPONSE_STATUS,
    ArchiveDeleteConfirmationResponse,
    ArchiveDeleteConfirmationResponseArtifact,
    build_archive_delete_confirmation_response,
    export_archive_delete_confirmation_response,
    summarize_archive_delete_confirmation_response,
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


def test_build_response_from_actual_preview_copies_only_safe_metadata() -> None:
    preview = _preview()

    response = build_archive_delete_confirmation_response(
        preview,
        preview.confirmation_phrase,
    )

    assert response.session_id == "session-001"
    assert response.requires_confirmation is True
    assert response.confirmation_verified is True
    assert response.status == ARCHIVE_DELETE_CONFIRMATION_RESPONSE_STATUS
    assert response.artifact_count == 3
    assert response.artifacts == (
        ArchiveDeleteConfirmationResponseArtifact(
            kind="transcript_jsonl",
            filename="transcript.jsonl",
        ),
        ArchiveDeleteConfirmationResponseArtifact(
            kind="events_jsonl",
            filename="events.jsonl",
        ),
        ArchiveDeleteConfirmationResponseArtifact(
            kind="reviewer_markdown",
            filename="reviewer.md",
        ),
    )
    assert response.artifacts[0] is not preview.artifacts[0]
    assert set(response.model_dump()) == {
        "session_id",
        "requires_confirmation",
        "confirmation_verified",
        "status",
        "artifact_count",
        "artifacts",
    }


@pytest.mark.parametrize(
    "entered_phrase",
    [
        "",
        " ",
        "delete archive",
        "Delete Archive",
        "DELETE ARCHIVE ",
        " DELETE ARCHIVE",
        "DELETE  ARCHIVE",
        "wrong private phrase",
    ],
)
def test_builder_requires_exact_confirmation_phrase(entered_phrase: str) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_archive_delete_confirmation_response(_preview(), entered_phrase)

    assert str(exc_info.value) == "confirmation phrase does not match the preview"
    if entered_phrase.strip():
        assert entered_phrase not in str(exc_info.value)


@pytest.mark.parametrize("entered_phrase", [None, True, 1, b"DELETE ARCHIVE", []])
def test_builder_rejects_non_string_confirmation_phrase(
    entered_phrase: object,
) -> None:
    with pytest.raises(TypeError) as exc_info:
        build_archive_delete_confirmation_response(_preview(), entered_phrase)  # type: ignore[arg-type]

    assert str(exc_info.value) == "confirmation phrase must be a string"


def test_builder_rejects_non_preview_inputs() -> None:
    class PreviewSubclass(ArchiveDeleteConfirmationPreview):
        pass

    subclassed_preview = PreviewSubclass.model_validate(_preview().model_dump())

    for value in (
        None,
        {},
        _preview().model_dump(),
        [],
        "preview",
        b"preview",
        object(),
        subclassed_preview,
    ):
        with pytest.raises(TypeError):
            build_archive_delete_confirmation_response(
                value,  # type: ignore[arg-type]
                ARCHIVE_DELETE_CONFIRMATION_PHRASE,
            )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("requires_confirmation", False),
        ("requires_confirmation", 1),
        ("requires_confirmation", "true"),
        ("confirmation_verified", False),
        ("confirmation_verified", 1),
        ("confirmation_verified", "true"),
    ],
)
def test_response_rejects_false_or_non_true_confirmation_flags(
    field_name: str,
    value: object,
) -> None:
    data = _response().model_dump()
    data[field_name] = value

    with pytest.raises(ValidationError):
        ArchiveDeleteConfirmationResponse(**data)


@pytest.mark.parametrize(
    "status",
    ["", "confirmed", "deleted", "pending", "confirmation verified"],
)
def test_response_rejects_arbitrary_status_text(status: str) -> None:
    data = _response().model_dump()
    data["status"] = status

    with pytest.raises(ValidationError):
        ArchiveDeleteConfirmationResponse(**data)


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
def test_response_rejects_unsafe_session_ids(session_id: str) -> None:
    data = _response().model_dump()
    data["session_id"] = session_id

    with pytest.raises(ValidationError):
        ArchiveDeleteConfirmationResponse(**data)


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
        ArchiveDeleteConfirmationResponseArtifact(kind=kind, filename=filename)


def test_response_rejects_extra_fields_count_mismatch_empty_and_duplicates() -> None:
    response = _response()

    with pytest.raises(ValidationError):
        ArchiveDeleteConfirmationResponse(**response.model_dump(), extra="blocked")

    with pytest.raises(ValidationError):
        ArchiveDeleteConfirmationResponseArtifact(
            kind="transcript_jsonl",
            filename="transcript.jsonl",
            private_path="C:\\Users\\student\\secret.txt",
        )

    data = response.model_dump()
    data["artifact_count"] = 2
    with pytest.raises(ValidationError):
        ArchiveDeleteConfirmationResponse(**data)

    data = response.model_dump()
    data["artifacts"] = []
    data["artifact_count"] = 0
    with pytest.raises(ValidationError):
        ArchiveDeleteConfirmationResponse(**data)

    duplicate_artifact = {
        "kind": "transcript_jsonl",
        "filename": "transcript.jsonl",
    }
    data = response.model_dump()
    data["artifacts"] = [duplicate_artifact, duplicate_artifact]
    data["artifact_count"] = 2
    with pytest.raises(ValidationError):
        ArchiveDeleteConfirmationResponse(**data)


def test_builder_revalidates_constructed_preview_metadata() -> None:
    unsafe_preview = ArchiveDeleteConfirmationPreview.model_construct(
        session_id="C:\\Users\\student\\secret-session",
        confirmation_phrase=ARCHIVE_DELETE_CONFIRMATION_PHRASE,
        artifact_count=1,
        artifacts=(
            ArchiveDeleteConfirmationArtifact.model_construct(
                kind="transcript_jsonl",
                filename="transcript.jsonl",
            ),
        ),
    )

    with pytest.raises(ValidationError):
        build_archive_delete_confirmation_response(
            unsafe_preview,
            ARCHIVE_DELETE_CONFIRMATION_PHRASE,
        )

    unsafe_artifact_preview = ArchiveDeleteConfirmationPreview.model_construct(
        session_id="session-001",
        confirmation_phrase=ARCHIVE_DELETE_CONFIRMATION_PHRASE,
        artifact_count=1,
        artifacts=(
            ArchiveDeleteConfirmationArtifact.model_construct(
                kind="transcript_jsonl",
                filename="C:\\Users\\student\\transcript.jsonl",
            ),
        ),
    )

    with pytest.raises(ValidationError):
        build_archive_delete_confirmation_response(
            unsafe_artifact_preview,
            ARCHIVE_DELETE_CONFIRMATION_PHRASE,
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("title", "Private delete prompt"),
        ("body", "Private body text"),
        ("confirmation_phrase", "wrong private phrase"),
        ("requires_confirmation", False),
        ("requires_confirmation", 1),
    ],
)
def test_builder_rejects_tampered_preview_confirmation_controls(
    field_name: str,
    value: object,
) -> None:
    preview_data = {
        "session_id": "session-001",
        "title": ARCHIVE_DELETE_CONFIRMATION_TITLE,
        "body": ARCHIVE_DELETE_CONFIRMATION_BODY,
        "requires_confirmation": True,
        "confirmation_phrase": ARCHIVE_DELETE_CONFIRMATION_PHRASE,
        "artifact_count": 1,
        "artifacts": (
            ArchiveDeleteConfirmationArtifact.model_construct(
                kind="transcript_jsonl",
                filename="transcript.jsonl",
            ),
        ),
    }
    preview_data[field_name] = value
    tampered_preview = ArchiveDeleteConfirmationPreview.model_construct(**preview_data)

    with pytest.raises(ValueError) as exc_info:
        build_archive_delete_confirmation_response(
            tampered_preview,
            str(value),
        )

    assert str(exc_info.value) == "preview confirmation controls are invalid"
    if isinstance(value, str):
        assert value not in str(exc_info.value)


def test_serialization_helpers_return_deterministic_json_ready_safe_data() -> None:
    response = _response()

    assert summarize_archive_delete_confirmation_response(response) == {
        "session_id": "session-001",
        "requires_confirmation": True,
        "confirmation_verified": True,
        "status": "confirmation_verified",
        "artifact_count": 3,
    }
    assert export_archive_delete_confirmation_response(response) == {
        "session_id": "session-001",
        "requires_confirmation": True,
        "confirmation_verified": True,
        "status": "confirmation_verified",
        "artifact_count": 3,
        "artifacts": [
            {"kind": "transcript_jsonl", "filename": "transcript.jsonl"},
            {"kind": "events_jsonl", "filename": "events.jsonl"},
            {"kind": "reviewer_markdown", "filename": "reviewer.md"},
        ],
    }
    assert json.loads(
        json.dumps(export_archive_delete_confirmation_response(response))
    ) == export_archive_delete_confirmation_response(response)

    exported_text = json.dumps(export_archive_delete_confirmation_response(response))
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


def test_helpers_reject_non_response_inputs() -> None:
    for value in (None, {}, _response().model_dump(), [], "response", object()):
        with pytest.raises(TypeError):
            summarize_archive_delete_confirmation_response(value)  # type: ignore[arg-type]
        with pytest.raises(TypeError):
            export_archive_delete_confirmation_response(value)  # type: ignore[arg-type]


def test_helpers_revalidate_constructed_responses_before_export() -> None:
    tampered_response = ArchiveDeleteConfirmationResponse.model_construct(
        session_id="session-001",
        requires_confirmation=False,
        confirmation_verified=True,
        status="confirmation_verified",
        artifact_count=1,
        artifacts=(
            ArchiveDeleteConfirmationResponseArtifact.model_construct(
                kind="transcript_jsonl",
                filename="transcript.jsonl",
            ),
        ),
    )

    with pytest.raises(ValidationError):
        summarize_archive_delete_confirmation_response(tampered_response)
    with pytest.raises(ValidationError):
        export_archive_delete_confirmation_response(tampered_response)

    private_path_response = ArchiveDeleteConfirmationResponse.model_construct(
        session_id="session-001",
        requires_confirmation=True,
        confirmation_verified=True,
        status="confirmation_verified",
        artifact_count=1,
        artifacts=(
            ArchiveDeleteConfirmationResponseArtifact.model_construct(
                kind="transcript_jsonl",
                filename="C:\\Users\\student\\transcript.jsonl",
            ),
        ),
    )

    with pytest.raises(ValidationError):
        export_archive_delete_confirmation_response(private_path_response)


def test_models_are_immutable() -> None:
    response = _response()

    with pytest.raises(ValidationError):
        response.session_id = "session-002"

    with pytest.raises(ValidationError):
        response.artifacts[0].filename = "events.jsonl"


def test_source_has_no_execution_or_persistence_behavior() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "async_scholar"
        / "archive_delete_confirmation_response.py"
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
