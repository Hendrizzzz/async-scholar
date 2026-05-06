from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_vad_plan_demo.ps1"


def run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(SCRIPT),
            *args,
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_vad_plan_demo_script_help_text_is_explicit_and_narrow() -> None:
    result = run_script("-Help")
    output = result.stdout + result.stderr

    assert result.returncode == 0
    assert "-AudioPath" in output
    assert "-OutputRoot" in output
    assert "vad-plan-report.json" in output
    assert "model" not in output.lower()
    assert "stt" not in output.lower()


def test_vad_plan_demo_script_requires_audio_path() -> None:
    result = run_script()
    output = result.stdout + result.stderr

    assert result.returncode != 0
    assert "Missing required -AudioPath" in output
    assert "model" not in output.lower()
    assert "stt" not in output.lower()


def test_vad_plan_demo_script_requires_output_root(tmp_path: Path) -> None:
    audio_path = tmp_path / "input.wav"
    audio_path.write_bytes(b"fake")

    result = run_script("-AudioPath", str(audio_path))
    output = result.stdout + result.stderr

    assert result.returncode != 0
    assert "Missing required -OutputRoot" in output
    assert "model" not in output.lower()
    assert "stt" not in output.lower()


def test_vad_plan_demo_script_validates_missing_audio_path(tmp_path: Path) -> None:
    missing_audio_path = tmp_path / "missing.wav"

    result = run_script(
        "-AudioPath",
        str(missing_audio_path),
        "-OutputRoot",
        str(tmp_path / "out"),
    )
    output = result.stdout + result.stderr

    assert result.returncode != 0
    assert "AudioPath does not exist or is not a file" in output
    assert "model" not in output.lower()
    assert "stt" not in output.lower()
