from __future__ import annotations

import inspect
import json
from typing import Any

import pytest
from pydantic import ValidationError

from async_scholar import archive_delete_confirmation
from async_scholar.archive_delete import (
    ArchiveDeleteArtifactCandidate,
    ArchiveDeletePlan,
)
from async_scholar.archive_delete_confirmation import (
    ARCHIVE_DELETE_CONFIRMATION_BODY,
    ARCHIVE_DELETE_CONFIRMATION_PHRASE,
    ARCHIVE_DELETE_CONFIRMATION_TITLE,
    ArchiveDeleteConfirmationArtifact,
    ArchiveDeleteConfirmationPreview,
    build_archive_delete_confirmation_preview,
    export_archive_delete_confirmation,
    summarize_archive_delete_confirmation,
)

VALID_SESSION_ID = "session-001"
VALID_ARTIFACTS = (
    ("transcript_jsonl", "transcript.jsonl"),
    ("events_jsonl", "events.jsonl"),
)


def _delete_plan() -> ArchiveDeletePlan:
    return ArchiveDeletePlan(
        session_id=VALID_SESSION_ID,
        requires_confirmation=True,
        artifacts=tuple(
            ArchiveDeleteArtifactCandidate(kind=kind, filename=filename)
            for kind, filename in VALID_ARTIFACTS
        ),
    )


def _confirmation_artifact() -> ArchiveDeleteConfirmationArtifact:
    kind, filename = VALID_ARTIFACTS[0]
    return ArchiveDeleteConfirmationArtifact(kind=kind, filename=filename)


def _confirmation_preview(**overrides: Any) -> ArchiveDeleteConfirmationPreview:
    data: dict[str, Any] = {
        "session_id": VALID_SESSION_ID,
        "title": ARCHIVE_DELETE_CONFIRMATION_TITLE,
        "body": ARCHIVE_DELETE_CONFIRMATION_BODY,
        "requires_confirmation": True,
        "confirmation_phrase": ARCHIVE_DELETE_CONFIRMATION_PHRASE,
        "artifact_count": 1,
        "artifacts": (_confirmation_artifact(),),
    }
    data.update(overrides)
    return ArchiveDeleteConfirmationPreview(**data)


def test_valid_confirmation_preview_creation() -> None:
    preview = _confirmation_preview()

    assert preview.session_id == VALID_SESSION_ID
    assert preview.title == ARCHIVE_DELETE_CONFIRMATION_TITLE
    assert preview.body == ARCHIVE_DELETE_CONFIRMATION_BODY
    assert preview.requires_confirmation is True
    assert preview.confirmation_phrase == ARCHIVE_DELETE_CONFIRMATION_PHRASE
    assert preview.artifact_count == 1
    assert preview.artifacts == (_confirmation_artifact(),)


def test_builder_copies_ordered_metadata_from_archive_delete_plan() -> None:
    plan = _delete_plan()

    preview = build_archive_delete_confirmation_preview(plan)

    assert preview.session_id == plan.session_id
    assert preview.artifact_count == 2
    assert preview.artifacts == tuple(
        ArchiveDeleteConfirmationArtifact(kind=kind, filename=filename)
        for kind, filename in VALID_ARTIFACTS
    )
    assert preview.to_safe_export()["artifacts"] == [
        {"kind": "transcript_jsonl", "filename": "transcript.jsonl"},
        {"kind": "events_jsonl", "filename": "events.jsonl"},
    ]


@pytest.mark.parametrize(
    "not_plan",
    [
        {
            "session_id": VALID_SESSION_ID,
            "requires_confirmation": True,
            "artifacts": [{"kind": "transcript_jsonl", "filename": "transcript.jsonl"}],
        },
        "session-001",
        b"session-001",
        [
            ArchiveDeleteArtifactCandidate(
                kind="transcript_jsonl", filename="transcript.jsonl"
            )
        ],
        object(),
    ],
)
def test_builder_rejects_non_archive_delete_plan_inputs(not_plan: Any) -> None:
    with pytest.raises(TypeError):
        build_archive_delete_confirmation_preview(not_plan)


def test_preview_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        _confirmation_preview(private_path="C:\\Users\\student\\class.mp4")


@pytest.mark.parametrize("requires_confirmation", [False, 1, "true", None])
def test_preview_requires_exact_true_confirmation(requires_confirmation: Any) -> None:
    with pytest.raises(ValidationError):
        _confirmation_preview(requires_confirmation=requires_confirmation)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("title", "Delete these files"),
        ("body", "This includes private transcript contents."),
        ("confirmation_phrase", "delete archive"),
    ],
)
def test_preview_rejects_arbitrary_confirmation_text(
    field_name: str, value: str
) -> None:
    with pytest.raises(ValidationError):
        _confirmation_preview(**{field_name: value})


