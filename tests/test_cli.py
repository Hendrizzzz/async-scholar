from __future__ import annotations

import inspect
import json
import subprocess
import sys
import types
from pathlib import Path

from async_scholar import __main__ as cli


def test_module_help_prints_useful_output() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "async_scholar", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar" in result.stdout
    assert "local-first lecture monitoring" in result.stdout
    assert "--version" in result.stdout
    assert "crash-recovery-preflight" in result.stdout
    assert "archive-export-preflight" in result.stdout
    assert "archive-export-local" in result.stdout
    assert "archive-export-verify-local" in result.stdout
    assert "archive-delete-dry-run-local" in result.stdout
    assert "scheduled-start-preview-local" in result.stdout
    assert "mic-recording-diagnostic" in result.stdout


def test_mic_recording_diagnostic_help_prints_existing_options() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "mic-recording-diagnostic",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "--output-root" in result.stdout
    assert "--seconds" in result.stdout
    assert "--max-chunks" in result.stdout
    assert "--device-id" in result.stdout


def test_build_parser_does_not_import_mic_recording_diagnostic(
    monkeypatch,
) -> None:
    module_name = "async_scholar.audio.mic_recording_diagnostic"
    monkeypatch.delitem(sys.modules, module_name, raising=False)

    cli.build_parser()

    assert module_name not in sys.modules


