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
    ARCHIVE_DELETE_DRY_RUN_LOCAL_ERROR,
    ARCHIVE_DELETE_DRY_RUN_RESULT_KIND,
    ARCHIVE_DELETE_DRY_RUN_RESULT_STATUS,
    ArchiveDeleteDryRunLocalArtifact,
    ArchiveDeleteDryRunLocalResult,
    ArchiveDeleteDryRunResult,
    ArchiveDeleteDryRunResultArtifact,
    build_archive_delete_dry_run_local_result,
    build_archive_delete_dry_run_result,
    export_archive_delete_dry_run_local_result,
    export_archive_delete_dry_run_result,
    summarize_archive_delete_dry_run_result,
)
from async_scholar.archive_export import (
    ALLOWED_ARCHIVE_ARTIFACT_FILENAMES,
    ArchiveArtifactKind,
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
        "CON",
        "LPT1.session",
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


def test_build_local_dry_run_result_returns_safe_metadata(tmp_path: Path) -> None:
    archive_root = tmp_path / "archive-token-secret-auth-profile"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    event_text = "Synthetic event token secret auth profile payload."
    reviewer_text = "Synthetic reviewer private payload."
    (session_dir / "events.jsonl").write_text(event_text, encoding="utf-8")
    (session_dir / "reviewer.md").write_text(reviewer_text, encoding="utf-8")

    result = build_archive_delete_dry_run_local_result(
        archive_root,
        "session-001",
    )
    payload = export_archive_delete_dry_run_local_result(result)

    assert result.session_id == "session-001"
    assert result.session_dir == "session-001"
    assert result.result_kind == ARCHIVE_DELETE_DRY_RUN_RESULT_KIND
    assert result.status == ARCHIVE_DELETE_DRY_RUN_RESULT_STATUS
    assert result.dry_run_only is True
    assert result.deletion_performed is False
    assert result.artifact_count == len(ALLOWED_ARCHIVE_ARTIFACT_FILENAMES)
    assert result.existing_artifact_count == 2
    assert result.total_existing_size_bytes == len(
        event_text.encode("utf-8"),
    ) + len(reviewer_text.encode("utf-8"))
    assert [artifact.filename for artifact in result.artifacts] == list(
        ALLOWED_ARCHIVE_ARTIFACT_FILENAMES,
    )
    assert payload["session_id"] == "session-001"
    assert payload["session_dir"] == "session-001"
    assert payload["dry_run_only"] is True
    assert payload["deletion_performed"] is False
    assert payload["artifact_count"] == len(ALLOWED_ARCHIVE_ARTIFACT_FILENAMES)
    assert payload["existing_artifact_count"] == 2
    assert payload["total_existing_size_bytes"] == result.total_existing_size_bytes
    assert [artifact["filename"] for artifact in payload["artifacts"]] == list(
        ALLOWED_ARCHIVE_ARTIFACT_FILENAMES,
    )
    assert payload["artifacts"][2] == {
        "kind": "events_jsonl",
        "filename": "events.jsonl",
        "exists": True,
        "size_bytes": len(event_text.encode("utf-8")),
        "action": "would_delete",
        "status": "not_deleted",
    }
    assert payload["artifacts"][4] == {
        "kind": "reviewer_markdown",
        "filename": "reviewer.md",
        "exists": True,
        "size_bytes": len(reviewer_text.encode("utf-8")),
        "action": "would_delete",
        "status": "not_deleted",
    }
    for artifact in payload["artifacts"]:
        if artifact["exists"] is False:
            assert "size_bytes" not in artifact
        assert artifact["action"] == "would_delete"
        assert artifact["status"] == "not_deleted"

    exported_text = json.dumps(payload).lower()
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "archive-token",
        "synthetic event",
        "synthetic reviewer",
        "token",
        "secret",
        "auth",
        "profile",
        "payload",
        "c:\\",
        "/users",
        "traceback",
    ):
        assert forbidden_fragment not in exported_text