@pytest.mark.parametrize(
    "session_id",
    [
        "",
        "session..001",
        "../session-001",
        "session/001",
        "session\\001",
        "C:\\session-001",
        "https://example.test/session-001",
        "session-001\n",
    ],
)
def test_preview_rejects_unsafe_session_ids(session_id: str) -> None:
    with pytest.raises(ValidationError):
        _confirmation_preview(session_id=session_id)


@pytest.mark.parametrize(
    "filename",
    [
        "",
        "../transcript.jsonl",
        "nested/transcript.jsonl",
        "nested\\transcript.jsonl",
        "C:\\private\\transcript.jsonl",
        "https://example.test/transcript.jsonl",
        "transcript.jsonl\n",
    ],
)
def test_artifact_rejects_unsafe_filenames(filename: str) -> None:
    with pytest.raises(ValidationError):
        ArchiveDeleteConfirmationArtifact(kind="transcript_jsonl", filename=filename)


def test_artifact_rejects_unknown_safe_filename_pair() -> None:
    with pytest.raises(ValidationError):
        ArchiveDeleteConfirmationArtifact(
            kind="transcript_jsonl", filename="alerts.log"
        )


def test_preview_rejects_duplicate_artifacts() -> None:
    artifact = _confirmation_artifact()

    with pytest.raises(ValidationError):
        _confirmation_preview(artifact_count=2, artifacts=(artifact, artifact))


def test_preview_rejects_mismatched_artifact_count() -> None:
    with pytest.raises(ValidationError):
        _confirmation_preview(artifact_count=2)


def test_preview_rejects_scalar_artifacts_collection() -> None:
    with pytest.raises(ValidationError):
        _confirmation_preview(artifact_count=1, artifacts="transcript.jsonl")


def test_safe_summary_and_export_are_deterministic_json_ready() -> None:
    preview = build_archive_delete_confirmation_preview(_delete_plan())

    summary = summarize_archive_delete_confirmation(preview)
    exported = export_archive_delete_confirmation(preview)

    assert summary == {
        "session_id": VALID_SESSION_ID,
        "title": ARCHIVE_DELETE_CONFIRMATION_TITLE,
        "body": ARCHIVE_DELETE_CONFIRMATION_BODY,
        "requires_confirmation": True,
        "confirmation_phrase": ARCHIVE_DELETE_CONFIRMATION_PHRASE,
        "artifact_count": 2,
    }
    assert exported == {
        **summary,
        "artifacts": [
            {"kind": "transcript_jsonl", "filename": "transcript.jsonl"},
            {"kind": "events_jsonl", "filename": "events.jsonl"},
        ],
    }
    assert json.loads(json.dumps(exported, sort_keys=True)) == exported


def test_model_dump_is_json_ready_and_privacy_safe() -> None:
    preview = build_archive_delete_confirmation_preview(_delete_plan())

    dumped = preview.model_dump(mode="json")
    dumped_json = json.dumps(dumped, sort_keys=True)

    assert dumped == {
        "session_id": VALID_SESSION_ID,
        "title": ARCHIVE_DELETE_CONFIRMATION_TITLE,
        "body": ARCHIVE_DELETE_CONFIRMATION_BODY,
        "requires_confirmation": True,
        "confirmation_phrase": ARCHIVE_DELETE_CONFIRMATION_PHRASE,
        "artifact_count": 2,
        "artifacts": [
            {"kind": "transcript_jsonl", "filename": "transcript.jsonl"},
            {"kind": "events_jsonl", "filename": "events.jsonl"},
        ],
    }
    for forbidden_fragment in [
        "C:\\",
        "/Users/",
        "transcript text",
        "event contents",
        "alert payload",
        "cookie",
        "token",
        "secret",
        "model cache",
        "sqlite",
        "scheduler",
        "worker",
        "timer",
        "DELETE_EXECUTION",
        "generated artifact contents",
    ]:
        assert forbidden_fragment not in dumped_json


def test_models_are_immutable() -> None:
    preview = _confirmation_preview()
    artifact = _confirmation_artifact()

    with pytest.raises(ValidationError):
        preview.session_id = "session-002"
    with pytest.raises(ValidationError):
        artifact.filename = "events.jsonl"


@pytest.mark.parametrize(
    "helper_input", [_confirmation_preview().to_safe_export(), object()]
)
def test_safe_helpers_reject_non_preview_inputs(helper_input: Any) -> None:
    with pytest.raises(TypeError):
        summarize_archive_delete_confirmation(helper_input)
    with pytest.raises(TypeError):
        export_archive_delete_confirmation(helper_input)


def test_module_source_has_no_forbidden_behavior() -> None:
    source = inspect.getsource(archive_delete_confirmation).lower()

    forbidden_tokens = [
        "open(",
        ".read(",
        ".write(",
        "unlink",
        "remove(",
        "rmdir",
        "sqlite",
        "socket",
        "requests",
        "urllib",
        "subprocess",
        "threading",
        "timer",
        "sleep(",
        "nicegui",
        "audio",
        "stt",
        "vad",
        "browser",
        "notification",
    ]
    for token in forbidden_tokens:
        assert token not in source