def test_crash_recovery_preflight_help_does_not_build_preflight(
    monkeypatch,
) -> None:
    module_name = "async_scholar.session_recovery"
    monkeypatch.delitem(sys.modules, module_name, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "crash-recovery-preflight",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar crash-recovery-preflight" in result.stdout
    assert "--sessions-root" in result.stdout
    assert "metadata" in result.stdout
    assert module_name not in sys.modules


def test_crash_recovery_preflight_requires_explicit_sessions_root() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "crash-recovery-preflight",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "crash recovery session preflight could not be built\n"


def test_crash_recovery_preflight_sanitizes_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "crash-recovery-preflight",
            "session-001",
            "C:\\Users\\student\\token-secret-auth-profile",
            "--sessions-root",
            ".",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "crash recovery session preflight could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "unrecognized arguments",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_crash_recovery_preflight_sanitizes_misordered_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--sessions-root",
            "C:\\Users\\student\\token-secret-auth-profile",
            "crash-recovery-preflight",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "crash recovery session preflight could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_crash_recovery_preflight_sanitizes_equals_form_parent_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--sessions-root=C:\\Users\\student\\token-secret-auth-profile",
            "fixture-demo",
            "tests/fixtures/transcripts/attendance_roll_call.jsonl",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "crash recovery session preflight could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_crash_recovery_preflight_command_prints_safe_json(tmp_path) -> None:
    session_dir = tmp_path / "session-001"
    session_dir.mkdir()
    transcript_text = "Synthetic transcript token secret auth profile payload."
    event_text = "Synthetic event private payload."
    alert_text = "Synthetic alert private payload."
    reviewer_text = "Synthetic reviewer private payload."
    (session_dir / "transcript.jsonl").write_text(
        transcript_text,
        encoding="utf-8",
    )
    (session_dir / "events.jsonl").write_text(event_text, encoding="utf-8")
    (session_dir / "alerts.log").write_text(alert_text, encoding="utf-8")
    (session_dir / "reviewer.md").write_text(reviewer_text, encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "crash-recovery-preflight",
            "session-001",
            "--sessions-root",
            str(tmp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    payload = json.loads(result.stdout)
    assert payload["preflight_kind"] == "crash_recovery_session_preflight"
    assert payload["session_id"] == "session-001"
    assert payload["session_dir"] == "session-001"
    assert payload["recovery_status"] == "partial"
    assert payload["existing_count"] == 4
    assert payload["missing_count"] == 3
    assert payload["total_existing_size_bytes"] == sum(
        len(text.encode("utf-8"))
        for text in (transcript_text, event_text, alert_text, reviewer_text)
    )
    assert [artifact["filename"] for artifact in payload["artifacts"]] == [
        "transcript.jsonl",
        "transcript.md",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
        "runtime.jsonl",
        "benchmark-report.json",
    ]

    combined_output = f"{result.stdout}\n{result.stderr}".lower()
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "synthetic transcript",
        "synthetic event",
        "synthetic alert",
        "synthetic reviewer",
        "token",
        "secret",
        "auth",
        "profile",
        "payload",
        "repair",
        "delete",
        "scheduler",
        "traceback",
    ):
        assert forbidden_fragment not in combined_output


def test_crash_recovery_preflight_command_sanitizes_failures(tmp_path) -> None:
    unsafe_root = tmp_path / "root-token-secret-auth-profile"
    unsafe_root.write_text("Synthetic private root placeholder.", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "crash-recovery-preflight",
            "session-001",
            "--sessions-root",
            str(unsafe_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "crash recovery session preflight could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "root-token",
        "secret",
        "auth",
        "profile",
        "Synthetic private",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_preflight_help_does_not_build_preflight(
    monkeypatch,
) -> None:
    module_name = "async_scholar.archive_export"
    monkeypatch.delitem(sys.modules, module_name, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-preflight",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar archive-export-preflight" in result.stdout
    assert "--archive-root" in result.stdout
    assert "metadata" in result.stdout
    assert module_name not in sys.modules


def test_archive_export_preflight_requires_explicit_archive_root() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-preflight",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "archive export preflight could not be built\n"


def test_archive_export_preflight_sanitizes_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-preflight",
            "session-001",
            "C:\\Users\\student\\token-secret-auth-profile",
            "--archive-root",
            ".",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "archive export preflight could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "unrecognized arguments",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_preflight_sanitizes_misordered_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--archive-root",
            "C:\\Users\\student\\token-secret-auth-profile",
            "archive-export-preflight",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "archive export preflight could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_preflight_sanitizes_equals_form_parent_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--archive-root=C:\\Users\\student\\token-secret-auth-profile",
            "fixture-demo",
            "tests/fixtures/transcripts/attendance_roll_call.jsonl",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "archive export preflight could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_preflight_command_prints_safe_json(tmp_path) -> None:
    session_dir = tmp_path / "session-001"
    session_dir.mkdir()
    transcript_text = "Synthetic transcript token secret auth profile payload."
    event_text = "Synthetic event private payload."
    alert_text = "Synthetic alert private payload."
    reviewer_text = "Synthetic reviewer private payload."
    (session_dir / "transcript.jsonl").write_text(
        transcript_text,
        encoding="utf-8",
    )
    (session_dir / "events.jsonl").write_text(event_text, encoding="utf-8")
    (session_dir / "alerts.log").write_text(alert_text, encoding="utf-8")
    (session_dir / "reviewer.md").write_text(reviewer_text, encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-preflight",
            "session-001",
            "--archive-root",
            str(tmp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    payload = json.loads(result.stdout)
    assert payload["session_id"] == "session-001"
    assert payload["session_dir"] == "session-001"
    assert payload["existing_count"] == 4
    assert payload["missing_count"] == 3
    assert payload["total_existing_size_bytes"] == sum(
        len(text.encode("utf-8"))
        for text in (transcript_text, event_text, alert_text, reviewer_text)
    )
    assert [artifact["filename"] for artifact in payload["artifacts"]] == [
        "transcript.jsonl",
        "transcript.md",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
        "runtime.jsonl",
        "benchmark-report.json",
    ]

    combined_output = f"{result.stdout}\n{result.stderr}".lower()
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "synthetic transcript",
        "synthetic event",
        "synthetic alert",
        "synthetic reviewer",
        "token",
        "secret",
        "auth",
        "profile",
        "payload",
        "copy",
        "delete",
        "scheduler",
        "traceback",
    ):
        assert forbidden_fragment not in combined_output


def test_archive_export_preflight_command_sanitizes_failures(tmp_path) -> None:
    unsafe_root = tmp_path / "root-token-secret-auth-profile"
    unsafe_root.write_text("Synthetic private root placeholder.", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-preflight",
            "session-001",
            "--archive-root",
            str(unsafe_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "archive export preflight could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "root-token",
        "secret",
        "auth",
        "profile",
        "Synthetic private",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_preflight_command_delegates_to_existing_helpers(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    module_name = "async_scholar.archive_export"
    fake_module = types.ModuleType(module_name)
    fake_preflight = object()

    def fake_build(archive_root: Path, session_id: str) -> object:
        received["archive_root"] = archive_root
        received["session_id"] = session_id
        return fake_preflight

    def fake_summary(preflight: object) -> dict[str, object]:
        received["preflight"] = preflight
        return {"session_id": "session-001", "existing_count": 0}

    fake_module.build_archive_export_preflight_summary_from_root = fake_build
    fake_module.archive_export_preflight_summary_safe_summary = fake_summary
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(
        [
            "archive-export-preflight",
            "session-001",
            "--archive-root",
            "archive-root",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "existing_count": 0,
        "session_id": "session-001",
    }
    assert captured.err == ""
    assert received == {
        "archive_root": Path("archive-root"),
        "session_id": "session-001",
        "preflight": fake_preflight,
    }


def test_archive_export_local_help_does_not_execute_export(
    monkeypatch,
) -> None:
    module_name = "async_scholar.archive_export"
    monkeypatch.delitem(sys.modules, module_name, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar archive-export-local" in result.stdout
    assert "--archive-root" in result.stdout
    assert "--export-root" in result.stdout
    assert module_name not in sys.modules


def test_archive_export_local_requires_explicit_roots() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "archive export could not be executed\n"


def test_archive_export_local_sanitizes_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-local",
            "session-001",
            "C:\\Users\\student\\token-secret-auth-profile",
            "--archive-root",
            ".",
            "--export-root",
            ".",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "archive export could not be executed\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "unrecognized arguments",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_local_sanitizes_misordered_archive_root_failure() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--archive-root",
            "C:\\Users\\student\\token-secret-auth-profile",
            "archive-export-local",
            "session-001",
            "--export-root",
            ".",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "archive export could not be executed\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_local_sanitizes_misordered_export_root_failure() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--export-root=C:\\Users\\student\\token-secret-auth-profile",
            "fixture-demo",
            "tests/fixtures/transcripts/attendance_roll_call.jsonl",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "archive export could not be executed\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_local_command_prints_safe_json_and_copies_allowed_files(
    tmp_path,
) -> None:
    archive_root = tmp_path / "archive"
    export_root = tmp_path / "export"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    export_root.mkdir()
    transcript_text = "Synthetic transcript token secret auth profile payload."
    event_text = "Synthetic event private payload."
    alert_text = "Synthetic alert private payload."
    reviewer_text = "Synthetic reviewer private payload."
    (session_dir / "transcript.jsonl").write_text(
        transcript_text,
        encoding="utf-8",
    )
    (session_dir / "events.jsonl").write_text(event_text, encoding="utf-8")
    (session_dir / "alerts.log").write_text(alert_text, encoding="utf-8")
    (session_dir / "reviewer.md").write_text(reviewer_text, encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-local",
            "session-001",
            "--archive-root",
            str(archive_root),
            "--export-root",
            str(export_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    payload = json.loads(result.stdout)
    assert payload["session_id"] == "session-001"
    assert payload["session_dir"] == "session-001"
    assert payload["export_dir"] == "session-001"
    assert payload["artifact_count"] == 4
    assert payload["total_exported_size_bytes"] == sum(
        len(text.encode("utf-8"))
        for text in (transcript_text, event_text, alert_text, reviewer_text)
    )
    assert [artifact["filename"] for artifact in payload["artifacts"]] == [
        "transcript.jsonl",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
    ]
    assert all(artifact["status"] == "exported" for artifact in payload["artifacts"])
    exported_session_dir = export_root / "session-001"
    for filename in (
        "transcript.jsonl",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
    ):
        assert (exported_session_dir / filename).is_file()

    combined_output = f"{result.stdout}\n{result.stderr}".lower()
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "synthetic transcript",
        "synthetic event",
        "synthetic alert",
        "synthetic reviewer",
        "token",
        "secret",
        "auth",
        "profile",
        "payload",
        "scheduler",
        "traceback",
        "gate d",
    ):
        assert forbidden_fragment not in combined_output


def test_archive_export_local_command_sanitizes_failures(tmp_path) -> None:
    archive_root = tmp_path / "archive"
    unsafe_export_root = tmp_path / "export-token-secret-auth-profile"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    unsafe_export_root.write_text(
        "Synthetic private export placeholder.",
        encoding="utf-8",
    )
    (session_dir / "events.jsonl").write_text("{}", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-local",
            "session-001",
            "--archive-root",
            str(archive_root),
            "--export-root",
            str(unsafe_export_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "archive export could not be executed\n"
    for forbidden_fragment in (
        str(tmp_path),
        "export-token",
        "secret",
        "auth",
        "profile",
        "Synthetic private",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_local_command_delegates_to_existing_helpers(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    module_name = "async_scholar.archive_export"
    fake_module = types.ModuleType(module_name)
    fake_result = object()

    def fake_execute(archive_root: Path, export_root: Path, session_id: str) -> object:
        received["archive_root"] = archive_root
        received["export_root"] = export_root
        received["session_id"] = session_id
        return fake_result

    def fake_summary(export_result: object) -> dict[str, object]:
        received["export_result"] = export_result
        return {"artifact_count": 0, "session_id": "session-001"}

    fake_module.execute_archive_export_to_local_root = fake_execute
    fake_module.archive_export_execution_result_safe_summary = fake_summary
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(
        [
            "archive-export-local",
            "session-001",
            "--archive-root",
            "archive-root",
            "--export-root",
            "export-root",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "artifact_count": 0,
        "session_id": "session-001",
    }
    assert captured.err == ""
    assert received == {
        "archive_root": Path("archive-root"),
        "export_root": Path("export-root"),
        "session_id": "session-001",
        "export_result": fake_result,
    }


def test_archive_export_verify_local_help_does_not_build_verification(
    monkeypatch,
) -> None:
    module_name = "async_scholar.archive_export"
    monkeypatch.delitem(sys.modules, module_name, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-verify-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar archive-export-verify-local" in result.stdout
    assert "--archive-root" in result.stdout
    assert "--export-root" in result.stdout
    assert module_name not in sys.modules


def test_archive_export_verify_local_requires_explicit_roots() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-verify-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "archive export verification could not be built\n"


def test_archive_export_verify_local_sanitizes_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-verify-local",
            "session-001",
            "C:\\Users\\student\\token-secret-auth-profile",
            "--archive-root",
            ".",
            "--export-root",
            ".",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "archive export verification could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "unrecognized arguments",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_verify_local_sanitizes_misordered_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--archive-root",
            "C:\\Users\\student\\token-secret-auth-profile",
            "archive-export-verify-local",
            "session-001",
            "--export-root",
            ".",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "archive export verification could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_verify_local_command_prints_safe_json(tmp_path) -> None:
    archive_root = tmp_path / "archive-token-secret-auth-profile"
    export_root = tmp_path / "export-token-secret-auth-profile"
    session_dir = archive_root / "session-001"
    exported_session_dir = export_root / "session-001"
    session_dir.mkdir(parents=True)
    exported_session_dir.mkdir(parents=True)
    event_text = "Synthetic event token secret auth profile payload."
    reviewer_text = "Synthetic reviewer private payload."
    (session_dir / "events.jsonl").write_text(event_text, encoding="utf-8")
    (session_dir / "reviewer.md").write_text(reviewer_text, encoding="utf-8")
    (exported_session_dir / "events.jsonl").write_text(event_text, encoding="utf-8")
    (exported_session_dir / "reviewer.md").write_text(
        reviewer_text,
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-verify-local",
            "session-001",
            "--archive-root",
            str(archive_root),
            "--export-root",
            str(export_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    payload = json.loads(result.stdout)
    assert payload["session_id"] == "session-001"
    assert payload["session_dir"] == "session-001"
    assert payload["export_dir"] == "session-001"
    assert payload["expected_count"] == 2
    assert payload["verified_count"] == 2
    assert payload["all_verified"] is True
    assert [artifact["filename"] for artifact in payload["artifacts"]] == [
        "transcript.jsonl",
        "transcript.md",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
        "runtime.jsonl",
        "benchmark-report.json",
    ]
    assert payload["artifacts"][2]["status"] == "verified"
    assert payload["artifacts"][4]["status"] == "verified"

    combined_output = f"{result.stdout}\n{result.stderr}".lower()
    for forbidden_fragment in (
        str(tmp_path).lower(),
        "archive-token",
        "export-token",
        "synthetic event",
        "synthetic reviewer",
        "token",
        "secret",
        "auth",
        "profile",
        "payload",
        "traceback",
        "gate d",
    ):
        assert forbidden_fragment not in combined_output


def test_archive_export_verify_local_command_sanitizes_failures(tmp_path) -> None:
    archive_root = tmp_path / "archive-token-secret-auth-profile"
    export_root = tmp_path / "export-token-secret-auth-profile"
    archive_root.write_text("Synthetic private archive placeholder.", encoding="utf-8")
    export_root.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-export-verify-local",
            "session-001",
            "--archive-root",
            str(archive_root),
            "--export-root",
            str(export_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "archive export verification could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "archive-token",
        "export-token",
        "secret",
        "auth",
        "profile",
        "Synthetic private",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_export_verify_local_command_delegates_to_existing_helpers(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    module_name = "async_scholar.archive_export"
    fake_module = types.ModuleType(module_name)
    fake_verification = object()

    def fake_build(archive_root: Path, export_root: Path, session_id: str) -> object:
        received["archive_root"] = archive_root
        received["export_root"] = export_root
        received["session_id"] = session_id
        return fake_verification

    def fake_summary(verification: object) -> dict[str, object]:
        received["verification"] = verification
        return {"all_verified": True, "session_id": "session-001"}

    fake_module.build_archive_export_verification_summary_from_roots = fake_build
    fake_module.archive_export_verification_summary_safe_summary = fake_summary
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(
        [
            "archive-export-verify-local",
            "session-001",
            "--archive-root",
            "archive-root",
            "--export-root",
            "export-root",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "all_verified": True,
        "session_id": "session-001",
    }
    assert captured.err == ""
    assert received == {
        "archive_root": Path("archive-root"),
        "export_root": Path("export-root"),
        "session_id": "session-001",
        "verification": fake_verification,
    }


def test_archive_delete_dry_run_local_help_does_not_build_dry_run(
    monkeypatch,
) -> None:
    module_name = "async_scholar.archive_delete_dry_run_result"
    monkeypatch.delitem(sys.modules, module_name, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-delete-dry-run-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar archive-delete-dry-run-local" in result.stdout
    assert "--archive-root" in result.stdout
    assert "dry run" in result.stdout
    assert module_name not in sys.modules


def test_archive_delete_dry_run_local_requires_explicit_archive_root() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-delete-dry-run-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "archive delete dry run could not be built\n"


def test_archive_delete_dry_run_local_sanitizes_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-delete-dry-run-local",
            "session-001",
            "C:\\Users\\student\\token-secret-auth-profile",
            "--archive-root",
            ".",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "archive delete dry run could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "unrecognized arguments",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_delete_dry_run_local_sanitizes_misordered_archive_root_failure() -> (
    None
):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--archive-root",
            "C:\\Users\\student\\token-secret-auth-profile",
            "archive-delete-dry-run-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "archive delete dry run could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_delete_dry_run_local_command_prints_safe_json(tmp_path) -> None:
    archive_root = tmp_path / "archive-token-secret-auth-profile"
    session_dir = archive_root / "session-001"
    session_dir.mkdir(parents=True)
    event_text = "Synthetic event token secret auth profile payload."
    reviewer_text = "Synthetic reviewer private payload."
    (session_dir / "events.jsonl").write_text(event_text, encoding="utf-8")
    (session_dir / "reviewer.md").write_text(reviewer_text, encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-delete-dry-run-local",
            "session-001",
            "--archive-root",
            str(archive_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    payload = json.loads(result.stdout)
    assert payload["session_id"] == "session-001"
    assert payload["session_dir"] == "session-001"
    assert payload["result_kind"] == "archive_delete_dry_run_result"
    assert payload["status"] == "dry_run_completed"
    assert payload["dry_run_only"] is True
    assert payload["deletion_performed"] is False
    assert payload["artifact_count"] == 7
    assert payload["existing_artifact_count"] == 2
    assert payload["total_existing_size_bytes"] == sum(
        len(text.encode("utf-8")) for text in (event_text, reviewer_text)
    )
    assert [artifact["filename"] for artifact in payload["artifacts"]] == [
        "transcript.jsonl",
        "transcript.md",
        "events.jsonl",
        "alerts.log",
        "reviewer.md",
        "runtime.jsonl",
        "benchmark-report.json",
    ]
    assert payload["artifacts"][2]["exists"] is True
    assert payload["artifacts"][2]["size_bytes"] == len(event_text.encode("utf-8"))
    assert payload["artifacts"][4]["exists"] is True
    assert payload["artifacts"][4]["size_bytes"] == len(reviewer_text.encode("utf-8"))
    assert all(artifact["status"] == "not_deleted" for artifact in payload["artifacts"])

    combined_output = f"{result.stdout}\n{result.stderr}".lower()
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
        "traceback",
        "gate d",
    ):
        assert forbidden_fragment not in combined_output


def test_archive_delete_dry_run_local_command_sanitizes_failures(tmp_path) -> None:
    unsafe_root = tmp_path / "archive-token-secret-auth-profile"
    unsafe_root.write_text("Synthetic private archive placeholder.", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "archive-delete-dry-run-local",
            "session-001",
            "--archive-root",
            str(unsafe_root),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "archive delete dry run could not be built\n"
    for forbidden_fragment in (
        str(tmp_path),
        "archive-token",
        "secret",
        "auth",
        "profile",
        "Synthetic private",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_archive_delete_dry_run_local_command_delegates_to_existing_helpers(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    module_name = "async_scholar.archive_delete_dry_run_result"
    fake_module = types.ModuleType(module_name)
    fake_dry_run = object()

    def fake_build(archive_root: Path, session_id: str) -> object:
        received["archive_root"] = archive_root
        received["session_id"] = session_id
        return fake_dry_run

    def fake_export(dry_run: object) -> dict[str, object]:
        received["dry_run"] = dry_run
        return {
            "deletion_performed": False,
            "dry_run_only": True,
            "session_id": "session-001",
        }

    fake_module.ARCHIVE_DELETE_DRY_RUN_LOCAL_ERROR = (
        "archive delete dry run could not be built"
    )
    fake_module.build_archive_delete_dry_run_local_result = fake_build
    fake_module.export_archive_delete_dry_run_local_result = fake_export
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(
        [
            "archive-delete-dry-run-local",
            "session-001",
            "--archive-root",
            "archive-root",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {
        "deletion_performed": False,
        "dry_run_only": True,
        "session_id": "session-001",
    }
    assert captured.err == ""
    assert received == {
        "archive_root": Path("archive-root"),
        "session_id": "session-001",
        "dry_run": fake_dry_run,
    }


def test_scheduled_start_preview_local_help_stays_lazy(
    monkeypatch,
) -> None:
    schedule_config_module = "async_scholar.schedule_config"
    scheduled_start_module = "async_scholar.scheduled_start"
    monkeypatch.delitem(sys.modules, schedule_config_module, raising=False)
    monkeypatch.delitem(sys.modules, scheduled_start_module, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-local",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar scheduled-start-preview-local" in result.stdout
    assert "--course-id" in result.stdout
    assert "--clock-local-time" in result.stdout
    assert "non-executing" in result.stdout
    assert schedule_config_module not in sys.modules
    assert scheduled_start_module not in sys.modules


def test_scheduled_start_preview_local_requires_explicit_metadata() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == "scheduled start preview could not be built\n"


def test_scheduled_start_preview_local_sanitizes_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-local",
            "session-001",
            "C:\\Users\\student\\token-secret-auth-profile",
            "--course-id",
            "cs101",
            "--day-of-week",
            "monday",
            "--local-start-time",
            "09:00",
            "--duration-minutes",
            "75",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "scheduled start preview could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "unrecognized arguments",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_preview_local_sanitizes_misordered_parse_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--course-id",
            "C:\\Users\\student\\token-secret-auth-profile",
            "scheduled-start-preview-local",
            "session-001",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "scheduled start preview could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "invalid choice",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_preview_local_command_prints_due_safe_json() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-local",
            "session-001",
            "--course-id",
            "cs101",
            "--day-of-week",
            "monday",
            "--local-start-time",
            "09:00",
            "--duration-minutes",
            "75",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    payload = json.loads(result.stdout)
    assert payload == {
        "clock_day_of_week": "monday",
        "clock_local_time": "09:00",
        "course_id": "cs101",
        "due": True,
        "enabled": True,
        "minutes_until_start": 0,
        "next_day_of_week": "monday",
        "next_local_start_time": "09:00",
        "result_kind": "scheduled_start_manual_result",
        "scheduled_day_of_week": "monday",
        "scheduled_local_start_time": "09:00",
        "session_id": "session-001",
        "source_kind": "file",
        "status": "due",
    }
    _assert_scheduled_start_preview_output_is_safe(result.stdout, result.stderr)


def test_scheduled_start_preview_local_command_prints_waiting_safe_json() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-local",
            "session-001",
            "--course-id",
            "cs101",
            "--day-of-week",
            "monday",
            "--local-start-time",
            "09:00",
            "--duration-minutes",
            "75",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "08:30",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["status"] == "waiting"
    assert payload["due"] is False
    assert payload["enabled"] is True
    assert payload["minutes_until_start"] == 30
    assert payload["next_day_of_week"] == "monday"
    assert payload["next_local_start_time"] == "09:00"
    _assert_scheduled_start_preview_output_is_safe(result.stdout, result.stderr)


def test_scheduled_start_preview_local_command_prints_disabled_safe_json() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-local",
            "session-001",
            "--course-id",
            "cs101",
            "--day-of-week",
            "monday",
            "--local-start-time",
            "09:00",
            "--duration-minutes",
            "75",
            "--source-kind",
            "mic",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
            "--disabled",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["status"] == "disabled"
    assert payload["source_kind"] == "mic"
    assert payload["enabled"] is False
    assert payload["due"] is False
    assert payload["minutes_until_start"] is None
    assert payload["next_day_of_week"] is None
    assert payload["next_local_start_time"] is None
    _assert_scheduled_start_preview_output_is_safe(result.stdout, result.stderr)


def test_scheduled_start_preview_local_command_sanitizes_build_failures() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "scheduled-start-preview-local",
            "C:\\Users\\student\\token-secret-auth-profile",
            "--course-id",
            "cs101",
            "--day-of-week",
            "monday",
            "--local-start-time",
            "09:00",
            "--duration-minutes",
            "75",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "scheduled start preview could not be built\n"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "ValidationError",
        "Traceback",
    ):
        assert forbidden_fragment not in result.stderr


def test_scheduled_start_preview_local_command_delegates_to_existing_helpers(
    capsys,
    monkeypatch,
) -> None:
    received: dict[str, object] = {}
    schedule_config_module = "async_scholar.schedule_config"
    scheduled_start_module = "async_scholar.scheduled_start"
    fake_schedule_config_module = types.ModuleType(schedule_config_module)
    fake_scheduled_start_module = types.ModuleType(scheduled_start_module)
    fake_config = object()
    fake_plan = object()
    fake_clock = object()
    fake_preview = object()

    class FakeScheduleConfig:
        def __new__(cls, **kwargs: object) -> object:
            received["schedule_config_kwargs"] = kwargs
            return fake_config

    def fake_build_plan(
        schedule_config: object,
        selected_class_time_index: int,
        source_kind: str,
        *,
        enabled: bool,
    ) -> object:
        received["plan_config"] = schedule_config
        received["selected_class_time_index"] = selected_class_time_index
        received["source_kind"] = source_kind
        received["enabled"] = enabled
        return fake_plan

    class FakeClock:
        def __new__(cls, **kwargs: object) -> object:
            received["clock_kwargs"] = kwargs
            return fake_clock

    def fake_build_manual_result(
        plan: object,
        clock: object,
        session_id: str,
    ) -> object:
        received["manual_plan"] = plan
        received["manual_clock"] = clock
        received["session_id"] = session_id
        return fake_preview

    def fake_summary(preview: object) -> dict[str, object]:
        received["preview"] = preview
        return {"session_id": "session-001", "status": "due"}

    fake_schedule_config_module.ScheduleConfig = FakeScheduleConfig
    fake_scheduled_start_module.ScheduledStartClock = FakeClock
    fake_scheduled_start_module.build_scheduled_start_plan = fake_build_plan
    fake_scheduled_start_module.build_scheduled_start_manual_result = (
        fake_build_manual_result
    )
    fake_scheduled_start_module.scheduled_start_manual_result_safe_summary = (
        fake_summary
    )
    monkeypatch.setitem(
        sys.modules,
        schedule_config_module,
        fake_schedule_config_module,
    )
    monkeypatch.setitem(
        sys.modules,
        scheduled_start_module,
        fake_scheduled_start_module,
    )

    exit_code = cli.main(
        [
            "scheduled-start-preview-local",
            "session-001",
            "--course-id",
            "cs101",
            "--day-of-week",
            "monday",
            "--local-start-time",
            "09:00",
            "--duration-minutes",
            "75",
            "--source-kind",
            "file",
            "--clock-day-of-week",
            "monday",
            "--clock-local-time",
            "09:00",
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out) == {"session_id": "session-001", "status": "due"}
    assert captured.err == ""
    assert received == {
        "schedule_config_kwargs": {
            "course_id": "cs101",
            "class_times": [
                {
                    "day_of_week": "monday",
                    "local_start_time": "09:00",
                    "duration_minutes": 75,
                }
            ],
        },
        "plan_config": fake_config,
        "selected_class_time_index": 0,
        "source_kind": "file",
        "enabled": True,
        "clock_kwargs": {"day_of_week": "monday", "local_time": "09:00"},
        "manual_plan": fake_plan,
        "manual_clock": fake_clock,
        "session_id": "session-001",
        "preview": fake_preview,
    }


def _assert_scheduled_start_preview_output_is_safe(
    stdout: str,
    stderr: str,
) -> None:
    combined_output = f"{stdout}\n{stderr}".lower()
    for forbidden_fragment in (
        "meeting",
        "timezone",
        "c:\\",
        "\\\\server",
        "/users",
        "token",
        "secret",
        "auth",
        "cookie",
        "profile",
        "transcript",
        "audio",
        "traceback",
        "gate d",
        "product promise",
    ):
        assert forbidden_fragment not in combined_output


def test_archive_export_preflight_handler_does_not_execute_export() -> None:
    source = inspect.getsource(cli._run_archive_export_preflight_command)

    assert "execute_archive_export_to_local_root" not in source
    assert "archive_export_execution_result_safe_summary" not in source


def test_archive_export_verify_local_handler_does_not_execute_export() -> None:
    source = inspect.getsource(cli._run_archive_export_verify_local_command)

    assert "execute_archive_export_to_local_root" not in source
    assert "archive_export_execution_result_safe_summary" not in source
    assert "archive_export_verification_summary_safe_summary" in source


def test_archive_delete_dry_run_local_handler_does_not_execute_delete_or_export() -> (
    None
):
    source = inspect.getsource(cli._run_archive_delete_dry_run_local_command)

    assert "build_archive_delete_dry_run_local_result" in source
    assert "export_archive_delete_dry_run_local_result" in source
    for forbidden_fragment in (
        "execute_archive_export_to_local_root",
        "archive_export_execution_result_safe_summary",
        "unlink",
        "remove",
        "rmdir",
        "rmtree",
        "shutil",
        "requests",
        "httpx",
        "playwright",
        "sounddevice",
        "telegram",
        "desktop_notifier",
        "Timer(",
        "threading",
        "asyncio",
    ):
        assert forbidden_fragment not in source


def test_scheduled_start_preview_local_handler_does_not_execute_scheduler() -> None:
    source = inspect.getsource(cli._run_scheduled_start_preview_local_command)

    assert "ScheduleConfig" in source
    assert "build_scheduled_start_plan" in source
    assert "ScheduledStartClock" in source
    assert "build_scheduled_start_manual_result" in source
    assert "scheduled_start_manual_result_safe_summary" in source
    for forbidden_fragment in (
        "datetime",
        "now(",
        "utcnow",
        "sleep",
        "Timer(",
        "threading",
        "subprocess",
        "webbrowser",
        "requests",
        "httpx",
        "playwright",
        "sounddevice",
        "telegram",
        "desktop_notifier",
        "execute_archive",
        "archive_export",
        ".open(",
        ".read_text(",
        ".write_text(",
        ".mkdir(",
        ".unlink(",
        ".remove(",
        ".rmdir(",
    ):
        assert forbidden_fragment not in source


def test_archive_export_cli_source_does_not_call_forbidden_surfaces() -> None:
    source = Path("src/async_scholar/__main__.py").read_text(encoding="utf-8")

    for forbidden_fragment in (
        "archive_delete_confirmation",
        "execute_archive_delete",
        ".unlink(",
        ".remove(",
        ".rmdir(",
        "rmtree",
        "shutil",
        "ZipFile",
        "tarfile",
        "requests",
        "httpx",
        "playwright",
        "sounddevice",
        "faster_whisper",
        "telegram",
        "desktop_notifier",
        "Timer(",
        "threading",
        "asyncio",
        "google",
    ):
        assert forbidden_fragment not in source


def test_mic_recording_diagnostic_command_delegates_to_existing_command(
    monkeypatch,
) -> None:
    received: dict[str, list[str]] = {}
    module_name = "async_scholar.audio.mic_recording_diagnostic"
    fake_module = types.ModuleType(module_name)

    def fake_main(argv: list[str]) -> int:
        received["argv"] = argv
        return 17

    fake_module.main = fake_main
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(
        [
            "mic-recording-diagnostic",
            "--seconds",
            "1",
            "--max-chunks",
            "1",
        ],
    )

    assert exit_code == 17
    assert received["argv"] == ["--seconds", "1", "--max-chunks", "1"]


def test_fixture_demo_command_writes_artifacts(tmp_path) -> None:
    fixture_path = Path("tests/fixtures/transcripts/attendance_roll_call.jsonl")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "fixture-demo",
            str(fixture_path),
            "--output-root",
            str(tmp_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    output_dir = tmp_path / "fixture_attendance_roll_call"
    assert result.returncode == 0
    assert "Fixture demo complete." in result.stdout
    assert "Events detected: 2" in result.stdout
    assert (output_dir / "events.jsonl").is_file()
    assert (output_dir / "alerts.log").is_file()
    assert (output_dir / "reviewer.md").is_file()
