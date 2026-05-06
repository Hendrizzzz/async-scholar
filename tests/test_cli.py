from __future__ import annotations

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