def test_local_dry_run_reports_missing_session_as_empty(tmp_path: Path) -> None:
    result = build_archive_delete_dry_run_local_result(tmp_path, "session-001")
    payload = export_archive_delete_dry_run_local_result(result)

    assert payload["session_id"] == "session-001"
    assert payload["session_dir"] == "session-001"
    assert payload["dry_run_only"] is True
    assert payload["deletion_performed"] is False
    assert payload["artifact_count"] == len(ALLOWED_ARCHIVE_ARTIFACT_FILENAMES)
    assert payload["existing_artifact_count"] == 0
    assert payload["total_existing_size_bytes"] == 0
    assert [artifact["filename"] for artifact in payload["artifacts"]] == list(
        ALLOWED_ARCHIVE_ARTIFACT_FILENAMES,
    )
    assert all(artifact["exists"] is False for artifact in payload["artifacts"])
    assert all("size_bytes" not in artifact for artifact in payload["artifacts"])


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
        "CON",
        "LPT1.session",
    ],
)
def test_local_dry_run_rejects_unsafe_session_ids(
    tmp_path: Path,
    session_id: str,
) -> None:
    with pytest.raises(ValueError, match=f"^{ARCHIVE_DELETE_DRY_RUN_LOCAL_ERROR}$"):
        build_archive_delete_dry_run_local_result(tmp_path, session_id)


def test_local_dry_run_rejects_missing_or_non_directory_root(tmp_path: Path) -> None:
    missing_root = tmp_path / "missing-token-secret-auth-profile"
    file_root = tmp_path / "file-token-secret-auth-profile"
    file_root.write_text("Synthetic private root placeholder.", encoding="utf-8")

    for archive_root in (missing_root, file_root):
        with pytest.raises(ValueError) as exc_info:
            build_archive_delete_dry_run_local_result(archive_root, "session-001")

        assert str(exc_info.value) == ARCHIVE_DELETE_DRY_RUN_LOCAL_ERROR
        for forbidden_fragment in (
            str(tmp_path),
            "token",
            "secret",
            "auth",
            "profile",
            "Synthetic private",
            "Traceback",
        ):
            assert forbidden_fragment not in str(exc_info.value)


@pytest.mark.parametrize(
    "archive_root",
    [
        "\\\\server\\share\\token-secret-auth-profile",
        "//server/share/token-secret-auth-profile",
    ],
)
def test_local_dry_run_rejects_unc_roots_before_metadata_probes(
    monkeypatch: pytest.MonkeyPatch,
    archive_root: str,
) -> None:
    probe_calls: list[str] = []

    def fail_if_probe_runs(self: Path) -> bool:
        probe_calls.append(str(self))
        raise AssertionError("network roots must be rejected before metadata probes")

    monkeypatch.setattr(Path, "exists", fail_if_probe_runs)
    monkeypatch.setattr(Path, "is_dir", fail_if_probe_runs)
    monkeypatch.setattr(Path, "is_file", fail_if_probe_runs)
    monkeypatch.setattr(Path, "is_symlink", fail_if_probe_runs)

    with pytest.raises(ValueError) as exc_info:
        build_archive_delete_dry_run_local_result(archive_root, "session-001")

    assert str(exc_info.value) == ARCHIVE_DELETE_DRY_RUN_LOCAL_ERROR
    assert probe_calls == []
    for forbidden_fragment in (
        "server",
        "share",
        "token",
        "secret",
        "auth",
        "profile",
        "Traceback",
    ):
        assert forbidden_fragment not in str(exc_info.value)


def test_local_dry_run_rejects_root_symlink(tmp_path: Path) -> None:
    real_root = tmp_path / "real-root"
    symlink_root = tmp_path / "root-symlink"
    real_root.mkdir()
    _symlink_to(real_root, symlink_root, target_is_directory=True)

    with pytest.raises(ValueError, match=f"^{ARCHIVE_DELETE_DRY_RUN_LOCAL_ERROR}$"):
        build_archive_delete_dry_run_local_result(symlink_root, "session-001")


