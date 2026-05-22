import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from async_scholar.archive_export import (
    ALLOWED_ARCHIVE_ARTIFACT_FILENAMES,
    ArchiveArtifactEntry,
    ArchiveArtifactKind,
    ArchiveExportExecutionResult,
    ArchiveExportManifest,
    ArchiveExportPreflightSummary,
    ArchiveExportVerificationArtifact,
    ArchiveExportVerificationStatus,
    ArchiveExportVerificationSummary,
    ArchiveInventoryArtifact,
    ArchiveSessionInventory,
    archive_export_execution_result_safe_summary,
    archive_export_execution_result_to_json_ready,
    archive_export_manifest_safe_summary,
    archive_export_manifest_to_json_ready,
    archive_export_preflight_summary_safe_summary,
    archive_export_preflight_summary_to_json_ready,
    archive_export_verification_summary_safe_summary,
    archive_export_verification_summary_to_json_ready,
    archive_session_inventory_safe_summary,
    archive_session_inventory_to_json_ready,
    build_archive_export_manifest,
    build_archive_export_manifest_from_inventory,
    build_archive_export_manifest_from_root,
    build_archive_export_preflight_summary_from_root,
    build_archive_export_verification_summary_from_roots,
    build_archive_session_inventory,
    execute_archive_export_to_local_root,
    resolve_session_archive_dir,
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


def test_resolve_session_archive_dir_confines_safe_session_id(tmp_path) -> None:
    archive_root = tmp_path / "archive-root"

    resolved_session_dir = resolve_session_archive_dir(archive_root, "session-001")

    assert resolved_session_dir == archive_root.resolve(strict=False) / "session-001"


def test_archive_session_inventory_returns_relative_allowlisted_metadata(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    transcript_text = "Synthetic private lecture sentence with token-shaped text."
    reviewer_text = "Synthetic reviewer note that should never be serialized."
    (session_dir / "transcript.jsonl").write_text(transcript_text, encoding="utf-8")
    (session_dir / "reviewer.md").write_text(reviewer_text, encoding="utf-8")

    inventory = build_archive_session_inventory(archive_root, "session-001")
    payload = archive_session_inventory_to_json_ready(inventory)
    summary = archive_session_inventory_safe_summary(inventory)

    assert inventory.session_id == "session-001"
    assert inventory.session_dir == "session-001"
    assert [artifact.filename for artifact in inventory.artifacts] == list(
        ALLOWED_ARCHIVE_ARTIFACT_FILENAMES
    )
    assert payload["session_id"] == "session-001"
    assert payload["session_dir"] == "session-001"
    assert summary["existing_artifact_count"] == 2
    assert payload["artifacts"][0] == {
        "kind": "transcript_jsonl",
        "filename": "transcript.jsonl",
        "relative_path": "transcript.jsonl",
        "exists": True,
        "size_bytes": len(transcript_text.encode("utf-8")),
    }
    assert payload["artifacts"][1] == {
        "kind": "transcript_markdown",
        "filename": "transcript.md",
        "relative_path": "transcript.md",
        "exists": False,
    }
    assert payload["artifacts"][4] == {
        "kind": "reviewer_markdown",
        "filename": "reviewer.md",
        "relative_path": "reviewer.md",
        "exists": True,
        "size_bytes": len(reviewer_text.encode("utf-8")),
    }
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload
    assert json.loads(json.dumps(summary, sort_keys=True)) == summary

    serialized_payload = json.dumps(payload, sort_keys=True).lower()
    assert str(tmp_path).lower() not in serialized_payload
    assert "synthetic private lecture sentence" not in serialized_payload
    assert "token-shaped text" not in serialized_payload
    assert "synthetic reviewer note" not in serialized_payload


def test_archive_session_inventory_ignores_unallowlisted_files(tmp_path) -> None:
    archive_root = tmp_path / "archive-root"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    (session_dir / "private-notes.txt").write_text(
        "Synthetic private notes that must not be inventoried.",
        encoding="utf-8",
    )

    payload = archive_session_inventory_to_json_ready(
        build_archive_session_inventory(archive_root, "session-001"),
    )

    serialized_payload = json.dumps(payload, sort_keys=True)
    assert [artifact["filename"] for artifact in payload["artifacts"]] == list(
        ALLOWED_ARCHIVE_ARTIFACT_FILENAMES
    )
    assert "private-notes.txt" not in serialized_payload
    assert "Synthetic private notes" not in serialized_payload


def test_archive_export_manifest_from_inventory_keeps_existing_artifacts_only(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    (session_dir / "transcript.jsonl").write_text("{}", encoding="utf-8")
    (session_dir / "alerts.log").write_text("{}", encoding="utf-8")
    (session_dir / "benchmark-report.json").write_text("{}", encoding="utf-8")

    inventory = build_archive_session_inventory(archive_root, "session-001")
    manifest = build_archive_export_manifest_from_inventory(inventory)

    assert archive_export_manifest_to_json_ready(manifest) == {
        "session_id": "session-001",
        "artifacts": [
            {"kind": "transcript_jsonl", "filename": "transcript.jsonl"},
            {"kind": "alerts_log", "filename": "alerts.log"},
            {"kind": "benchmark_report", "filename": "benchmark-report.json"},
        ],
    }


def test_archive_export_manifest_from_inventory_rejects_all_missing_artifacts(
    tmp_path,
) -> None:
    inventory = build_archive_session_inventory(tmp_path, "session-001")

    with pytest.raises(ValueError, match="at least one existing artifact"):
        build_archive_export_manifest_from_inventory(inventory)


@pytest.mark.parametrize(
    "inventory_input",
    [
        "inventory",
        b"inventory",
        ["transcript.jsonl"],
        {"session_id": "session-001"},
    ],
)
def test_archive_export_manifest_from_inventory_rejects_non_inventory_inputs(
    inventory_input: object,
) -> None:
    with pytest.raises(TypeError):
        build_archive_export_manifest_from_inventory(inventory_input)


def test_archive_export_manifest_from_inventory_rejects_subclass_input(
    tmp_path,
) -> None:
    class InventorySubclass(ArchiveSessionInventory):
        pass

    inventory = build_archive_session_inventory(tmp_path, "session-001")
    subclass_inventory = InventorySubclass.model_validate(inventory.model_dump())

    with pytest.raises(TypeError):
        build_archive_export_manifest_from_inventory(subclass_inventory)


def test_archive_export_manifest_from_inventory_revalidates_constructed_inventory(
    tmp_path,
) -> None:
    valid_inventory = build_archive_session_inventory(tmp_path, "session-001")
    tampered_artifacts = list(valid_inventory.artifacts)
    tampered_artifacts[0] = ArchiveInventoryArtifact.model_construct(
        kind=ArchiveArtifactKind.TRANSCRIPT_JSONL,
        filename="C:/Users/student/transcript.jsonl",
        relative_path="C:/Users/student/transcript.jsonl",
        exists=True,
        size_bytes=10,
    )
    tampered_inventory = ArchiveSessionInventory.model_construct(
        session_id="session-001",
        session_dir="session-001",
        artifacts=tuple(tampered_artifacts),
    )

    with pytest.raises(ValueError, match="inventory metadata failed validation"):
        build_archive_export_manifest_from_inventory(tampered_inventory)


def test_archive_export_manifest_from_inventory_sanitizes_revalidation_errors(
    tmp_path,
) -> None:
    valid_inventory = build_archive_session_inventory(tmp_path, "session-001")
    unsafe_fragments = (
        "C:/Users/student/transcript.jsonl",
        "Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
    )
    tampered_artifacts = list(valid_inventory.artifacts)
    tampered_artifacts[0] = ArchiveInventoryArtifact.model_construct(
        kind=ArchiveArtifactKind.TRANSCRIPT_JSONL,
        filename="C:/Users/student/transcript-token-secret-auth-profile.jsonl",
        relative_path="C:/Users/student/transcript-token-secret-auth-profile.jsonl",
        exists=True,
        size_bytes=10,
    )
    tampered_inventory = ArchiveSessionInventory.model_construct(
        session_id="session-001",
        session_dir="session-001",
        artifacts=tuple(tampered_artifacts),
    )

    with pytest.raises(ValueError) as exc_info:
        build_archive_export_manifest_from_inventory(tampered_inventory)

    error_text = str(exc_info.value)
    assert error_text == "inventory metadata failed validation"
    for unsafe_fragment in unsafe_fragments:
        assert unsafe_fragment not in error_text


def test_archive_export_manifest_from_inventory_revalidates_nested_consistency(
    tmp_path,
) -> None:
    valid_inventory = build_archive_session_inventory(tmp_path, "session-001")
    tampered_artifacts = list(valid_inventory.artifacts)
    tampered_artifacts[0] = ArchiveInventoryArtifact.model_construct(
        kind=ArchiveArtifactKind.TRANSCRIPT_JSONL,
        filename="transcript.jsonl",
        relative_path="transcript.jsonl",
        exists=True,
        size_bytes=None,
    )
    tampered_inventory = ArchiveSessionInventory.model_construct(
        session_id="session-001",
        session_dir="session-001",
        artifacts=tuple(tampered_artifacts),
    )

    with pytest.raises(ValueError, match="inventory metadata failed validation"):
        build_archive_export_manifest_from_inventory(tampered_inventory)


def test_archive_export_manifest_from_inventory_exposes_only_manifest_metadata(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    secret_text = "Synthetic transcript token secret auth profile text."
    (session_dir / "transcript.jsonl").write_text(secret_text, encoding="utf-8")

    manifest = build_archive_export_manifest_from_inventory(
        build_archive_session_inventory(archive_root, "session-001"),
    )
    payload = archive_export_manifest_to_json_ready(manifest)

    assert payload == {
        "session_id": "session-001",
        "artifacts": [
            {"kind": "transcript_jsonl", "filename": "transcript.jsonl"},
        ],
    }
    serialized_payload = json.dumps(payload, sort_keys=True).lower()
    for forbidden_fragment in (
        "session_dir",
        "relative_path",
        "exists",
        "size_bytes",
        str(tmp_path).lower(),
        "synthetic transcript",
        "token",
        "secret",
        "auth",
        "profile",
        "c:\\",
        "/users/",
    ):
        assert forbidden_fragment not in serialized_payload


def test_archive_export_manifest_from_root_keeps_existing_artifacts_only(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    (session_dir / "events.jsonl").write_text("{}", encoding="utf-8")
    (session_dir / "runtime.jsonl").write_text("{}", encoding="utf-8")

    manifest = build_archive_export_manifest_from_root(archive_root, "session-001")

    assert archive_export_manifest_to_json_ready(manifest) == {
        "session_id": "session-001",
        "artifacts": [
            {"kind": "events_jsonl", "filename": "events.jsonl"},
            {"kind": "runtime_log", "filename": "runtime.jsonl"},
        ],
    }


@pytest.mark.parametrize(
    "session_id",
    [
        "../session",
        "session/one",
        "session\\one",
        "C:session",
        "https://example.test/session",
        "CON",
        "lpt1.txt",
    ],
)
def test_archive_export_manifest_from_root_rejects_unsafe_session_ids(
    tmp_path,
    session_id: str,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_archive_export_manifest_from_root(tmp_path, session_id)

    assert str(exc_info.value) == "archive export manifest could not be built"


def test_archive_export_manifest_from_root_rejects_all_missing_without_leaking(
    tmp_path,
) -> None:
    unsafe_fragments = (
        str(tmp_path),
        "Users",
        "token",
        "secret",
        "auth",
        "profile",
        "session-001",
    )

    with pytest.raises(ValueError) as exc_info:
        build_archive_export_manifest_from_root(tmp_path, "session-001")

    error_text = str(exc_info.value)
    assert error_text == "archive export manifest could not be built"
    for unsafe_fragment in unsafe_fragments:
        assert unsafe_fragment not in error_text


def test_archive_export_manifest_from_root_exposes_only_manifest_metadata(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root-token-secret-auth-profile"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    private_text = "Synthetic transcript token secret auth profile text."
    (session_dir / "transcript.jsonl").write_text(private_text, encoding="utf-8")

    manifest = build_archive_export_manifest_from_root(archive_root, "session-001")
    payload = archive_export_manifest_to_json_ready(manifest)

    assert payload == {
        "session_id": "session-001",
        "artifacts": [
            {"kind": "transcript_jsonl", "filename": "transcript.jsonl"},
        ],
    }
    serialized_payload = json.dumps(payload, sort_keys=True).lower()
    for forbidden_fragment in (
        "archive-root",
        "session_dir",
        "relative_path",
        "exists",
        "size_bytes",
        str(tmp_path).lower(),
        "synthetic transcript",
        "token",
        "secret",
        "auth",
        "profile",
        "c:\\",
        "/users/",
    ):
        assert forbidden_fragment not in serialized_payload


def test_archive_export_preflight_summary_from_root_returns_safe_metadata(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    events_text = "{}"
    reviewer_text = "Synthetic reviewer note with token-shaped private text."
    (session_dir / "events.jsonl").write_text(events_text, encoding="utf-8")
    (session_dir / "reviewer.md").write_text(reviewer_text, encoding="utf-8")

    summary = build_archive_export_preflight_summary_from_root(
        archive_root,
        "session-001",
    )
    payload = archive_export_preflight_summary_to_json_ready(summary)

    assert isinstance(summary, ArchiveExportPreflightSummary)
    assert payload == archive_export_preflight_summary_safe_summary(summary)
    assert set(payload) == {
        "session_id",
        "session_dir",
        "existing_count",
        "missing_count",
        "total_existing_size_bytes",
        "artifacts",
    }
    assert payload["session_id"] == "session-001"
    assert payload["session_dir"] == "session-001"
    assert payload["existing_count"] == 2
    assert payload["missing_count"] == len(ALLOWED_ARCHIVE_ARTIFACT_FILENAMES) - 2
    assert payload["total_existing_size_bytes"] == len(
        events_text.encode("utf-8")
    ) + len(reviewer_text.encode("utf-8"))
    assert [artifact["filename"] for artifact in payload["artifacts"]] == list(
        ALLOWED_ARCHIVE_ARTIFACT_FILENAMES
    )

    artifacts_by_filename = {
        artifact["filename"]: artifact for artifact in payload["artifacts"]
    }
    assert artifacts_by_filename["events.jsonl"] == {
        "kind": "events_jsonl",
        "filename": "events.jsonl",
        "exists": True,
        "size_bytes": len(events_text.encode("utf-8")),
    }
    assert artifacts_by_filename["reviewer.md"] == {
        "kind": "reviewer_markdown",
        "filename": "reviewer.md",
        "exists": True,
        "size_bytes": len(reviewer_text.encode("utf-8")),
    }
    assert artifacts_by_filename["transcript.jsonl"] == {
        "kind": "transcript_jsonl",
        "filename": "transcript.jsonl",
        "exists": False,
    }


def test_archive_export_preflight_summary_from_root_allows_all_missing_artifacts(
    tmp_path,
) -> None:
    summary = build_archive_export_preflight_summary_from_root(
        tmp_path,
        "session-001",
    )
    payload = archive_export_preflight_summary_to_json_ready(summary)

    assert payload["existing_count"] == 0
    assert payload["missing_count"] == len(ALLOWED_ARCHIVE_ARTIFACT_FILENAMES)
    assert payload["total_existing_size_bytes"] == 0
    assert [artifact["exists"] for artifact in payload["artifacts"]] == [False] * len(
        ALLOWED_ARCHIVE_ARTIFACT_FILENAMES
    )
    assert all("size_bytes" not in artifact for artifact in payload["artifacts"])


@pytest.mark.parametrize(
    "session_id",
    [
        "../session",
        "session/one",
        "session\\one",
        "C:session",
        "https://example.test/session",
        "CON",
        "lpt1.txt",
    ],
)
def test_archive_export_preflight_summary_from_root_rejects_unsafe_session_ids(
    tmp_path,
    session_id: str,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_archive_export_preflight_summary_from_root(tmp_path, session_id)

    assert str(exc_info.value) == "archive export preflight summary could not be built"


def test_archive_export_preflight_summary_from_root_sanitizes_path_errors(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root-token-secret-auth-profile"
    archive_root.write_text("Synthetic private root placeholder.", encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        build_archive_export_preflight_summary_from_root(archive_root, "session-001")

    error_text = str(exc_info.value)
    assert error_text == "archive export preflight summary could not be built"
    for unsafe_fragment in (
        str(tmp_path),
        "archive-root",
        "token",
        "secret",
        "auth",
        "profile",
        "Synthetic private",
    ):
        assert unsafe_fragment not in error_text


def test_archive_export_preflight_summary_from_root_exposes_no_private_data(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root-token-secret-auth-profile"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    private_text = "Synthetic transcript token secret auth profile text."
    (session_dir / "transcript.jsonl").write_text(private_text, encoding="utf-8")

    summary = build_archive_export_preflight_summary_from_root(
        archive_root,
        "session-001",
    )
    payload = archive_export_preflight_summary_to_json_ready(summary)
    serialized_payload = json.dumps(payload, sort_keys=True).lower()

    for forbidden_fragment in (
        "archive-root",
        "relative_path",
        str(tmp_path).lower(),
        "synthetic transcript",
        "token",
        "secret",
        "auth",
        "profile",
        "c:\\",
        "/users/",
    ):
        assert forbidden_fragment not in serialized_payload


def test_archive_export_preflight_summary_does_not_change_manifest_schema(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    (session_dir / "transcript.jsonl").write_text("{}", encoding="utf-8")

    build_archive_export_preflight_summary_from_root(archive_root, "session-001")
    manifest = build_archive_export_manifest_from_root(archive_root, "session-001")

    assert archive_export_manifest_to_json_ready(manifest) == {
        "session_id": "session-001",
        "artifacts": [
            {"kind": "transcript_jsonl", "filename": "transcript.jsonl"},
        ],
    }


def test_execute_archive_export_to_local_root_copies_existing_artifacts(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root"
    export_root = tmp_path / "export-root"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    export_root.mkdir()
    events_text = "{}"
    reviewer_text = "Synthetic reviewer text with token-shaped private text."
    (session_dir / "events.jsonl").write_text(events_text, encoding="utf-8")
    (session_dir / "reviewer.md").write_text(reviewer_text, encoding="utf-8")

    result = execute_archive_export_to_local_root(
        archive_root,
        export_root,
        "session-001",
    )
    payload = archive_export_execution_result_to_json_ready(result)

    assert isinstance(result, ArchiveExportExecutionResult)
    assert payload == archive_export_execution_result_safe_summary(result)
    assert payload == {
        "session_id": "session-001",
        "session_dir": "session-001",
        "export_dir": "session-001",
        "artifact_count": 2,
        "total_exported_size_bytes": len(events_text.encode("utf-8"))
        + len(reviewer_text.encode("utf-8")),
        "artifacts": [
            {
                "kind": "events_jsonl",
                "filename": "events.jsonl",
                "size_bytes": len(events_text.encode("utf-8")),
                "status": "exported",
            },
            {
                "kind": "reviewer_markdown",
                "filename": "reviewer.md",
                "size_bytes": len(reviewer_text.encode("utf-8")),
                "status": "exported",
            },
        ],
    }
    assert (export_root / "session-001" / "events.jsonl").read_text(
        encoding="utf-8"
    ) == events_text
    assert (export_root / "session-001" / "reviewer.md").read_text(
        encoding="utf-8"
    ) == reviewer_text
    assert (session_dir / "events.jsonl").read_text(encoding="utf-8") == events_text
    assert (session_dir / "reviewer.md").read_text(encoding="utf-8") == reviewer_text


def test_execute_archive_export_to_local_root_omits_missing_artifacts(tmp_path) -> None:
    archive_root = tmp_path / "archive-root"
    export_root = tmp_path / "export-root"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    export_root.mkdir()
    (session_dir / "alerts.log").write_text("{}", encoding="utf-8")

    result = execute_archive_export_to_local_root(
        archive_root,
        export_root,
        "session-001",
    )
    payload = archive_export_execution_result_to_json_ready(result)

    assert payload["artifact_count"] == 1
    assert payload["artifacts"] == [
        {
            "kind": "alerts_log",
            "filename": "alerts.log",
            "size_bytes": 2,
            "status": "exported",
        }
    ]
    assert (export_root / "session-001" / "alerts.log").is_file()
    assert not (export_root / "session-001" / "transcript.jsonl").exists()


def test_execute_archive_export_to_local_root_rejects_all_missing_artifacts(
    tmp_path,
) -> None:
    export_root = tmp_path / "export-root"
    export_root.mkdir()

    with pytest.raises(ValueError) as exc_info:
        execute_archive_export_to_local_root(tmp_path, export_root, "session-001")

    assert str(exc_info.value) == "archive export could not be executed"
    assert not (export_root / "session-001").exists()


@pytest.mark.parametrize(
    "session_id",
    [
        "../session",
        "session/one",
        "session\\one",
        "C:session",
        "https://example.test/session",
        "CON",
        "lpt1.txt",
    ],
)
def test_execute_archive_export_to_local_root_rejects_unsafe_session_ids(
    tmp_path,
    session_id: str,
) -> None:
    export_root = tmp_path / "export-root"
    export_root.mkdir()

    with pytest.raises(ValueError) as exc_info:
        execute_archive_export_to_local_root(tmp_path, export_root, session_id)

    assert str(exc_info.value) == "archive export could not be executed"


def test_execute_archive_export_to_local_root_requires_existing_export_root(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    (session_dir / "events.jsonl").write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        execute_archive_export_to_local_root(
            archive_root,
            tmp_path / "missing-export-root",
            "session-001",
        )

    assert str(exc_info.value) == "archive export could not be executed"


def test_execute_archive_export_to_local_root_rejects_export_root_inside_archive_root(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root"
    export_root = archive_root / "exports"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    export_root.mkdir()
    (session_dir / "events.jsonl").write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        execute_archive_export_to_local_root(archive_root, export_root, "session-001")

    assert str(exc_info.value) == "archive export could not be executed"
    assert not (export_root / "session-001").exists()


def test_execute_archive_export_to_local_root_rejects_destination_overwrite(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root"
    export_root = tmp_path / "export-root"
    session_dir = archive_root / "session-001"
    destination_dir = export_root / "session-001"
    session_dir.mkdir(parents=True)
    destination_dir.mkdir(parents=True)
    (session_dir / "events.jsonl").write_text("new", encoding="utf-8")
    existing_destination = destination_dir / "events.jsonl"
    existing_destination.write_text("existing", encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        execute_archive_export_to_local_root(archive_root, export_root, "session-001")

    assert str(exc_info.value) == "archive export could not be executed"
    assert existing_destination.read_text(encoding="utf-8") == "existing"


def test_execute_archive_export_to_local_root_exposes_no_private_data(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root-token-secret-auth-profile"
    export_root = tmp_path / "export-root-token-secret-auth-profile"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    export_root.mkdir()
    private_text = "Synthetic transcript token secret auth profile text."
    (session_dir / "transcript.jsonl").write_text(private_text, encoding="utf-8")

    result = execute_archive_export_to_local_root(
        archive_root,
        export_root,
        "session-001",
    )
    payload = archive_export_execution_result_to_json_ready(result)
    serialized_payload = json.dumps(payload, sort_keys=True).lower()

    for forbidden_fragment in (
        "archive-root",
        "export-root",
        "relative_path",
        str(tmp_path).lower(),
        "synthetic transcript",
        "token",
        "secret",
        "auth",
        "profile",
        "c:\\",
        "/users/",
    ):
        assert forbidden_fragment not in serialized_payload


def test_execute_archive_export_to_local_root_sanitizes_copy_errors(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root-token-secret-auth-profile"
    archive_root.write_text("Synthetic private root placeholder.", encoding="utf-8")
    export_root = tmp_path / "export-root"
    export_root.mkdir()

    with pytest.raises(ValueError) as exc_info:
        execute_archive_export_to_local_root(archive_root, export_root, "session-001")

    error_text = str(exc_info.value)
    assert error_text == "archive export could not be executed"
    for unsafe_fragment in (
        str(tmp_path),
        "archive-root",
        "export-root",
        "token",
        "secret",
        "auth",
        "profile",
        "Synthetic private",
    ):
        assert unsafe_fragment not in error_text


def test_execute_archive_export_preserves_manifest_and_preflight_schema(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root"
    export_root = tmp_path / "export-root"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    export_root.mkdir()
    (session_dir / "transcript.jsonl").write_text("{}", encoding="utf-8")

    execute_archive_export_to_local_root(archive_root, export_root, "session-001")
    manifest = build_archive_export_manifest_from_root(archive_root, "session-001")
    preflight = build_archive_export_preflight_summary_from_root(
        archive_root,
        "session-001",
    )

    assert archive_export_manifest_to_json_ready(manifest) == {
        "session_id": "session-001",
        "artifacts": [
            {"kind": "transcript_jsonl", "filename": "transcript.jsonl"},
        ],
    }
    assert set(archive_export_preflight_summary_to_json_ready(preflight)) == {
        "session_id",
        "session_dir",
        "existing_count",
        "missing_count",
        "total_existing_size_bytes",
        "artifacts",
    }


def test_archive_export_verification_summary_from_roots_returns_safe_metadata(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root-token-secret-auth-profile"
    export_root = tmp_path / "export-root-token-secret-auth-profile"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    export_root.mkdir()
    private_transcript = "Synthetic transcript token secret auth profile text."
    private_events = "Synthetic event private payload."
    private_reviewer = "Synthetic reviewer private payload."
    (session_dir / "transcript.jsonl").write_text(
        private_transcript,
        encoding="utf-8",
    )
    (session_dir / "events.jsonl").write_text(private_events, encoding="utf-8")
    (session_dir / "reviewer.md").write_text(private_reviewer, encoding="utf-8")
    execute_archive_export_to_local_root(archive_root, export_root, "session-001")

    summary = build_archive_export_verification_summary_from_roots(
        archive_root,
        export_root,
        "session-001",
    )
    payload = archive_export_verification_summary_to_json_ready(summary)

    assert isinstance(summary, ArchiveExportVerificationSummary)
    assert payload == archive_export_verification_summary_safe_summary(summary)
    assert payload["session_id"] == "session-001"
    assert payload["session_dir"] == "session-001"
    assert payload["export_dir"] == "session-001"
    assert payload["expected_count"] == 3
    assert payload["verified_count"] == 3
    assert payload["missing_export_count"] == 0
    assert payload["size_mismatch_count"] == 0
    assert payload["unexpected_export_count"] == 0
    assert payload["not_expected_count"] == 4
    assert payload["all_verified"] is True
    assert [artifact["filename"] for artifact in payload["artifacts"]] == list(
        ALLOWED_ARCHIVE_ARTIFACT_FILENAMES
    )
    assert payload["artifacts"][0] == {
        "kind": "transcript_jsonl",
        "filename": "transcript.jsonl",
        "expected_exists": True,
        "expected_size_bytes": len(private_transcript.encode("utf-8")),
        "exported_exists": True,
        "exported_size_bytes": len(private_transcript.encode("utf-8")),
        "status": "verified",
    }
    assert payload["artifacts"][1] == {
        "kind": "transcript_markdown",
        "filename": "transcript.md",
        "expected_exists": False,
        "exported_exists": False,
        "status": "not_expected",
    }

    serialized_payload = json.dumps(payload, sort_keys=True).lower()
    for forbidden_fragment in (
        "archive-root",
        "export-root",
        str(tmp_path).lower(),
        "synthetic transcript",
        "synthetic event",
        "synthetic reviewer",
        "token",
        "secret",
        "auth",
        "profile",
        "payload",
        "c:\\",
        "/users/",
    ):
        assert forbidden_fragment not in serialized_payload


def test_archive_export_verification_reports_missing_export(tmp_path) -> None:
    archive_root = tmp_path / "archive-root"
    export_root = tmp_path / "export-root"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    export_root.mkdir()
    (session_dir / "events.jsonl").write_text("{}", encoding="utf-8")

    summary = build_archive_export_verification_summary_from_roots(
        archive_root,
        export_root,
        "session-001",
    )
    payload = archive_export_verification_summary_to_json_ready(summary)

    assert payload["expected_count"] == 1
    assert payload["verified_count"] == 0
    assert payload["missing_export_count"] == 1
    assert payload["all_verified"] is False
    event_artifact = payload["artifacts"][2]
    assert event_artifact["filename"] == "events.jsonl"
    assert event_artifact["expected_exists"] is True
    assert event_artifact["exported_exists"] is False
    assert event_artifact["status"] == "missing_export"


def test_archive_export_verification_reports_size_mismatch(tmp_path) -> None:
    archive_root = tmp_path / "archive-root"
    export_root = tmp_path / "export-root"
    session_dir = archive_root / "session-001"
    exported_session_dir = export_root / "session-001"
    session_dir.mkdir(parents=True)
    exported_session_dir.mkdir(parents=True)
    (session_dir / "events.jsonl").write_text("archive", encoding="utf-8")
    (exported_session_dir / "events.jsonl").write_text("export", encoding="utf-8")

    payload = archive_export_verification_summary_to_json_ready(
        build_archive_export_verification_summary_from_roots(
            archive_root,
            export_root,
            "session-001",
        ),
    )

    assert payload["size_mismatch_count"] == 1
    assert payload["all_verified"] is False
    event_artifact = payload["artifacts"][2]
    assert event_artifact["status"] == "size_mismatch"
    assert event_artifact["expected_size_bytes"] == len(b"archive")
    assert event_artifact["exported_size_bytes"] == len(b"export")


def test_archive_export_verification_reports_unexpected_export(tmp_path) -> None:
    archive_root = tmp_path / "archive-root"
    export_root = tmp_path / "export-root"
    exported_session_dir = export_root / "session-001"
    archive_root.mkdir()
    exported_session_dir.mkdir(parents=True)
    (exported_session_dir / "events.jsonl").write_text("{}", encoding="utf-8")

    payload = archive_export_verification_summary_to_json_ready(
        build_archive_export_verification_summary_from_roots(
            archive_root,
            export_root,
            "session-001",
        ),
    )

    assert payload["expected_count"] == 0
    assert payload["unexpected_export_count"] == 1
    assert payload["all_verified"] is False
    event_artifact = payload["artifacts"][2]
    assert event_artifact["expected_exists"] is False
    assert event_artifact["exported_exists"] is True
    assert event_artifact["status"] == "unexpected_export"


def test_archive_export_verification_reports_zero_expected_as_not_verified(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root"
    export_root = tmp_path / "export-root"
    archive_root.mkdir()
    export_root.mkdir()

    payload = archive_export_verification_summary_to_json_ready(
        build_archive_export_verification_summary_from_roots(
            archive_root,
            export_root,
            "session-001",
        ),
    )

    assert payload["expected_count"] == 0
    assert payload["verified_count"] == 0
    assert payload["not_expected_count"] == len(ALLOWED_ARCHIVE_ARTIFACT_FILENAMES)
    assert payload["all_verified"] is False


def test_archive_export_verification_summary_models_reject_inconsistent_metadata() -> (
    None
):
    with pytest.raises(ValidationError):
        ArchiveExportVerificationArtifact(
            kind="events_jsonl",
            filename="events.jsonl",
            expected_exists=True,
            exported_exists=True,
            expected_size_bytes=2,
            exported_size_bytes=3,
            status="verified",
        )

    artifact = ArchiveExportVerificationArtifact(
        kind="events_jsonl",
        filename="events.jsonl",
        expected_exists=True,
        exported_exists=True,
        expected_size_bytes=2,
        exported_size_bytes=2,
        status=ArchiveExportVerificationStatus.VERIFIED,
    )
    with pytest.raises(ValidationError):
        ArchiveExportVerificationSummary(
            session_id="session-001",
            session_dir="session-001",
            export_dir="session-001",
            expected_count=1,
            verified_count=1,
            missing_export_count=0,
            size_mismatch_count=0,
            unexpected_export_count=0,
            not_expected_count=0,
            all_verified=True,
            artifacts=[artifact],
        )


@pytest.mark.parametrize(
    "session_id",
    [
        "../session",
        "session/one",
        "session\\one",
        "C:session",
        "https://example.test/session",
        "CON",
        "lpt1.txt",
    ],
)
def test_archive_export_verification_rejects_unsafe_session_ids(
    tmp_path,
    session_id: str,
) -> None:
    archive_root = tmp_path / "archive-root"
    export_root = tmp_path / "export-root"
    archive_root.mkdir()
    export_root.mkdir()

    with pytest.raises(ValueError) as exc_info:
        build_archive_export_verification_summary_from_roots(
            archive_root,
            export_root,
            session_id,
        )

    assert str(exc_info.value) == "archive export verification could not be built"


def test_archive_export_verification_requires_existing_roots(tmp_path) -> None:
    archive_root = tmp_path / "archive-root"
    export_root = tmp_path / "export-root"
    archive_root.mkdir()
    export_root.mkdir()

    for missing_root, existing_root in (
        (tmp_path / "missing-archive-root", export_root),
        (archive_root, tmp_path / "missing-export-root"),
    ):
        with pytest.raises(ValueError) as exc_info:
            build_archive_export_verification_summary_from_roots(
                missing_root,
                existing_root,
                "session-001",
            )

        assert str(exc_info.value) == "archive export verification could not be built"


def test_archive_export_verification_rejects_export_root_inside_archive_root(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root"
    export_root = archive_root / "exports"
    archive_root.mkdir()
    export_root.mkdir()

    with pytest.raises(ValueError) as exc_info:
        build_archive_export_verification_summary_from_roots(
            archive_root,
            export_root,
            "session-001",
        )

    assert str(exc_info.value) == "archive export verification could not be built"


def test_archive_export_verification_sanitizes_errors(tmp_path) -> None:
    archive_root = tmp_path / "archive-root-token-secret-auth-profile"
    export_root = tmp_path / "export-root-token-secret-auth-profile"
    archive_root.write_text("Synthetic private archive placeholder.", encoding="utf-8")
    export_root.mkdir()

    with pytest.raises(ValueError) as exc_info:
        build_archive_export_verification_summary_from_roots(
            archive_root,
            export_root,
            "session-001",
        )

    error_text = str(exc_info.value)
    assert error_text == "archive export verification could not be built"
    for forbidden_fragment in (
        str(tmp_path),
        "archive-root",
        "export-root",
        "token",
        "secret",
        "auth",
        "profile",
        "Synthetic private",
    ):
        assert forbidden_fragment not in error_text


def test_archive_export_verification_rejects_session_symlink(tmp_path) -> None:
    archive_root = tmp_path / "archive-root"
    export_root = tmp_path / "export-root"
    outside_root = tmp_path / "outside-root-token-secret-auth-profile"
    archive_root.mkdir()
    export_root.mkdir()
    outside_root.mkdir()
    _make_symlink(outside_root, archive_root / "session-001", target_is_directory=True)

    with pytest.raises(ValueError) as exc_info:
        build_archive_export_verification_summary_from_roots(
            archive_root,
            export_root,
            "session-001",
        )

    assert str(exc_info.value) == "archive export verification could not be built"


def test_archive_export_verification_rejects_archive_artifact_symlink_escape(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root"
    export_root = tmp_path / "export-root"
    session_dir = archive_root / "session-001"
    outside_root = tmp_path / "outside-root-token-secret-auth-profile"
    session_dir.mkdir(parents=True)
    export_root.mkdir()
    outside_root.mkdir()
    outside_file = outside_root / "events.jsonl"
    outside_file.write_text("Synthetic outside event secret.", encoding="utf-8")
    _make_symlink(outside_file, session_dir / "events.jsonl")

    with pytest.raises(ValueError) as exc_info:
        build_archive_export_verification_summary_from_roots(
            archive_root,
            export_root,
            "session-001",
        )

    assert str(exc_info.value) == "archive export verification could not be built"


def test_archive_export_verification_rejects_export_artifact_symlink_escape(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root"
    export_root = tmp_path / "export-root"
    session_dir = archive_root / "session-001"
    exported_session_dir = export_root / "session-001"
    outside_root = tmp_path / "outside-root-token-secret-auth-profile"
    session_dir.mkdir(parents=True)
    exported_session_dir.mkdir(parents=True)
    outside_root.mkdir()
    (session_dir / "events.jsonl").write_text("{}", encoding="utf-8")
    outside_file = outside_root / "events.jsonl"
    outside_file.write_text("Synthetic outside event secret.", encoding="utf-8")
    _make_symlink(outside_file, exported_session_dir / "events.jsonl")

    with pytest.raises(ValueError) as exc_info:
        build_archive_export_verification_summary_from_roots(
            archive_root,
            export_root,
            "session-001",
        )

    assert str(exc_info.value) == "archive export verification could not be built"


def test_execute_archive_export_to_local_root_rejects_source_symlink_escape(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root"
    export_root = tmp_path / "export-root"
    session_dir = archive_root / "session-001"
    outside_root = tmp_path / "outside-root-token-secret-auth-profile"
    session_dir.mkdir(parents=True)
    outside_root.mkdir()
    export_root.mkdir()
    outside_file = outside_root / "events.jsonl"
    outside_file.write_text("Synthetic outside event secret.", encoding="utf-8")
    _make_symlink(outside_file, session_dir / "events.jsonl")

    with pytest.raises(ValueError) as exc_info:
        execute_archive_export_to_local_root(archive_root, export_root, "session-001")

    assert str(exc_info.value) == "archive export could not be executed"
    assert not (export_root / "session-001").exists()


def test_execute_archive_export_to_local_root_rejects_destination_symlink_escape(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root"
    export_root = tmp_path / "export-root"
    session_dir = archive_root / "session-001"
    outside_root = tmp_path / "outside-root-token-secret-auth-profile"
    session_dir.mkdir(parents=True)
    export_root.mkdir()
    outside_root.mkdir()
    (session_dir / "events.jsonl").write_text("{}", encoding="utf-8")
    _make_symlink(
        outside_root,
        export_root / "session-001",
        target_is_directory=True,
    )

    with pytest.raises(ValueError) as exc_info:
        execute_archive_export_to_local_root(archive_root, export_root, "session-001")

    assert str(exc_info.value) == "archive export could not be executed"
    assert not (outside_root / "events.jsonl").exists()


def test_archive_export_manifest_from_root_rejects_session_symlink_escape(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root"
    outside_root = tmp_path / "outside-root-token-secret-auth-profile"
    archive_root.mkdir()
    outside_root.mkdir()
    _make_symlink(outside_root, archive_root / "session-001", target_is_directory=True)

    with pytest.raises(ValueError) as exc_info:
        build_archive_export_manifest_from_root(archive_root, "session-001")

    error_text = str(exc_info.value)
    assert error_text == "archive export manifest could not be built"
    for unsafe_fragment in (str(tmp_path), "outside-root", "token", "secret", "auth"):
        assert unsafe_fragment not in error_text


def test_archive_export_manifest_from_root_rejects_artifact_symlink_escape(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive-root"
    session_dir = archive_root / "session-001"
    outside_root = tmp_path / "outside-root-token-secret-auth-profile"
    session_dir.mkdir(parents=True)
    outside_root.mkdir()
    outside_file = outside_root / "transcript.jsonl"
    outside_file.write_text("Synthetic outside transcript secret.", encoding="utf-8")
    _make_symlink(outside_file, session_dir / "transcript.jsonl")

    with pytest.raises(ValueError) as exc_info:
        build_archive_export_manifest_from_root(archive_root, "session-001")

    error_text = str(exc_info.value)
    assert error_text == "archive export manifest could not be built"
    for unsafe_fragment in (str(tmp_path), "outside-root", "secret", "transcript"):
        assert unsafe_fragment not in error_text


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
        "CON",
        "con.txt",
        "LPT1.session",
    ],
)
def test_archive_session_inventory_rejects_unsafe_session_ids(
    tmp_path,
    session_id: str,
) -> None:
    with pytest.raises((ValueError, ValidationError)):
        build_archive_session_inventory(tmp_path, session_id)


def test_archive_session_inventory_model_rejects_shape_drift() -> None:
    with pytest.raises(ValidationError):
        ArchiveSessionInventory(
            session_id="session-001",
            session_dir="session-001",
            artifacts=[
                {
                    "kind": "transcript_jsonl",
                    "filename": "transcript.jsonl",
                    "relative_path": "../transcript.jsonl",
                    "exists": False,
                    "absolute_path": "C:\\Users\\student\\transcript.jsonl",
                },
            ],
            archive_root="C:\\Users\\student\\archives",
        )


def test_archive_session_inventory_rejects_session_symlink_escape(tmp_path) -> None:
    archive_root = tmp_path / "archive-root"
    outside_root = tmp_path / "outside-root"
    archive_root.mkdir()
    outside_root.mkdir()
    _make_symlink(outside_root, archive_root / "session-001", target_is_directory=True)

    with pytest.raises(ValueError):
        build_archive_session_inventory(archive_root, "session-001")


def test_archive_session_inventory_rejects_artifact_symlink_escape(tmp_path) -> None:
    archive_root = tmp_path / "archive-root"
    session_dir = archive_root / "session-001"
    outside_root = tmp_path / "outside-root"
    session_dir.mkdir(parents=True)
    outside_root.mkdir()
    outside_file = outside_root / "transcript.jsonl"
    outside_text = "Synthetic outside transcript content that must not leak."
    outside_file.write_text(outside_text, encoding="utf-8")
    _make_symlink(outside_file, session_dir / "transcript.jsonl")

    with pytest.raises(ValueError):
        build_archive_session_inventory(archive_root, "session-001")


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


def test_archive_export_module_has_no_destructive_or_external_behavior() -> None:
    source = Path("src/async_scholar/archive_export.py").read_text(encoding="utf-8")

    forbidden_fragments = (
        "read_text(",
        "write_text(",
        "iterdir(",
        "glob(",
        "rglob(",
        "listdir(",
        "scandir(",
        "walk(",
        "unlink(",
        "remove(",
        "rmdir(",
        "rename(",
        "replace(",
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


def test_archive_manifest_from_inventory_helper_has_no_filesystem_io() -> None:
    source = Path("src/async_scholar/archive_export.py").read_text(encoding="utf-8")
    helper_source = source[
        source.index("def build_archive_export_manifest_from_inventory") : source.index(
            "\ndef build_archive_export_manifest_from_root"
        )
    ]

    forbidden_fragments = (
        "Path(",
        ".resolve(",
        ".exists(",
        ".is_file(",
        ".stat(",
        "open(",
        "read_text(",
        "write_text(",
        "mkdir(",
        "iterdir(",
        "glob(",
        "rglob(",
        "listdir(",
        "scandir(",
        "walk(",
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
        assert fragment not in helper_source


def test_archive_manifest_from_root_helper_has_no_content_or_execution_behavior() -> (
    None
):
    source = Path("src/async_scholar/archive_export.py").read_text(encoding="utf-8")
    helper_source = source[
        source.index("def build_archive_export_manifest_from_root") : source.index(
            "\ndef build_archive_export_preflight_summary_from_root"
        )
    ]

    forbidden_fragments = (
        "open(",
        "read_text(",
        "write_text(",
        "mkdir(",
        "iterdir(",
        "glob(",
        "rglob(",
        "listdir(",
        "scandir(",
        "walk(",
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
        assert fragment not in helper_source


def test_archive_preflight_from_root_helper_has_no_content_or_execution_behavior() -> (
    None
):
    source = Path("src/async_scholar/archive_export.py").read_text(encoding="utf-8")
    helper_source = source[
        source.index(
            "def build_archive_export_preflight_summary_from_root"
        ) : source.index("\ndef _archive_export_verification_status")
    ]

    forbidden_fragments = (
        "open(",
        "read_text(",
        "write_text(",
        "mkdir(",
        "iterdir(",
        "glob(",
        "rglob(",
        "listdir(",
        "scandir(",
        "walk(",
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
        "subprocess",
        "threading",
        "asyncio",
        "Timer(",
    )
    for fragment in forbidden_fragments:
        assert fragment not in helper_source


def test_archive_export_verification_helper_has_no_content_or_execution_behavior() -> (
    None
):
    source = Path("src/async_scholar/archive_export.py").read_text(encoding="utf-8")
    helper_source = source[
        source.index("def _archive_export_verification_status") : source.index(
            "\ndef _copy_file_exclusive"
        )
    ]

    forbidden_fragments = (
        "open(",
        "read_text(",
        "write_text(",
        "mkdir(",
        "iterdir(",
        "glob(",
        "rglob(",
        "listdir(",
        "scandir(",
        "walk(",
        "unlink(",
        "remove(",
        "rmdir(",
        "rename(",
        "replace(",
        "ZipFile",
        "zipfile",
        "tarfile",
        "shutil",
        "_copy_file_exclusive",
        "execute_archive_export_to_local_root",
        "sqlite3",
        "requests",
        "httpx",
        "playwright",
        "sounddevice",
        "faster_whisper",
        "nicegui",
        "subprocess",
        "threading",
        "asyncio",
        "Timer(",
    )
    for fragment in forbidden_fragments:
        assert fragment not in helper_source


def test_archive_export_execution_helper_has_no_destructive_or_external_behavior() -> (
    None
):
    source = Path("src/async_scholar/archive_export.py").read_text(encoding="utf-8")
    helper_source = source[
        source.index("def _copy_file_exclusive") : source.index(
            "\ndef archive_export_manifest_to_json_ready"
        )
    ]

    forbidden_fragments = (
        "read_text(",
        "write_text(",
        "iterdir(",
        "glob(",
        "rglob(",
        "listdir(",
        "scandir(",
        "walk(",
        "unlink(",
        "remove(",
        "rmdir(",
        "rename(",
        "replace(",
        "parents=True",
        "ZipFile",
        "zipfile",
        "tarfile",
        "shutil",
        "copyfile(",
        "copy2(",
        "sqlite3",
        "requests",
        "httpx",
        "playwright",
        "sounddevice",
        "faster_whisper",
        "nicegui",
        "subprocess",
        "threading",
        "asyncio",
        "Timer(",
    )
    for fragment in forbidden_fragments:
        assert fragment not in helper_source
    assert '.open("rb")' in helper_source
    assert '.open("xb")' in helper_source
    assert "parents=False" in helper_source


def _make_symlink(
    source: Path,
    link: Path,
    *,
    target_is_directory: bool = False,
) -> None:
    try:
        link.symlink_to(source, target_is_directory=target_is_directory)
    except (NotImplementedError, OSError) as error:
        pytest.skip(f"symlink creation is unavailable in this environment: {error}")
