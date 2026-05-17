import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from async_scholar import session_recovery
from async_scholar.archive_export import (
    ALLOWED_ARCHIVE_ARTIFACT_FILENAMES,
    ARCHIVE_ARTIFACT_FILENAMES_BY_KIND,
    ArchiveArtifactKind,
)
from async_scholar.session_recovery import (
    CRASH_RECOVERY_PREFLIGHT_ERROR,
    CrashRecoveryPreflightArtifact,
    CrashRecoverySessionPreflight,
    build_crash_recovery_session_preflight,
    crash_recovery_session_preflight_safe_summary,
    crash_recovery_session_preflight_to_json_ready,
)


def _write_artifact(session_dir: Path, filename: str, text: str = "{}") -> None:
    (session_dir / filename).write_text(text, encoding="utf-8")


def _artifact_filenames(payload: dict[str, object]) -> list[str]:
    return [artifact["filename"] for artifact in payload["artifacts"]]


def test_crash_recovery_preflight_reports_partial_session_metadata(tmp_path) -> None:
    session_dir = tmp_path / "session-001"
    session_dir.mkdir()
    events_text = "{}"
    reviewer_text = "Synthetic reviewer private text must not be serialized."
    _write_artifact(session_dir, "events.jsonl", events_text)
    _write_artifact(session_dir, "reviewer.md", reviewer_text)

    preflight = build_crash_recovery_session_preflight(tmp_path, "session-001")
    payload = crash_recovery_session_preflight_to_json_ready(preflight)

    assert isinstance(preflight, CrashRecoverySessionPreflight)
    assert payload == crash_recovery_session_preflight_safe_summary(preflight)
    assert payload["preflight_kind"] == "crash_recovery_session_preflight"
    assert payload["session_id"] == "session-001"
    assert payload["session_dir"] == "session-001"
    assert payload["recovery_status"] == "partial"
    assert payload["existing_count"] == 2
    assert payload["missing_count"] == len(ALLOWED_ARCHIVE_ARTIFACT_FILENAMES) - 2
    assert payload["total_existing_size_bytes"] == len(
        events_text.encode("utf-8")
    ) + len(reviewer_text.encode("utf-8"))
    assert _artifact_filenames(payload) == list(ALLOWED_ARCHIVE_ARTIFACT_FILENAMES)
    assert payload["artifacts"][2] == {
        "kind": "events_jsonl",
        "filename": "events.jsonl",
        "exists": True,
        "size_bytes": len(events_text.encode("utf-8")),
    }
    assert payload["artifacts"][4] == {
        "kind": "reviewer_markdown",
        "filename": "reviewer.md",
        "exists": True,
        "size_bytes": len(reviewer_text.encode("utf-8")),
    }
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload

    serialized_payload = json.dumps(payload, sort_keys=True).lower()
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "synthetic reviewer",
        "private text",
        "c:\\",
        "/users/",
    ):
        assert forbidden_fragment not in serialized_payload


def test_crash_recovery_preflight_reports_empty_session(tmp_path) -> None:
    preflight = build_crash_recovery_session_preflight(tmp_path, "session-001")
    payload = preflight.to_json_ready()

    assert payload["recovery_status"] == "empty"
    assert payload["existing_count"] == 0
    assert payload["missing_count"] == len(ALLOWED_ARCHIVE_ARTIFACT_FILENAMES)
    assert payload["total_existing_size_bytes"] == 0
    assert all(not artifact["exists"] for artifact in payload["artifacts"])


def test_crash_recovery_preflight_reports_complete_session(tmp_path) -> None:
    session_dir = tmp_path / "session-001"
    session_dir.mkdir()
    total_size = 0
    for filename in ALLOWED_ARCHIVE_ARTIFACT_FILENAMES:
        text = f"{filename}-metadata-only-fixture"
        total_size += len(text.encode("utf-8"))
        _write_artifact(session_dir, filename, text)

    payload = build_crash_recovery_session_preflight(
        tmp_path,
        "session-001",
    ).to_json_ready()

    assert payload["recovery_status"] == "complete"
    assert payload["existing_count"] == len(ALLOWED_ARCHIVE_ARTIFACT_FILENAMES)
    assert payload["missing_count"] == 0
    assert payload["total_existing_size_bytes"] == total_size


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
def test_crash_recovery_preflight_rejects_unsafe_session_ids(
    tmp_path,
    session_id: str,
) -> None:
    with pytest.raises(ValueError) as exc_info:
        build_crash_recovery_session_preflight(tmp_path, session_id)

    assert str(exc_info.value) == CRASH_RECOVERY_PREFLIGHT_ERROR


