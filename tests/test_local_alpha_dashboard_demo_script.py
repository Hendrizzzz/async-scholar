from __future__ import annotations

import json
import os
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_local_alpha_dashboard_demo.ps1"
SCRIPT_ERROR = "local alpha dashboard demo script could not be built"


def test_script_help_does_not_invoke_uv(tmp_path: Path) -> None:
    marker = tmp_path / "uv-called.txt"
    result = _run_script("-Help", env=_fake_uv_env(tmp_path, marker))

    assert result.returncode == 0
    assert result.stderr == ""
    assert "AsyncScholar local alpha dashboard demo" in result.stdout
    assert "-DryRun" in result.stdout
    assert "-HostName" in result.stdout
    assert "-Port" in result.stdout
    assert "product_judgment_evidence" in result.stdout
    assert not marker.exists()


def test_script_dry_run_delegates_to_existing_cli_without_server() -> None:
    result = _run_script("-DryRun")

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["url"] == "http://127.0.0.1:8086"
    assert payload["server_started"] is False
    assert payload["browser_opened"] is False
    assert payload["product_judgment_evidence_status"] == "blocking"
    assert payload["product_promise_alpha_pass_claimed"] is False


def test_script_live_mode_delegates_defaults_to_loopback(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "uv-called.txt"
    result = _run_script(env=_fake_uv_env(tmp_path, marker))

    assert result.returncode == 0
    assert result.stderr == ""
    assert marker.read_text(encoding="utf-8").strip() == (
        "run python -m async_scholar local-alpha-dashboard-demo "
        "--host 127.0.0.1 --port 8086"
    )


def test_script_dry_run_delegates_custom_loopback_host_and_port(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "uv-called.txt"
    result = _run_script(
        "-DryRun",
        "-HostName",
        "localhost",
        "-Port",
        "8090",
        env=_fake_uv_env(tmp_path, marker),
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert marker.read_text(encoding="utf-8").strip() == (
        "run python -m async_scholar local-alpha-dashboard-demo "
        "--host localhost --port 8090 --dry-run"
    )


def test_script_rejects_non_loopback_host_without_invoking_uv(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "uv-called.txt"
    result = _run_script(
        "-HostName",
        "0.0.0.0",
        env=_fake_uv_env(tmp_path, marker),
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == f"{SCRIPT_ERROR}\n"
    assert "0.0.0.0" not in result.stderr
    assert not marker.exists()


def test_script_rejects_invalid_port_without_invoking_uv(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "uv-called.txt"
    result = _run_script(
        "-Port",
        "65536",
        env=_fake_uv_env(tmp_path, marker),
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == f"{SCRIPT_ERROR}\n"
    assert not marker.exists()


def test_script_rejects_unknown_arguments_without_invoking_uv(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "uv-called.txt"
    result = _run_script(
        "-UnknownParam",
        "C:\\Users\\student\\secret-path",
        env=_fake_uv_env(tmp_path, marker),
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == f"{SCRIPT_ERROR}\n"
    assert "secret-path" not in result.stderr
    assert not marker.exists()


def test_script_sanitizes_uv_failure_output(tmp_path: Path) -> None:
    result = _run_script(
        "-DryRun",
        env=_fake_failing_uv_env(
            tmp_path,
            stdout_text="C:\\Users\\student\\private-output",
            stderr_text="Traceback C:\\Users\\student\\secret-token.txt",
        ),
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == f"{SCRIPT_ERROR}\n"
    assert "private-output" not in result.stdout
    assert "secret-token" not in result.stderr


def test_script_source_preserves_local_demo_scope() -> None:
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
        "cookie",
        ".env",
        "token",
    ):
        assert forbidden not in source

    assert "local-alpha-dashboard-demo" in source
    assert "127.0.0.1" in source
    assert "0.0.0.0" not in source


def test_readme_documents_one_command_script_boundaries() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "scripts\\run_local_alpha_dashboard_demo.ps1 -DryRun" in readme
    assert "scripts\\run_local_alpha_dashboard_demo.ps1" in readme
    assert "product_judgment_evidence" in readme
    assert "does not replace product judgment evidence" in readme
    assert "pass Gate D / Product Promise Alpha" in readme


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
            echo %* > "{marker}"
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
