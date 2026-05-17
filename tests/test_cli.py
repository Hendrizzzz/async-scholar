from __future__ import annotations

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
