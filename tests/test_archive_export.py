import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from async_scholar.archive_export import (
    ArchiveArtifactEntry,
    ArchiveExportManifest,
    archive_export_manifest_safe_summary,
    archive_export_manifest_to_json_ready,
    build_archive_export_manifest,
)


def test_build_archive_export_manifest_accepts_safe_artifacts() -> None:
    manifest = build_archive_export_manifest(
        "fixture_attendance_roll_call",
        ["transcript.jsonl", "events.jsonl", "alerts.log"],
    )

    assert manifest.session_id == "fixture_attendance_roll_call"
    assert [artifact.kind.value for artifact in manifest.artifacts] == [
        "transcript_jsonl",
        "events_jsonl",
        "alerts_log",
    ]
    assert [artifact.filename for artifact in manifest.artifacts] == [
        "transcript.jsonl",
        "events.jsonl",
        "alerts.log",
    ]


@pytest.mark.parametrize(
    "session_id",
    [
        "",
        "   ",
        ".hidden",
        "../session",
        "session/one",
        "session\\one",
        "C:session",
        "\\\\server\\share",
        "https://example.test/session",
        "session\none",
        "session one",
    ],
)
def test_archive_export_manifest_rejects_invalid_session_ids(session_id: str) -> None:
    with pytest.raises(ValidationError):
        ArchiveExportManifest(
            session_id=session_id,
            artifacts=[{"kind": "transcript_jsonl", "filename": "transcript.jsonl"}],
        )


@pytest.mark.parametrize(
    "filename",
    [
        "",
        "   ",
        "unknown.json",
        "/tmp/transcript.jsonl",
        "C:\\Users\\student\\transcript.jsonl",
        "\\\\server\\share\\transcript.jsonl",
        "https://example.test/transcript.jsonl",
        "../transcript.jsonl",
        "nested/transcript.jsonl",
        "nested\\transcript.jsonl",
        "transcript.jsonl\n",
    ],
)
def test_archive_export_manifest_rejects_unsafe_artifact_filenames(
    filename: str,
) -> None:
    with pytest.raises((ValueError, ValidationError)):
        build_archive_export_manifest("session-001", [filename])


def test_archive_export_manifest_rejects_unknown_or_mismatched_artifacts() -> None:
    with pytest.raises(ValidationError):
        ArchiveArtifactEntry(kind="events_jsonl", filename="transcript.jsonl")

    with pytest.raises(ValidationError):
        ArchiveArtifactEntry(kind="unknown", filename="transcript.jsonl")


@pytest.mark.parametrize(
    "artifact_input",
    [
        ("transcript_jsonl", "transcript.jsonl"),
        {"kind": "transcript_jsonl", "filename": "transcript.jsonl"},
        ArchiveArtifactEntry(kind="transcript_jsonl", filename="transcript.jsonl"),
    ],
)
def test_archive_export_builder_accepts_only_filename_inputs(
    artifact_input: object,
) -> None:
    with pytest.raises(TypeError):
        build_archive_export_manifest("session-001", [artifact_input])


@pytest.mark.parametrize(
    "artifact_filenames",
    [
        "transcript.jsonl",
        b"transcript.jsonl",
        {"transcript.jsonl": "C:\\Users\\student\\lecture\\transcript.jsonl"},
    ],
)
def test_archive_export_builder_rejects_non_iterable_filename_collections(
    artifact_filenames: object,
) -> None:
    with pytest.raises(TypeError):
        build_archive_export_manifest("session-001", artifact_filenames)


def test_archive_export_manifest_rejects_duplicate_artifacts() -> None:
    with pytest.raises(ValidationError):
        build_archive_export_manifest(
            "session-001",
            ["transcript.jsonl", "events.jsonl", "transcript.jsonl"],
        )


def test_archive_export_manifest_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ArchiveExportManifest(
            session_id="session-001",
            artifacts=[
                {
                    "kind": "transcript_jsonl",
                    "filename": "transcript.jsonl",
                    "absolute_path": "C:\\Users\\student\\lecture\\transcript.jsonl",
                },
            ],
            worker_state="running",
        )


def test_archive_export_manifest_helpers_return_json_ready_data() -> None:
    manifest = build_archive_export_manifest(
        "session-001",
        ["transcript.jsonl", "reviewer.md"],
    )

    export_data = archive_export_manifest_to_json_ready(manifest)
    summary = archive_export_manifest_safe_summary(manifest)

    assert export_data == {
        "session_id": "session-001",
        "artifacts": [
            {"kind": "transcript_jsonl", "filename": "transcript.jsonl"},
            {"kind": "reviewer_markdown", "filename": "reviewer.md"},
        ],
    }
    assert summary == {
        "session_id": "session-001",
        "artifact_count": 2,
        "artifacts": [
            {"kind": "transcript_jsonl", "filename": "transcript.jsonl"},
            {"kind": "reviewer_markdown", "filename": "reviewer.md"},
        ],
    }
    assert json.loads(json.dumps(export_data, sort_keys=True)) == export_data
    assert json.loads(json.dumps(summary, sort_keys=True)) == summary


def test_archive_export_manifest_safe_helpers_expose_only_manifest_metadata() -> None:
    manifest = build_archive_export_manifest(
        "session-001",
        ["transcript.jsonl", "events.jsonl", "alerts.log", "runtime.jsonl"],
    )

    export_text = json.dumps(manifest.safe_export(), sort_keys=True)
    summary_text = json.dumps(manifest.safe_summary(), sort_keys=True)

    for payload in (manifest.safe_export(), manifest.safe_summary()):
        assert set(payload) <= {"session_id", "artifact_count", "artifacts"}

    combined_text = f"{export_text}\n{summary_text}".lower()
    for forbidden_fragment in (
        "c:\\",
        "\\users\\",
        "/users/",
        "transcript text",
        "event contents",
        "alert payload",
        "auth",
        "cookie",
        "secret",
        "token",
        "model path",
        "worker_state",
        "timer_state",
        "sqlite",
        "delete",
        "execute",
    ):
        assert forbidden_fragment not in combined_text


def test_archive_export_manifest_is_immutable() -> None:
    manifest = build_archive_export_manifest("session-001", ["transcript.jsonl"])

    with pytest.raises(ValidationError):
        manifest.session_id = "session-002"
    with pytest.raises(AttributeError):
        manifest.artifacts.append(
            ArchiveArtifactEntry(kind="events_jsonl", filename="events.jsonl"),
        )
    with pytest.raises(ValidationError):
        manifest.artifacts[0].filename = "events.jsonl"


def test_archive_export_module_has_no_execution_or_persistence_behavior() -> None:
    source = Path("src/async_scholar/archive_export.py").read_text(encoding="utf-8")

    forbidden_fragments = (
        "open(",
        "read_text(",
        "write_text(",
        "mkdir(",
        "unlink(",
        "remove(",
        "rmdir(",
        "ZipFile",
        "zipfile",
        "tarfile",
        "shutil",
        "sqlite3",
        "requests",
        "httpx",
        "playwright",
        "sounddevice",
        "faster_whisper",
        "nicegui",
        "threading",
        "asyncio",
        "Timer(",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source
