import inspect
import json

import pytest
from pydantic import ValidationError

import async_scholar.archive_delete as archive_delete
from async_scholar.archive_delete import (
    ArchiveDeleteArtifactCandidate,
    ArchiveDeleteIntent,
    ArchiveDeletePlan,
    build_archive_delete_plan,
)
from async_scholar.archive_export import (
    ArchiveArtifactKind,
    build_archive_export_manifest,
)


def _candidate(
    filename: str = "transcript.jsonl",
    kind: ArchiveArtifactKind = ArchiveArtifactKind.TRANSCRIPT_JSONL,
) -> ArchiveDeleteArtifactCandidate:
    return ArchiveDeleteArtifactCandidate(kind=kind, filename=filename)


def test_valid_delete_plan_preserves_ordered_safe_metadata() -> None:
    plan = ArchiveDeletePlan(
        session_id="session-001",
        artifacts=(
            _candidate("transcript.jsonl", ArchiveArtifactKind.TRANSCRIPT_JSONL),
            _candidate("events.jsonl", ArchiveArtifactKind.EVENTS_JSONL),
        ),
    )

    assert plan.session_id == "session-001"
    assert plan.requires_confirmation is True
    assert plan.intent is ArchiveDeleteIntent.ARCHIVE_ARTIFACT_CANDIDATES
    assert [artifact.filename for artifact in plan.artifacts] == [
        "transcript.jsonl",
        "events.jsonl",
    ]


def test_builder_copies_safe_metadata_from_archive_export_manifest_only() -> None:
    manifest = build_archive_export_manifest(
        "session-001",
        ["transcript.jsonl", "events.jsonl", "alerts.log"],
    )

    plan = build_archive_delete_plan(manifest)

    assert plan.safe_export() == {
        "session_id": "session-001",
        "intent": "archive_artifact_candidates",
        "requires_confirmation": True,
        "artifacts": [
            {"kind": "transcript_jsonl", "filename": "transcript.jsonl"},
            {"kind": "events_jsonl", "filename": "events.jsonl"},
            {"kind": "alerts_log", "filename": "alerts.log"},
        ],
    }


@pytest.mark.parametrize(
    "manifest",
    [
        None,
        {},
        {"session_id": "session-001", "artifacts": ["transcript.jsonl"]},
        ["transcript.jsonl"],
        "transcript.jsonl",
        b"transcript.jsonl",
        object(),
    ],
)
def test_builder_rejects_non_archive_export_manifest_inputs(manifest: object) -> None:
    with pytest.raises(TypeError):
        build_archive_delete_plan(manifest)


@pytest.mark.parametrize(
    "session_id",
    [
        "",
        " ",
        " session-001",
        ".session-001",
        "session..001",
        "session-001..backup",
        "../session-001",
        "session/001",
        r"session\001",
        "C:session-001",
        r"\\server\share",
        "https://example.test/session-001",
        "session-001\n",
    ],
)
def test_delete_plan_rejects_unsafe_session_ids(session_id: str) -> None:
    with pytest.raises(ValidationError):
        ArchiveDeletePlan(session_id=session_id, artifacts=(_candidate(),))


def test_delete_plan_rejects_empty_and_duplicate_artifacts() -> None:
    with pytest.raises(ValidationError):
        ArchiveDeletePlan(session_id="session-001", artifacts=())

    duplicate = _candidate()
    with pytest.raises(ValidationError):
        ArchiveDeletePlan(session_id="session-001", artifacts=(duplicate, duplicate))


@pytest.mark.parametrize(
    "filename",
    [
        "",
        " transcript.jsonl",
        "/tmp/transcript.jsonl",
        r"C:\private\transcript.jsonl",
        r"\\server\share\transcript.jsonl",
        "file:///tmp/transcript.jsonl",
        "https://example.test/transcript.jsonl",
        "../transcript.jsonl",
        "nested/transcript.jsonl",
        r"nested\transcript.jsonl",
        "transcript.jsonl\n",
        "unknown.jsonl",
    ],
)
def test_artifact_candidate_rejects_unsafe_or_unknown_filenames(filename: str) -> None:
    with pytest.raises(ValidationError):
        _candidate(filename)


def test_artifact_candidate_rejects_kind_filename_mismatch() -> None:
    with pytest.raises(ValidationError):
        ArchiveDeleteArtifactCandidate(
            kind=ArchiveArtifactKind.EVENTS_JSONL,
            filename="transcript.jsonl",
        )


