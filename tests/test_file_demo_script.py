from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_file_demo.ps1"


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
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )


def combined_output(result: subprocess.CompletedProcess[str]) -> str:
    return f"{result.stdout}\n{result.stderr}"


def test_help_describes_explicit_inputs_and_ignored_artifacts() -> None:
    result = run_script("-Help")

    assert result.returncode == 0
    output = combined_output(result)
    assert "-AudioPath" in output
    assert "-ModelSizeOrPath" in output
    assert "-OutputRoot" in output
    assert "No sample audio is bundled or selected" in output
    assert "No default model is chosen" in output
    assert "transcript.jsonl" in output
    assert "transcript.md" in output
    assert "benchmark-report.json" in output
    assert "ignored local outputs" in output
    assert "does not print transcript text" in output


def test_missing_parameters_fail_without_running_benchmark() -> None:
    result = run_script()

    assert result.returncode != 0
    output = combined_output(result)
    assert "Missing required parameter(s)" in output
    assert "-AudioPath" in output
    assert "-ModelSizeOrPath" in output
    assert "-OutputRoot" in output
    assert "Running AsyncScholar file STT smoke" not in output
    assert "async_scholar.stt.benchmark" not in output


def test_missing_audio_file_fails_before_model_work(tmp_path: Path) -> None:
    result = run_script(
        "-AudioPath",
        str(tmp_path / "missing.wav"),
        "-ModelSizeOrPath",
        "explicit-test-model",
        "-OutputRoot",
        str(tmp_path / "output"),
    )

    assert result.returncode != 0
    output = combined_output(result)
    assert "AudioPath does not exist or is not a file" in output
    assert "Running AsyncScholar file STT smoke" not in output
    assert "async_scholar.stt.benchmark" not in output
    assert not (tmp_path / "output").exists()