def test_crash_recovery_preflight_sanitizes_path_and_metadata_errors(tmp_path) -> None:
    unsafe_root = tmp_path / "root-token-secret-auth-profile"
    unsafe_root.write_text("Synthetic private root placeholder.", encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        build_crash_recovery_session_preflight(unsafe_root, "session-001")

    error_text = str(exc_info.value)
    assert error_text == CRASH_RECOVERY_PREFLIGHT_ERROR
    for unsafe_fragment in (
        str(tmp_path),
        "root-token",
        "secret",
        "auth",
        "profile",
        "Synthetic private",
    ):
        assert unsafe_fragment not in error_text


def test_crash_recovery_preflight_ignores_unallowlisted_files(tmp_path) -> None:
    session_dir = tmp_path / "session-001"
    session_dir.mkdir()
    _write_artifact(session_dir, "private-notes.txt", "Synthetic private notes.")

    payload = build_crash_recovery_session_preflight(
        tmp_path,
        "session-001",
    ).to_json_ready()
    serialized_payload = json.dumps(payload, sort_keys=True)

    assert _artifact_filenames(payload) == list(ALLOWED_ARCHIVE_ARTIFACT_FILENAMES)
    assert "private-notes.txt" not in serialized_payload
    assert "Synthetic private notes" not in serialized_payload


def test_crash_recovery_preflight_model_rejects_shape_drift() -> None:
    with pytest.raises(ValidationError):
        CrashRecoverySessionPreflight(
            session_id="session-001",
            session_dir="session-001",
            recovery_status="partial",
            existing_count=1,
            missing_count=len(ALLOWED_ARCHIVE_ARTIFACT_FILENAMES) - 1,
            total_existing_size_bytes=2,
            artifacts=[
                {
                    "kind": "transcript_jsonl",
                    "filename": "transcript.jsonl",
                    "exists": True,
                    "size_bytes": 2,
                    "absolute_path": "C:\\Users\\student\\transcript.jsonl",
                }
            ],
            repair_allowed=True,
        )


def test_crash_recovery_preflight_model_rejects_unsafe_session_metadata() -> None:
    artifacts = tuple(
        CrashRecoveryPreflightArtifact(
            kind=kind,
            filename=filename,
            exists=False,
        )
        for kind, filename in ARCHIVE_ARTIFACT_FILENAMES_BY_KIND.items()
    )

    with pytest.raises(ValidationError):
        CrashRecoverySessionPreflight(
            session_id="C:/Users/student/session-001",
            session_dir="C:/Users/student/session-001",
            recovery_status="empty",
            existing_count=0,
            missing_count=len(artifacts),
            total_existing_size_bytes=0,
            artifacts=artifacts,
        )

    with pytest.raises(ValidationError):
        CrashRecoverySessionPreflight(
            session_id="CON",
            session_dir="CON",
            recovery_status="empty",
            existing_count=0,
            missing_count=len(artifacts),
            total_existing_size_bytes=0,
            artifacts=artifacts,
        )


def test_crash_recovery_preflight_model_rejects_status_drift() -> None:
    artifacts = tuple(
        CrashRecoveryPreflightArtifact(
            kind=kind,
            filename=filename,
            exists=False,
        )
        for kind, filename in ARCHIVE_ARTIFACT_FILENAMES_BY_KIND.items()
    )

    with pytest.raises(ValidationError):
        CrashRecoverySessionPreflight(
            session_id="session-001",
            session_dir="session-001",
            recovery_status="complete",
            existing_count=0,
            missing_count=len(artifacts),
            total_existing_size_bytes=0,
            artifacts=artifacts,
        )


def test_crash_recovery_artifact_model_rejects_inconsistent_metadata() -> None:
    with pytest.raises(ValidationError):
        CrashRecoveryPreflightArtifact(
            kind=ArchiveArtifactKind.EVENTS_JSONL,
            filename="transcript.jsonl",
            exists=False,
        )

    with pytest.raises(ValidationError):
        CrashRecoveryPreflightArtifact(
            kind=ArchiveArtifactKind.TRANSCRIPT_JSONL,
            filename="transcript.jsonl",
            exists=True,
        )

    with pytest.raises(ValidationError):
        CrashRecoveryPreflightArtifact(
            kind=ArchiveArtifactKind.TRANSCRIPT_JSONL,
            filename="transcript.jsonl",
            exists=False,
            size_bytes=1,
        )


def test_crash_recovery_preflight_is_immutable(tmp_path) -> None:
    preflight = build_crash_recovery_session_preflight(tmp_path, "session-001")

    with pytest.raises(ValidationError):
        preflight.recovery_status = "complete"
    with pytest.raises(AttributeError):
        preflight.artifacts.append(
            CrashRecoveryPreflightArtifact(
                kind=ArchiveArtifactKind.TRANSCRIPT_JSONL,
                filename="transcript.jsonl",
                exists=False,
            )
        )
    with pytest.raises(ValidationError):
        preflight.artifacts[0].exists = True


def test_crash_recovery_preflight_exposes_no_content_or_private_data(tmp_path) -> None:
    session_dir = tmp_path / "session-001"
    session_dir.mkdir()
    private_text = "Synthetic transcript token secret auth profile payload."
    _write_artifact(session_dir, "transcript.jsonl", private_text)

    payload = build_crash_recovery_session_preflight(
        tmp_path,
        "session-001",
    ).to_json_ready()
    serialized_payload = json.dumps(payload, sort_keys=True).lower()

    for forbidden_fragment in (
        str(tmp_path).lower(),
        "synthetic transcript",
        "token",
        "secret",
        "auth",
        "profile",
        "payload",
        "absolute_path",
        "root",
        "home",
        "repair",
        "delete",
        "copy",
        "export",
        "sqlite",
        "scheduler",
        "timer",
    ):
        assert forbidden_fragment not in serialized_payload


def test_crash_recovery_safe_helpers_reject_constructed_preflight_leakage() -> None:
    if not hasattr(CrashRecoverySessionPreflight, "model_construct"):
        pytest.skip("Pydantic model_construct is not available")

    unsafe_fragments = (
        "C:",
        "Users",
        "student",
        "session-token",
        "secret",
        "auth",
        "profile",
    )
    unsafe_artifact = CrashRecoveryPreflightArtifact.model_construct(
        kind=ArchiveArtifactKind.TRANSCRIPT_JSONL,
        filename="C:/Users/student/transcript-token-secret-auth-profile.jsonl",
        exists=True,
        size_bytes=1,
    )
    unsafe_preflight = CrashRecoverySessionPreflight.model_construct(
        preflight_kind="crash_recovery_session_preflight",
        session_id="C:/Users/student/session-token-secret-auth-profile",
        session_dir="C:/Users/student/session-token-secret-auth-profile",
        recovery_status="complete",
        existing_count=1,
        missing_count=0,
        total_existing_size_bytes=1,
        artifacts=(unsafe_artifact,),
    )

    for helper in (
        unsafe_preflight.to_json_ready,
        unsafe_preflight.safe_summary,
        lambda: crash_recovery_session_preflight_to_json_ready(unsafe_preflight),
        lambda: crash_recovery_session_preflight_safe_summary(unsafe_preflight),
    ):
        with pytest.raises(ValueError) as exc_info:
            helper()

        error_text = str(exc_info.value)
        assert error_text == CRASH_RECOVERY_PREFLIGHT_ERROR
        for unsafe_fragment in unsafe_fragments:
            assert unsafe_fragment not in error_text


def test_crash_recovery_artifact_safe_helper_rejects_constructed_leakage() -> None:
    if not hasattr(CrashRecoveryPreflightArtifact, "model_construct"):
        pytest.skip("Pydantic model_construct is not available")

    unsafe_artifact = CrashRecoveryPreflightArtifact.model_construct(
        kind=ArchiveArtifactKind.TRANSCRIPT_JSONL,
        filename="C:/Users/student/transcript-token-secret-auth-profile.jsonl",
        exists=True,
        size_bytes=1,
    )

    with pytest.raises(ValueError) as exc_info:
        unsafe_artifact.to_json_ready()

    error_text = str(exc_info.value)
    assert error_text == CRASH_RECOVERY_PREFLIGHT_ERROR
    for unsafe_fragment in ("C:", "Users", "student", "token", "secret", "auth"):
        assert unsafe_fragment not in error_text


def test_crash_recovery_preflight_rejects_session_symlink_escape(tmp_path) -> None:
    outside_root = tmp_path / "outside-root-token-secret-auth-profile"
    outside_root.mkdir()
    _make_symlink(outside_root, tmp_path / "session-001", target_is_directory=True)

    with pytest.raises(ValueError) as exc_info:
        build_crash_recovery_session_preflight(tmp_path, "session-001")

    assert str(exc_info.value) == CRASH_RECOVERY_PREFLIGHT_ERROR


def test_crash_recovery_preflight_rejects_artifact_symlink_escape(tmp_path) -> None:
    session_dir = tmp_path / "session-001"
    outside_root = tmp_path / "outside-root-token-secret-auth-profile"
    session_dir.mkdir()
    outside_root.mkdir()
    outside_file = outside_root / "transcript.jsonl"
    outside_file.write_text("Synthetic outside transcript secret.", encoding="utf-8")
    _make_symlink(outside_file, session_dir / "transcript.jsonl")

    with pytest.raises(ValueError) as exc_info:
        build_crash_recovery_session_preflight(tmp_path, "session-001")

    assert str(exc_info.value) == CRASH_RECOVERY_PREFLIGHT_ERROR


def test_session_recovery_module_has_no_content_io_or_execution_behavior() -> None:
    source = Path(session_recovery.__file__).read_text(encoding="utf-8")

    forbidden_fragments = (
        "open(",
        "read_text(",
        "read_bytes(",
        "write_text(",
        "write_bytes(",
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
        "mkdir(",
        "json.loads",
        "jsonl",
        "transcript parsing",
        "log parsing",
        "sqlite",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "nicegui",
        "subprocess",
        "threading",
        "asyncio",
        "timer",
        "sleep(",
        "notification",
        "telegram",
        "desktop_notifier",
        "execute_archive_export",
        "delete",
        "repair",
    )

    normalized_source = source.lower()
    for fragment in forbidden_fragments:
        assert fragment.lower() not in normalized_source


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