def test_local_dry_run_rejects_session_symlink(tmp_path: Path) -> None:
    real_session = tmp_path / "real-session"
    real_session.mkdir()
    _symlink_to(real_session, tmp_path / "session-001", target_is_directory=True)

    with pytest.raises(ValueError, match=f"^{ARCHIVE_DELETE_DRY_RUN_LOCAL_ERROR}$"):
        build_archive_delete_dry_run_local_result(tmp_path, "session-001")


def test_local_dry_run_rejects_artifact_symlink_escape(tmp_path: Path) -> None:
    session_dir = tmp_path / "session-001"
    outside_file = tmp_path / "outside-token-secret-auth-profile.jsonl"
    session_dir.mkdir()
    outside_file.write_text("Synthetic private outside file.", encoding="utf-8")
    _symlink_to(outside_file, session_dir / "events.jsonl")

    with pytest.raises(ValueError, match=f"^{ARCHIVE_DELETE_DRY_RUN_LOCAL_ERROR}$"):
        build_archive_delete_dry_run_local_result(tmp_path, "session-001")


def test_local_dry_run_rejects_artifact_directory(tmp_path: Path) -> None:
    session_dir = tmp_path / "session-001"
    session_dir.mkdir()
    (session_dir / "events.jsonl").mkdir()

    with pytest.raises(ValueError, match=f"^{ARCHIVE_DELETE_DRY_RUN_LOCAL_ERROR}$"):
        build_archive_delete_dry_run_local_result(tmp_path, "session-001")


def test_local_dry_run_model_rejects_mismatched_metadata() -> None:
    with pytest.raises(ValidationError):
        ArchiveDeleteDryRunLocalArtifact(
            kind=ArchiveArtifactKind.EVENTS_JSONL,
            filename="reviewer.md",
            exists=True,
            size_bytes=1,
        )

    valid_artifacts = tuple(
        ArchiveDeleteDryRunLocalArtifact(
            kind=kind,
            filename=filename,
            exists=False,
        )
        for kind, filename in [
            (ArchiveArtifactKind.EVENTS_JSONL, "events.jsonl"),
            (ArchiveArtifactKind.TRANSCRIPT_JSONL, "transcript.jsonl"),
        ]
    )
    with pytest.raises(ValidationError):
        ArchiveDeleteDryRunLocalResult(
            session_id="session-001",
            session_dir="session-001",
            artifact_count=len(valid_artifacts),
            existing_artifact_count=0,
            total_existing_size_bytes=0,
            artifacts=valid_artifacts,
        )


def test_local_dry_run_export_rejects_non_result_and_revalidates() -> None:
    class LocalResultSubclass(ArchiveDeleteDryRunLocalResult):
        pass

    valid_result = build_archive_delete_dry_run_local_result(Path.cwd(), "session-001")
    subclassed_result = LocalResultSubclass.model_validate(valid_result.model_dump())
    for value in (None, {}, [], "result", object(), subclassed_result):
        with pytest.raises(TypeError):
            export_archive_delete_dry_run_local_result(value)  # type: ignore[arg-type]

    tampered_result = ArchiveDeleteDryRunLocalResult.model_construct(
        session_id="session-001",
        session_dir="session-001",
        result_kind=ARCHIVE_DELETE_DRY_RUN_RESULT_KIND,
        status=ARCHIVE_DELETE_DRY_RUN_RESULT_STATUS,
        dry_run_only=True,
        deletion_performed=True,
        artifact_count=1,
        existing_artifact_count=0,
        total_existing_size_bytes=0,
        artifacts=(
            ArchiveDeleteDryRunLocalArtifact.model_construct(
                kind=ArchiveArtifactKind.TRANSCRIPT_JSONL,
                filename="transcript.jsonl",
                exists=False,
                size_bytes=None,
                action="would_delete",
                status="not_deleted",
            ),
        ),
    )

    with pytest.raises(ValidationError):
        export_archive_delete_dry_run_local_result(tampered_result)


def _symlink_to(
    target: Path,
    link: Path,
    *,
    target_is_directory: bool = False,
) -> None:
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")


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
        "iterdir",
        "glob",
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
