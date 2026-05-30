from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_gate_d_human_walkthrough.ps1"
RUNBOOK = ROOT / "docs" / "public" / "gate-d-human-demo-inspection-runbook.md"
README = ROOT / "README.md"


def run_script(
    *args: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
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
        env=env,
        text=True,
    )


def combined_output(result: subprocess.CompletedProcess[str]) -> str:
    return f"{result.stdout}\n{result.stderr}"


def test_help_describes_one_command_human_walkthrough() -> None:
    result = run_script("-Help")
    output = combined_output(result)

    assert result.returncode == 0
    assert "AsyncScholar Gate D human walkthrough" in output
    assert "-WorkRoot <path>" in output
    assert "safe default temp work root" in output
    assert "product_judgment_evidence" in output
    assert "does not claim Gate D" in output
    assert "does not claim Product Promise Alpha" in output


def test_script_source_stays_in_demo_clarity_boundary() -> None:
    source = SCRIPT.read_text(encoding="utf-8").lower()

    required_fragments = (
        "gate-d-local-evidence-bundle",
        "gate-d-handoff-packet-local",
        "run_scheduler_archive_workflow_smoke.ps1",
        "manual product judgment is required",
        "human pass/fail/defer judgment",
    )
    for fragment in required_fragments:
        assert fragment in source

    forbidden_source_fragments = (
        "meet.google.com",
        "playwright",
        "selenium",
        "mic-recording-diagnostic",
        "archive-delete",
        "archive-export-local",
        "start-sleep",
        "start-job",
        "register-scheduledjob",
        "git push",
        "product promise alpha passed",
        "gate d passed",
        "product_judgment_evidence satisfied",
    )
    for fragment in forbidden_source_fragments:
        assert fragment not in source


def test_successful_walkthrough_prints_human_readout_with_default_work_root(
    tmp_path: Path,
) -> None:
    env = _fake_success_env(tmp_path)
    env["TEMP"] = str(tmp_path / "temp")

    result = run_script(env=env)
    output = combined_output(result)

    assert result.returncode == 0, output
    assert "AsyncScholar Gate D Product Promise Alpha walkthrough" in output
    assert "Step 1 - CLI availability" in output
    assert "What this proves: the local AsyncScholar CLI can be reached." in output
    assert "Expected signal: product_judgment_evidence is blocking." in output
    assert "Result: Gate D remains blocked on product_judgment_evidence." in output
    assert "Result: manual product judgment is required and not recorded." in output
    assert "Step 4 - Local scheduler/archive workflow smoke" in output
    assert "Temporary artifact root:" in output
    assert str(tmp_path / "temp" / "async-scholar-gate-d-human-walkthrough") in output
    assert "Next human step: inspect this readout and choose pass/fail/defer." in output
    assert "Gate D passed" not in output
    assert "Product Promise Alpha passed" not in output
    assert "product_judgment_evidence satisfied" not in output


def test_successful_walkthrough_uses_override_work_root(tmp_path: Path) -> None:
    env = _fake_success_env(tmp_path)
    work_root = tmp_path / "custom-walkthrough-root"

    result = run_script("-WorkRoot", str(work_root), env=env)
    output = combined_output(result)

    assert result.returncode == 0, output
    assert f"Walkthrough work root: {work_root}" in output
    assert (
        f"Scheduler/archive smoke work root: {work_root / 'scheduler-archive-smoke'}"
        in output
    )


def test_walkthrough_fails_when_gate_d_blocker_is_missing(tmp_path: Path) -> None:
    env = _fake_success_env(tmp_path, bundle_blocking=False)

    result = run_script("-WorkRoot", str(tmp_path / "work"), env=env)
    output = combined_output(result)

    assert result.returncode != 0
    assert (
        "Expected Gate D bundle blocker product_judgment_evidence was not present."
        in output
    )
    assert "Step 4 - Local scheduler/archive workflow smoke" not in output


def test_runbook_and_readme_point_to_one_command_walkthrough() -> None:
    runbook = RUNBOOK.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")

    assert "scripts\\run_gate_d_human_walkthrough.ps1" in runbook
    assert "Sample expected walkthrough readout" in runbook
    assert "Step 1 - CLI availability" in runbook
    assert "Result: Gate D remains blocked on product_judgment_evidence." in runbook
    assert (
        "Next human step: inspect this readout and choose pass/fail/defer." in runbook
    )
    assert "scripts\\run_gate_d_human_walkthrough.ps1" in readme
    assert "one-command human walkthrough" in readme.lower()
    assert "Gate D passed" not in readme
    assert "Product Promise Alpha passed" not in readme


def _fake_success_env(
    tmp_path: Path,
    *,
    bundle_blocking: bool = True,
) -> dict[str, str]:
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_uv = fake_bin / "uv.cmd"
    bundle_json = (
        '{"blocking_evidence":["product_judgment_evidence"],'
        '"product_judgment_evidence_status":"blocking",'
        '"gate_d_pass_claimed":false,'
        '"product_promise_alpha_pass_claimed":false}'
        if bundle_blocking
        else '{"blocking_evidence":[],"product_judgment_evidence_status":"missing"}'
    )
    handoff_json = (
        '{"manual_product_judgment_required":true,'
        '"manual_product_judgment_recorded":false,'
        '"review_can_be_completed_by_ai":false,'
        '"product_judgment_evidence_status":"blocking"}'
    )
    fake_uv.write_text(
        "\r\n".join(
            (
                "@echo off",
                'echo %* | findstr /C:"gate-d-local-evidence-bundle" >nul && echo '
                + bundle_json
                + " && exit /b 0",
                'echo %* | findstr /C:"gate-d-handoff-packet-local" >nul && echo '
                + handoff_json
                + " && exit /b 0",
                "echo fake async_scholar command ok",
                "exit /b 0",
            )
        ),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    return env
