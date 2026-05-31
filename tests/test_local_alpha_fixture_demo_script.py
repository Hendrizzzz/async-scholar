from __future__ import annotations

import json
import os
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_local_alpha_fixture_demo.ps1"
SCRIPT_ERROR = "local alpha fixture demo script could not be built"


def test_script_help_does_not_invoke_uv(tmp_path: Path) -> None:
    marker = tmp_path / "uv-called.txt"
    result = _run_script("-Help", env=_fake_uv_env(tmp_path, marker))

    assert result.returncode == 0
    assert result.stderr == ""
    assert "AsyncScholar local alpha fixture demo" in result.stdout
    assert "-OutputRoot" in result.stdout
    assert "-DashboardOutput" in result.stdout
    assert "-SummaryOutput" in result.stdout
    assert "product_judgment_evidence" in result.stdout
    assert "does not pass Gate D" in result.stdout
    assert not marker.exists()


def test_script_delegates_default_fixture_dashboard_and_gate_commands(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "uv-called.txt"
    result = _run_script(env=_fake_uv_env(tmp_path, marker))

    assert result.returncode == 0
    assert result.stderr == ""
    _assert_success_summary(result.stdout)
    marker_lines = _marker_lines(marker)
    assert len(marker_lines) == 4
    assert marker_lines[0].startswith(
        "run python -m async_scholar fixture-demo "
        "tests\\fixtures\\transcripts\\attendance_roll_call.jsonl --output-root "
    )
    assert "async-scholar-local-alpha-fixture-demo-" in marker_lines[0]
    assert marker_lines[1].startswith(
        "run python -m async_scholar local-alpha-dashboard-static-demo --output "
    )
    assert "async-scholar-local-alpha-fixture-demo-dashboard-" in marker_lines[1]
    assert marker_lines[1].endswith(".html")
    assert marker_lines[2] == (
        "run python -m async_scholar gate-d-local-evidence-bundle"
    )
    assert marker_lines[3] == (
        "run python -m async_scholar gate-d-handoff-packet-local"
    )


def test_script_delegates_explicit_local_outputs(tmp_path: Path) -> None:
    marker = tmp_path / "uv-called.txt"
    output_root = tmp_path / "fixture-output"
    dashboard_output = tmp_path / "dashboard.html"

    result = _run_script(
        "-OutputRoot",
        str(output_root),
        "-DashboardOutput",
        str(dashboard_output),
        env=_fake_uv_env(tmp_path, marker),
    )

    assert result.returncode == 0
    assert result.stderr == ""
    _assert_success_summary(result.stdout)
    marker_lines = _marker_lines(marker)
    assert marker_lines[0] == (
        "run python -m async_scholar fixture-demo "
        "tests\\fixtures\\transcripts\\attendance_roll_call.jsonl "
        f"--output-root {output_root}"
    )
    assert marker_lines[1] == (
        "run python -m async_scholar local-alpha-dashboard-static-demo "
        f"--output {dashboard_output}"
    )


def test_script_writes_sanitized_summary_output_after_success(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "uv-called.txt"
    output_root = tmp_path / "secret-token-auth-profile-output"
    dashboard_output = tmp_path / "secret-token-auth-profile-dashboard.html"
    summary_output = tmp_path / "secret-token-auth-profile-summary.json"

    result = _run_script(
        "-OutputRoot",
        str(output_root),
        "-DashboardOutput",
        str(dashboard_output),
        "-SummaryOutput",
        str(summary_output),
        env=_fake_uv_env(tmp_path, marker),
    )

    assert result.returncode == 0
    assert result.stderr == ""
    _assert_success_summary(result.stdout)
    assert str(summary_output) not in result.stdout
    assert summary_output.exists()
    assert json.loads(summary_output.read_text(encoding="utf-8")) == {
        "browser_server_launched": "no",
        "fixture_artifacts_generated": "yes",
        "gate_d_evidence_bundle_status": "blocked",
        "gate_d_handoff_packet_status": "manual_judgment_required",
        "live_delivery_performed": "no",
        "private_paths_included": "no",
        "product_judgment_evidence_status": "blocking",
        "product_judgment_recorded": "no",
        "product_promise_alpha_status": "not_passed",
        "raw_command_output_included": "no",
        "static_dashboard_generated": "yes",
        "summary_kind": "local_alpha_fixture_demo_sanitized_summary",
    }
    summary_text = summary_output.read_text(encoding="utf-8").casefold()
    for forbidden in (
        "raw fixture stdout",
        "attendance_roll_call",
        "secret",
        "token",
        "auth",
        "profile",
        "cookie",
        "meet.google",
        "traceback",
        "ready_for_gate_review",
        "missing_evidence",
        "blocking_evidence",
        "gate_d_pass_claimed",
        "product_promise_alpha_pass_claimed",
        str(output_root).casefold(),
        str(dashboard_output).casefold(),
        str(summary_output).casefold(),
        str(tmp_path).casefold(),
    ):
        assert forbidden not in summary_text


def test_script_rejects_existing_dashboard_output_without_invoking_uv(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "uv-called.txt"
    dashboard_output = tmp_path / "dashboard.html"
    dashboard_output.write_text("existing", encoding="utf-8")

    result = _run_script(
        "-DashboardOutput",
        str(dashboard_output),
        env=_fake_uv_env(tmp_path, marker),
    )

    _assert_fixed_failure(result)
    assert dashboard_output.read_text(encoding="utf-8") == "existing"
    assert not marker.exists()


def test_script_rejects_missing_dashboard_parent_without_invoking_uv(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "uv-called.txt"
    dashboard_output = tmp_path / "missing" / "dashboard.html"

    result = _run_script(
        "-DashboardOutput",
        str(dashboard_output),
        env=_fake_uv_env(tmp_path, marker),
    )

    _assert_fixed_failure(result)
    assert not dashboard_output.exists()
    assert not marker.exists()


def test_script_rejects_output_root_file_without_invoking_uv(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "uv-called.txt"
    output_root = tmp_path / "fixture-output"
    output_root.write_text("file", encoding="utf-8")

    result = _run_script(
        "-OutputRoot",
        str(output_root),
        env=_fake_uv_env(tmp_path, marker),
    )

    _assert_fixed_failure(result)
    assert output_root.read_text(encoding="utf-8") == "file"
    assert not marker.exists()


def test_script_rejects_unsafe_paths_and_arguments_without_invoking_uv(
    tmp_path: Path,
) -> None:
    cases = (
        ("-OutputRoot", ""),
        ("-OutputRoot", "https://example.invalid/output"),
        ("-OutputRoot", "file:fixture-output"),
        ("-OutputRoot", "mailto:student@example.invalid"),
        ("-OutputRoot", "\\\\server\\share\\fixture-output"),
        ("-OutputRoot", str(tmp_path / ".." / "fixture-output")),
        ("-DashboardOutput", "https://example.invalid/dashboard.html"),
        ("-DashboardOutput", "file:dashboard.html"),
        ("-DashboardOutput", "http:dashboard.html"),
        ("-DashboardOutput", "//server/share/dashboard.html"),
        ("-DashboardOutput", str(tmp_path / ".." / "dashboard.html")),
        ("-SummaryOutput", ""),
        ("-SummaryOutput", "https://example.invalid/summary.json"),
        ("-SummaryOutput", "file:summary.json"),
        ("-SummaryOutput", "http:summary.json"),
        ("-SummaryOutput", "mailto:student@example.invalid"),
        ("-SummaryOutput", "\\\\server\\share\\summary.json"),
        ("-SummaryOutput", "//server/share/summary.json"),
        ("-SummaryOutput", str(tmp_path / ".." / "summary.json")),
        ("-SummaryOutput", f"summary{chr(7)}.json"),
        ("-SummaryOutput", "-summary.json"),
        ("-Unknown", "C:\\Users\\student\\secret-output"),
        ("-OutputRoot",),
        ("-DashboardOutput",),
        ("-SummaryOutput",),
        ("-SummaryOutput", str(tmp_path / "summary-a.json"), "-SummaryOutput"),
    )

    for index, args in enumerate(cases):
        marker = tmp_path / f"uv-called-{index}.txt"
        result = _run_script(*args, env=_fake_uv_env(tmp_path, marker))

        _assert_fixed_failure(result)
        assert not marker.exists()


def test_script_rejects_invalid_summary_output_without_invoking_uv(
    tmp_path: Path,
) -> None:
    existing_file = tmp_path / "summary-file.json"
    existing_file.write_text("existing", encoding="utf-8")
    existing_directory = tmp_path / "summary-directory.json"
    existing_directory.mkdir()
    missing_parent = tmp_path / "missing" / "summary.json"

    cases = (
        existing_file,
        existing_directory,
        missing_parent,
    )

    for index, summary_output in enumerate(cases):
        marker = tmp_path / f"uv-called-summary-{index}.txt"
        result = _run_script(
            "-SummaryOutput",
            str(summary_output),
            env=_fake_uv_env(tmp_path, marker),
        )

        _assert_fixed_failure(result)
        assert not marker.exists()

    assert existing_file.read_text(encoding="utf-8") == "existing"
    assert existing_directory.is_dir()
    assert not missing_parent.exists()


def test_script_failure_does_not_create_summary_output(tmp_path: Path) -> None:
    summary_output = tmp_path / "summary.json"

    result = _run_script(
        "-SummaryOutput",
        str(summary_output),
        env=_fake_failing_uv_env(
            tmp_path,
            stdout_text='raw fixture stdout {"ready_for_gate_review":true}',
            stderr_text=(
                "Traceback C:\\Users\\student\\secret-cookie-profile "
                "https://meet.google.com/private"
            ),
        ),
    )

    _assert_fixed_failure(result)
    assert not summary_output.exists()
    combined = f"{result.stdout}\n{result.stderr}".casefold()
    for forbidden in (
        "raw fixture stdout",
        "ready_for_gate_review",
        "traceback",
        "secret",
        "cookie",
        "profile",
        "meet.google",
    ):
        assert forbidden not in combined


def test_script_sanitizes_failing_uv_output(tmp_path: Path) -> None:
    dashboard_output = tmp_path / "dashboard.html"
    result = _run_script(
        "-DashboardOutput",
        str(dashboard_output),
        env=_fake_failing_uv_env(
            tmp_path,
            stdout_text=(
                "private transcript tests\\fixtures\\transcripts\\"
                "attendance_roll_call.jsonl"
            ),
            stderr_text=(
                "Traceback C:\\Users\\student\\secret-cookie-profile "
                "https://meet.google.com/private"
            ),
        ),
    )

    _assert_fixed_failure(result)
    combined = f"{result.stdout}\n{result.stderr}".casefold()
    for forbidden in (
        "private transcript",
        "attendance_roll_call",
        "traceback",
        "secret",
        "cookie",
        "profile",
        "meet.google",
    ):
        assert forbidden not in combined


def test_script_success_output_does_not_echo_raw_uv_payloads_or_paths(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "uv-called.txt"
    output_root = tmp_path / "secret-token-auth-profile-output"
    dashboard_output = tmp_path / "secret-token-auth-profile-dashboard.html"

    result = _run_script(
        "-OutputRoot",
        str(output_root),
        "-DashboardOutput",
        str(dashboard_output),
        env=_fake_uv_env(tmp_path, marker),
    )

    assert result.returncode == 0
    _assert_success_summary(result.stdout)
    combined = f"{result.stdout}\n{result.stderr}".casefold()
    for forbidden in (
        "raw fixture stdout",
        "{",
        "}",
        "secret",
        "token",
        "auth",
        "profile",
        str(output_root).casefold(),
        str(dashboard_output).casefold(),
    ):
        assert forbidden not in combined


def test_script_source_preserves_fixture_only_scope() -> None:
    assert SCRIPT.exists()
    source = SCRIPT.read_text(encoding="utf-8").casefold()

    for forbidden in (
        "start-process",
        "invoke-webrequest",
        "invoke-restmethod",
        "remove-item",
        "start-sleep",
        "register-scheduledtask",
        "schtasks",
        "playwright",
        "selenium",
        "google meet",
        "local-alpha-dashboard-demo --host",
        "local-alpha-dashboard-demo --dry-run",
        "open-browser",
        "show=true",
        "fixture-demo --send",
    ):
        assert forbidden not in source

    assert "fixture-demo" in source
    assert "local-alpha-dashboard-static-demo" in source
    assert "gate-d-local-evidence-bundle" in source
    assert "gate-d-handoff-packet-local" in source
    assert "summaryoutput" in source
    assert "createnew" in source


def test_readme_documents_local_alpha_fixture_demo_boundaries() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "scripts\\run_local_alpha_fixture_demo.ps1" in readme
    assert "-SummaryOutput <local-summary-json>" in readme
    assert "sanitized JSON summary" in readme
    assert "fixture-demo" in readme
    assert "local-alpha-dashboard-static-demo" in readme
    assert "product_judgment_evidence" in readme
    assert "does not satisfy `product_judgment_evidence`" in readme
    assert "does not replace product judgment evidence" in readme
    assert "does not pass Gate D / Product Promise Alpha" in readme
    assert "local fixture-only" in readme


def _assert_success_summary(stdout: str) -> None:
    assert "fixture demo artifacts generated" in stdout
    assert "static dashboard generated" in stdout
    assert "Gate D evidence bundle remains blocked" in stdout
    assert "Gate D handoff packet still requires manual judgment" in stdout
    assert "product_judgment_evidence remains blocking" in stdout
    assert "Product Promise Alpha not passed" in stdout
    assert "Product Promise Alpha passed" not in stdout
    assert "Gate D passed" not in stdout


def _assert_fixed_failure(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == f"{SCRIPT_ERROR}\n"


def _marker_lines(marker: Path) -> list[str]:
    return [
        line.strip().replace("/", "\\")
        for line in marker.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _run_script(
    *args: str, env: dict[str, str] | None = None
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
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def _fake_uv_env(tmp_path: Path, marker: Path) -> dict[str, str]:
    fake_uv = tmp_path / "uv.cmd"
    fake_uv.write_text(
        textwrap.dedent(
            f"""\
            @echo off
            echo %* >> "{marker}"
            echo raw fixture stdout should be suppressed
            exit /b 0
            """
        ),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}{os.pathsep}{env['PATH']}"
    return env


def _fake_failing_uv_env(
    tmp_path: Path,
    *,
    stdout_text: str,
    stderr_text: str,
) -> dict[str, str]:
    fake_uv = tmp_path / "uv.cmd"
    fake_uv.write_text(
        textwrap.dedent(
            f"""\
            @echo off
            echo {stdout_text}
            echo {stderr_text} 1>&2
            exit /b 42
            """
        ),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}{os.pathsep}{env['PATH']}"
    return env
