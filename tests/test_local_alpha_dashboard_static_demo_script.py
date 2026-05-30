from __future__ import annotations

import os
import re
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_local_alpha_dashboard_static_demo.ps1"
SCRIPT_ERROR = "local alpha dashboard static demo script could not be built"


def test_script_help_does_not_invoke_uv(tmp_path: Path) -> None:
    marker = tmp_path / "uv-called.txt"
    result = _run_script("-Help", env=_fake_uv_env(tmp_path, marker))

    assert result.returncode == 0
    assert result.stderr == ""
    assert "AsyncScholar local alpha dashboard static demo" in result.stdout
    assert "-Output" in result.stdout
    assert "product_judgment_evidence" in result.stdout
    assert "does not pass Gate D" in result.stdout
    assert not marker.exists()


def test_script_writes_static_html_to_explicit_output(tmp_path: Path) -> None:
    output = tmp_path / "async-scholar-local-alpha-dashboard.html"

    result = _run_script("-Output", str(output))

    assert result.returncode == 0
    assert result.stderr == ""
    assert "local alpha dashboard static demo written" in result.stdout
    assert str(output) not in result.stdout
    html = output.read_text(encoding="utf-8")
    _assert_static_html_safe(html)


def test_script_default_output_generates_safe_temp_file() -> None:
    result = _run_script()

    assert result.returncode == 0
    assert result.stderr == ""
    output = _output_path_from_stdout(result.stdout)
    try:
        assert output.exists()
        assert os.path.samefile(output.parent, Path(os.environ["TEMP"]))
        _assert_static_html_safe(output.read_text(encoding="utf-8"))
    finally:
        output.unlink(missing_ok=True)


def test_script_delegates_default_output_to_static_cli(tmp_path: Path) -> None:
    marker = tmp_path / "uv-called.txt"
    result = _run_script(env=_fake_uv_env(tmp_path, marker))

    assert result.returncode == 0
    assert result.stderr == ""
    marker_text = marker.read_text(encoding="utf-8")
    assert marker_text.startswith(
        "run python -m async_scholar local-alpha-dashboard-static-demo --output "
    )
    assert "async-scholar-local-alpha-dashboard-" in marker_text
    assert marker_text.strip().endswith(".html")


def test_script_delegates_explicit_output_to_static_cli(tmp_path: Path) -> None:
    marker = tmp_path / "uv-called.txt"
    output = tmp_path / "dashboard.html"
    result = _run_script("-Output", str(output), env=_fake_uv_env(tmp_path, marker))

    assert result.returncode == 0
    assert result.stderr == ""
    assert marker.read_text(encoding="utf-8").strip() == (
        "run python -m async_scholar local-alpha-dashboard-static-demo "
        f"--output {output}"
    )


def test_script_rejects_existing_output_without_invoking_uv(tmp_path: Path) -> None:
    marker = tmp_path / "uv-called.txt"
    output = tmp_path / "dashboard.html"
    output.write_text("existing", encoding="utf-8")

    result = _run_script("-Output", str(output), env=_fake_uv_env(tmp_path, marker))

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == f"{SCRIPT_ERROR}\n"
    assert output.read_text(encoding="utf-8") == "existing"
    assert not marker.exists()


def test_script_rejects_missing_parent_without_invoking_uv(tmp_path: Path) -> None:
    marker = tmp_path / "uv-called.txt"
    output = tmp_path / "missing" / "dashboard.html"

    result = _run_script("-Output", str(output), env=_fake_uv_env(tmp_path, marker))

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == f"{SCRIPT_ERROR}\n"
    assert not output.exists()
    assert not marker.exists()


