from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_scheduler_archive_workflow_smoke.ps1"
SESSION_ID = "ticket-193-smoke-session"


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


def test_help_describes_required_work_root_and_local_artifacts() -> None:
    result = run_script("-Help")
    output = combined_output(result)

    assert result.returncode == 0
    assert "-WorkRoot <path>" in output
    assert "required" in output.lower()
    assert "schedule.sqlite" in output
    assert "stored-session-window-recovery-report.md" in output
    assert "explicit work root" in output.lower()
    assert "human-recorded narrow Gate D / Product Promise Alpha pass" in output
    assert "does not broaden that narrow pass" in output
    assert "does not approve Gate E" in output


def test_missing_work_root_fails_before_async_scholar_commands() -> None:
    result = run_script()
    output = combined_output(result)

    assert result.returncode != 0
    assert "Missing required -WorkRoot" in output
    assert "uv run" not in output
    assert "course-schedule-save-local" not in output
    assert "Running scheduler/archive workflow" not in output


def test_blank_work_root_fails_before_creating_artifacts(tmp_path: Path) -> None:
    result = run_script("-WorkRoot", "   ")
    output = combined_output(result)

    assert result.returncode != 0
    assert "Missing required -WorkRoot" in output
    assert "uv run" not in output
    assert "schedule.sqlite" not in output
    assert not any(tmp_path.iterdir())


def test_script_source_stays_in_allowed_local_metadata_scope() -> None:
    source = SCRIPT.read_text(encoding="utf-8").lower()

    forbidden_source_fragments = (
        "start-sleep",
        "start-job",
        "register-scheduledjob",
        "playwright",
        "selenium",
        "mic-recording-diagnostic",
        "archive-delete",
        "archive-export-local",
        "session-window-recovery-report-file-action-local",
        "product promise alpha passed",
        "gate d passed",
        "gate d remains blocked",
        "product_judgment_evidence satisfied",
        "ready for product",
    )
    for fragment in forbidden_source_fragments:
        assert fragment not in source


def test_first_failed_cli_command_stops_workflow(tmp_path: Path) -> None:
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_uv = fake_bin / "uv.cmd"
    fake_uv.write_text(
        "@echo off\r\necho fake uv called %*\r\nexit /b 23\r\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"

    result = run_script("-WorkRoot", str(tmp_path / "work"), env=env)
    output = combined_output(result)

    assert result.returncode == 23
    assert "course-schedule-save-local" in output
    assert "failed with exit code 23" in output
    assert "course-schedule-list-local" not in output
    assert "session-window-execute-from-store-local" not in output


def test_successful_run_writes_artifacts_only_under_temp_work_root(
    tmp_path: Path,
) -> None:
    work_root = tmp_path / "work"

    result = run_script("-WorkRoot", str(work_root))
    output = combined_output(result)

    assert result.returncode == 0, output
    schedule_db = work_root / "scheduler" / "schedule.sqlite"
    runtime_file = work_root / "archive" / SESSION_ID / "runtime.jsonl"
    report_file = (
        work_root
        / "recovery-reports"
        / SESSION_ID
        / "stored-session-window-recovery-report.md"
    )
    for artifact in (schedule_db, runtime_file, report_file):
        assert artifact.exists()
        assert artifact.is_file()
        assert artifact.is_relative_to(work_root)
        assert not artifact.is_relative_to(ROOT)
        assert str(artifact) in output

    assert "course-schedule-save-local" in output
    assert "gate-d-local-evidence-bundle" in output
    assert "gate-d-handoff-packet-local" in output
    assert "Historical Gate D handoff metadata reviewed" in output
    assert "Gate E remains blocked on human approval" in output
    assert "Gate D handoff remains blocked" not in output
    assert "Product Promise Alpha passed" not in output
    assert "Gate D passed" not in output
    assert "product_judgment_evidence satisfied" not in output
    assert not (ROOT / "schedule.sqlite").exists()
    assert not (ROOT / "stored-session-window-recovery-report.md").exists()
    assert not (
        ROOT / "data" / "async-scholar-scheduler-archive-workflow-smoke"
    ).exists()


def test_repeated_run_uses_fresh_recovery_report_path(tmp_path: Path) -> None:
    work_root = tmp_path / "work"

    first_result = run_script("-WorkRoot", str(work_root))
    second_result = run_script("-WorkRoot", str(work_root))
    second_output = combined_output(second_result)

    assert first_result.returncode == 0, combined_output(first_result)
    assert second_result.returncode == 0, second_output
    repeated_runtime_file = work_root / "archive" / f"{SESSION_ID}-2" / "runtime.jsonl"
    repeated_report_file = (
        work_root
        / "recovery-reports"
        / f"{SESSION_ID}-2"
        / "stored-session-window-recovery-report.md"
    )
    assert repeated_runtime_file.exists()
    assert repeated_report_file.exists()
    assert repeated_report_file.is_relative_to(work_root)
    assert str(repeated_report_file) in second_output
    assert "stored session window recovery report file could not be written" not in (
        second_output.lower()
    )