def test_models_reject_extra_fields_false_confirmation_and_arbitrary_intent() -> None:
    with pytest.raises(ValidationError):
        ArchiveDeleteArtifactCandidate(
            kind=ArchiveArtifactKind.TRANSCRIPT_JSONL,
            filename="transcript.jsonl",
            private_path=r"C:\Users\student\lecture.wav",
        )

    with pytest.raises(ValidationError):
        ArchiveDeletePlan(
            session_id="session-001",
            artifacts=(_candidate(),),
            deletion_reason="clean up private data",
        )

    with pytest.raises(ValidationError):
        ArchiveDeletePlan(
            session_id="session-001",
            artifacts=(_candidate(),),
            requires_confirmation=False,
        )

    with pytest.raises(ValidationError):
        ArchiveDeletePlan(
            session_id="session-001",
            artifacts=(_candidate(),),
            requires_confirmation=1,
        )

    with pytest.raises(ValidationError):
        ArchiveDeletePlan(
            session_id="session-001",
            artifacts=(_candidate(),),
            intent="delete_everything",
        )


def test_delete_plan_helpers_are_json_ready_and_deterministic() -> None:
    plan = build_archive_delete_plan(
        build_archive_export_manifest(
            "session-001",
            ["transcript.jsonl", "events.jsonl"],
        )
    )

    assert plan.safe_summary() == {
        "session_id": "session-001",
        "intent": "archive_artifact_candidates",
        "requires_confirmation": True,
        "artifact_count": 2,
        "artifacts": [
            {"kind": "transcript_jsonl", "filename": "transcript.jsonl"},
            {"kind": "events_jsonl", "filename": "events.jsonl"},
        ],
    }
    assert plan.to_json_ready() == plan.safe_export()
    json.dumps(plan.safe_summary())
    json.dumps(plan.safe_export())
    assert plan.model_dump(mode="json") == {
        "session_id": "session-001",
        "artifacts": [
            {"kind": "transcript_jsonl", "filename": "transcript.jsonl"},
            {"kind": "events_jsonl", "filename": "events.jsonl"},
        ],
        "requires_confirmation": True,
        "intent": "archive_artifact_candidates",
    }


def test_delete_plan_models_are_immutable() -> None:
    plan = ArchiveDeletePlan(session_id="session-001", artifacts=(_candidate(),))
    artifact = plan.artifacts[0]

    with pytest.raises(ValidationError):
        plan.session_id = "session-002"

    with pytest.raises(ValidationError):
        artifact.filename = "events.jsonl"


def test_safe_helpers_do_not_expose_private_or_execution_metadata() -> None:
    plan = build_archive_delete_plan(
        build_archive_export_manifest(
            "session-001",
            [
                "transcript.jsonl",
                "transcript.md",
                "events.jsonl",
                "alerts.log",
                "reviewer.md",
                "runtime.jsonl",
                "benchmark-report.json",
            ],
        )
    )

    exported = json.dumps(
        {
            "summary": plan.safe_summary(),
            "export": plan.safe_export(),
            "json_ready": plan.to_json_ready(),
        },
        sort_keys=True,
    )

    forbidden_fragments = [
        "C:",
        "\\\\",
        "/Users/",
        "lecture text",
        "event contents",
        "alert_payload",
        "cookie",
        "token",
        "secret",
        "auth",
        "browser",
        "model_path",
        "worker",
        "timer",
        "sqlite",
        "scheduler",
        "deleted_at",
        "deletion_result",
        "generated contents",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in exported


def test_archive_delete_source_has_no_execution_or_persistence_behavior() -> None:
    source = inspect.getsource(archive_delete)
    forbidden_snippets = [
        "open(",
        "read_text",
        "write_text",
        "from pathlib",
        "import os",
        "os.",
        "unlink",
        "remove(",
        "rmdir",
        "rmtree",
        "shutil",
        "zipfile",
        "tarfile",
        "sqlite",
        "connect(",
        "subprocess",
        "threading",
        "thread",
        "timer",
        "asyncio",
        "requests",
        "httpx",
        "socket",
        "urllib",
        "nicegui",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "notification",
        "notify",
    ]

    lowered = source.lower()
    for snippet in forbidden_snippets:
        assert snippet not in lowered