def test_script_rejects_unknown_arguments_without_invoking_uv(tmp_path: Path) -> None:
    marker = tmp_path / "uv-called.txt"
    result = _run_script(
        "-UnknownParam",
        "C:\\Users\\student\\secret-token-auth-profile",
        env=_fake_uv_env(tmp_path, marker),
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == f"{SCRIPT_ERROR}\n"
    assert "secret-token-auth-profile" not in result.stderr
    assert not marker.exists()


def test_script_rejects_missing_output_value_without_invoking_uv(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "uv-called.txt"
    result = _run_script("-Output", env=_fake_uv_env(tmp_path, marker))

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == f"{SCRIPT_ERROR}\n"
    assert str(SCRIPT) not in result.stderr
    assert not marker.exists()


def test_script_rejects_traversal_output_without_invoking_uv(
    tmp_path: Path,
) -> None:
    marker = tmp_path / "uv-called.txt"
    output = tmp_path / ".." / "async-scholar-traversal-review.html"

    result = _run_script("-Output", str(output), env=_fake_uv_env(tmp_path, marker))

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == f"{SCRIPT_ERROR}\n"
    assert not output.exists()
    assert not marker.exists()


def test_script_does_not_echo_sensitive_explicit_output_path(tmp_path: Path) -> None:
    output = tmp_path / "secret-token-auth-profile-dashboard.html"

    result = _run_script("-Output", str(output))

    assert result.returncode == 0
    assert result.stderr == ""
    assert output.exists()
    combined = f"{result.stdout}\n{result.stderr}".casefold()
    for forbidden in ("secret", "token", "auth", "profile", str(output).casefold()):
        assert forbidden not in combined


def test_script_sanitizes_uv_failure_output(tmp_path: Path) -> None:
    output = tmp_path / "dashboard.html"
    result = _run_script(
        "-Output",
        str(output),
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
    assert not output.exists()


def test_script_source_preserves_static_demo_scope() -> None:
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
        "local-alpha-dashboard-demo --host",
        "local-alpha-dashboard-demo --dry-run",
    ):
        assert forbidden not in source

    assert "local-alpha-dashboard-static-demo" in source
    assert "output" in source


def test_readme_documents_static_demo_script_boundaries() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "scripts\\run_local_alpha_dashboard_static_demo.ps1" in readme
    assert "local-alpha-dashboard-static-demo" in readme
    assert "product_judgment_evidence" in readme
    assert "does not replace product judgment evidence" in readme
    assert "pass Gate D / Product Promise Alpha" in readme


def _assert_static_html_safe(html: str) -> None:
    assert "AsyncScholar local alpha static demo" in html
    for heading in (
        "Gate D safety",
        "Evidence digest",
        "Session status",
        "Demo timeline",
        "Detected events",
        "Alert preview",
        "Confirmation queue",
        "Action controls",
        "Archive and reviewer",
        "Safety boundary",
    ):
        assert f"<h2>{heading}</h2>" in html
    assert html.count("<section") == 10
    assert "Server started: no" in html
    assert "Browser opened: no" in html
    assert "Gate D not passed" in html
    assert "Blocked on product_judgment_evidence" in html
    assert "Human product judgment: deferred" in html
    assert "Manual judgment required: yes" in html
    assert "Manual judgment recorded: no" in html
    assert "Handoff status: Ready for manual review" in html
    assert "Local bundle status: Blocked" in html
    assert "AI can complete product judgment: no" in html
    assert "Fixture source prepared" in html
    assert "Session completed" in html
    assert "Event detected" in html
    assert "Alert awaiting confirmation" in html
    assert "Archive/reviewer metadata ready" in html
    assert "Gate D blocked" in html
    assert "Run status: Completed" in html
    assert "Attendance prompt - 42s - 94% confidence" in html
    assert "Important event - 185s - 88% confidence" in html
    assert "Urgent alert" in html
    assert "Confirmation required" in html
    visible_html = _visible_html_text(html)
    assert "User confirmation required" in html
    assert "Alert status: pending" in html
    assert "Participation action sent: no" in html
    assert "Autonomous participation: no" in visible_html
    assert "Live delivery: no" in html
    assert "Academic answer behavior: no" in html
    assert "Review alert confirmation" in visible_html
    assert "Send participation action" in visible_html
    assert "Open archive reviewer" in visible_html
    assert "Record product judgment" in visible_html
    assert "Alert delivery live: no" in html
    assert "Gate D not passed" in html
    assert "Product Promise Alpha not passed" in html
    assert html.count("<button ") == 4
    assert html.count('type="button"') == 4
    assert html.count(" disabled ") == 4
    assert html.count('aria-disabled="true"') == 4
    assert "Local archive summary" in html
    assert "Reviewer artifact metadata only." in html
    assert "Safety boundary" in html
    lowered = html.casefold()
    for forbidden in (
        "<script",
        "<link",
        "<img",
        "<iframe",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "src=",
        "href=",
        "action=",
        "method=",
        "formaction=",
        "value=",
        "gate d passed",
        "product promise alpha passed",
        "product judgment evidence satisfied",
        "server started: yes",
        "browser opened: yes",
        "participation action sent: yes",
        "autonomous participation: yes",
        "live delivery: yes",
        "academic answer behavior: yes",
        "traceback",
        ".env",
        "cookie",
        "token",
        "auth",
    ):
        assert forbidden not in lowered
    _assert_no_event_handler_attributes(html)


def _output_path_from_stdout(stdout: str) -> Path:
    match = re.search(r"^Default output: (?P<path>.+)$", stdout, re.MULTILINE)
    assert match is not None, stdout
    return Path(match.group("path"))


def _visible_html_text(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)


def _assert_no_event_handler_attributes(html: str) -> None:
    assert re.search(r"\son[a-z]+\s*=", html, flags=re.IGNORECASE) is None


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
