from __future__ import annotations

import builtins
import json
import subprocess
import sys
import types
from pathlib import Path

from async_scholar import __main__ as cli

DEMO_ERROR = "local alpha dashboard demo could not be built"
INSPECTION_ERROR = "local alpha dashboard inspection could not be built"
STATIC_ERROR = "local alpha dashboard static demo could not be built"


def test_module_help_lists_local_alpha_dashboard_demo() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "async_scholar", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "local-alpha-dashboard-demo" in result.stdout
    assert "local-alpha-dashboard-inspection" in result.stdout
    assert "local-alpha-dashboard-static-demo" in result.stdout


def test_local_alpha_dashboard_demo_help_stays_lazy(monkeypatch) -> None:
    module_name = "async_scholar.ui.local_alpha_dashboard_demo"
    monkeypatch.delitem(sys.modules, module_name, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "local-alpha-dashboard-demo",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar local-alpha-dashboard-demo" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--host" in result.stdout
    assert "--port" in result.stdout
    assert module_name not in sys.modules


def test_local_alpha_dashboard_inspection_help_stays_lazy(monkeypatch) -> None:
    module_name = "async_scholar.ui.local_alpha_dashboard_demo"
    monkeypatch.delitem(sys.modules, module_name, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "local-alpha-dashboard-inspection",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar local-alpha-dashboard-inspection" in result.stdout
    assert "no-server" in result.stdout
    assert module_name not in sys.modules


def test_local_alpha_dashboard_static_demo_help_stays_lazy(monkeypatch) -> None:
    module_name = "async_scholar.ui.local_alpha_dashboard_demo"
    monkeypatch.delitem(sys.modules, module_name, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "local-alpha-dashboard-static-demo",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar local-alpha-dashboard-static-demo" in result.stdout
    assert "--output" in result.stdout
    assert "static HTML" in result.stdout
    assert module_name not in sys.modules


def test_local_alpha_dashboard_demo_dry_run_prints_compact_json() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "local-alpha-dashboard-demo",
            "--dry-run",
            "--host",
            "127.0.0.1",
            "--port",
            "8086",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert (
        result.stdout
        == json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    )
    assert payload["url"] == "http://127.0.0.1:8086"
    assert payload["server_started"] is False
    assert payload["browser_opened"] is False
    assert payload["gate_d_status"] == "not_passed"
    assert payload["product_judgment_evidence_status"] == "blocking"
    assert payload["manual_product_judgment_required"] is True
    assert payload["product_promise_alpha_pass_claimed"] is False
    assert payload["metadata_only_demo_sources"] is True
    assert payload["private_data_read"] is False
    assert payload["audio_capture_performed"] is False
    assert payload["browser_automation_performed"] is False
    assert payload["live_delivery_performed"] is False
    assert payload["scheduler_loop_performed"] is False
    assert payload["deletion_or_export_performed"] is False
    assert payload["real_online_monitoring_performed"] is False
    assert payload["autonomous_participation_performed"] is False
    assert payload["academic_answer_behavior_performed"] is False
    assert "product_judgment_evidence remains blocking" in payload["safety_summary"]
    _assert_output_safe(result.stdout, result.stderr)


def test_local_alpha_dashboard_inspection_prints_plain_text() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "local-alpha-dashboard-inspection",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.endswith("\n")
    assert "AsyncScholar local alpha inspection" in result.stdout
    assert "Server started: no" in result.stdout
    assert "Browser opened: no" in result.stdout
    assert "Gate D not passed" in result.stdout
    assert "Blocked on product_judgment_evidence" in result.stdout
    assert "Human product judgment: deferred" in result.stdout
    assert "Satisfactory evidence: 9" in result.stdout
    assert "Missing evidence: 0" in result.stdout
    assert "Manual judgment required: yes" in result.stdout
    assert "Manual judgment recorded: no" in result.stdout
    assert "Run status: Completed" in result.stdout
    assert "Source kind: Fixture demo" in result.stdout
    assert "Attendance prompt - 42s - 94% confidence" in result.stdout
    assert "Important event - 185s - 88% confidence" in result.stdout
    assert "Urgent alert" in result.stdout
    assert "Status: Pending" in result.stdout
    assert "Confirmation required" in result.stdout
    assert "Local archive summary" in result.stdout
    assert "Reviewer available" in result.stdout
    assert "Reviewer artifact metadata only." in result.stdout
    _assert_inspection_output_safe(result.stdout, result.stderr)


def test_local_alpha_dashboard_static_demo_writes_html(tmp_path: Path) -> None:
    output = tmp_path / "async-scholar-local-alpha-dashboard.html"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "local-alpha-dashboard-static-demo",
            "--output",
            str(output),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout == "local alpha dashboard static demo written\n"
    html = output.read_text(encoding="utf-8")
    assert html.startswith("<!doctype html>\n")
    assert "AsyncScholar local alpha static demo" in html
    assert "Server started: no" in html
    assert "Browser opened: no" in html
    assert "Gate D not passed" in html
    assert "Blocked on product_judgment_evidence" in html
    assert "Human product judgment: deferred" in html
    assert "Run status: Completed" in html
    assert "Attendance prompt - 42s - 94% confidence" in html
    assert "Important event - 185s - 88% confidence" in html
    assert "Urgent alert" in html
    assert "Confirmation required" in html
    assert "Local archive summary" in html
    assert "Reviewer artifact metadata only." in html
    _assert_static_output_safe(result.stdout, result.stderr, html)


def test_readme_lists_local_alpha_dashboard_inspection_command() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "local-alpha-dashboard-inspection" in readme
    assert "no-server" in readme
    assert "Gate D / Product Promise Alpha" in readme


def test_readme_lists_local_alpha_dashboard_static_demo_command() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "local-alpha-dashboard-static-demo" in readme
    assert "--output" in readme
    assert "static HTML" in readme


def test_local_alpha_dashboard_demo_rejects_public_host_without_echo() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "local-alpha-dashboard-demo",
            "--dry-run",
            "--host",
            "0.0.0.0",
            "--port",
            "8086",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == f"{DEMO_ERROR}\n"
    assert "0.0.0.0" not in result.stderr


def test_local_alpha_dashboard_demo_rejects_extra_args_safely() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "local-alpha-dashboard-demo",
            "--dry-run",
            "C:\\Users\\student\\token-secret-auth-profile",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == f"{DEMO_ERROR}\n"
    assert "token-secret-auth-profile" not in result.stderr


def test_local_alpha_dashboard_inspection_rejects_extra_args_safely() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "local-alpha-dashboard-inspection",
            "C:\\Users\\student\\token-secret-auth-profile",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == f"{INSPECTION_ERROR}\n"
    assert "token-secret-auth-profile" not in result.stderr


def test_local_alpha_dashboard_static_demo_requires_output_safely() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "local-alpha-dashboard-static-demo",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == f"{STATIC_ERROR}\n"


def test_local_alpha_dashboard_static_demo_rejects_extra_args_safely(
    tmp_path: Path,
) -> None:
    output = tmp_path / "dashboard.html"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "local-alpha-dashboard-static-demo",
            "--output",
            str(output),
            "C:\\Users\\student\\token-secret-auth-profile",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == f"{STATIC_ERROR}\n"
    assert "token-secret-auth-profile" not in result.stderr
    assert not output.exists()


def test_local_alpha_dashboard_demo_misordered_uses_fixed_error() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "C:\\Users\\student\\token-secret-auth-profile",
            "local-alpha-dashboard-demo",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == f"{DEMO_ERROR}\n"
    assert "token-secret-auth-profile" not in result.stderr


def test_local_alpha_dashboard_inspection_misordered_uses_fixed_error() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "C:\\Users\\student\\token-secret-auth-profile",
            "local-alpha-dashboard-inspection",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == f"{INSPECTION_ERROR}\n"
    assert "token-secret-auth-profile" not in result.stderr


def test_local_alpha_dashboard_static_demo_misordered_uses_fixed_error() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "C:\\Users\\student\\token-secret-auth-profile",
            "local-alpha-dashboard-static-demo",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert result.stderr == f"{STATIC_ERROR}\n"
    assert "token-secret-auth-profile" not in result.stderr


def test_local_alpha_dashboard_demo_command_delegates_to_helper(
    capsys,
    monkeypatch,
) -> None:
    module_name = "async_scholar.ui.local_alpha_dashboard_demo"
    fake_module = types.ModuleType(module_name)
    received: dict[str, object] = {}

    def fake_build_dry_run(*, host: str, port: int) -> dict[str, object]:
        received["host"] = host
        received["port"] = port
        return {
            "demo_kind": "local_alpha_dashboard_demo",
            "url": f"http://{host}:{port}",
            "host": host,
            "port": port,
            "dry_run": True,
            "server_started": False,
            "browser_opened": False,
            "gate_d_status": "not_passed",
            "product_judgment_evidence_status": "blocking",
            "manual_product_judgment_required": True,
            "product_promise_alpha_pass_claimed": False,
            "metadata_only_demo_sources": True,
            "private_data_read": False,
            "audio_capture_performed": False,
            "browser_automation_performed": False,
            "live_delivery_performed": False,
            "scheduler_loop_performed": False,
            "deletion_or_export_performed": False,
            "real_online_monitoring_performed": False,
            "autonomous_participation_performed": False,
            "academic_answer_behavior_performed": False,
            "safety_summary": (
                "Local metadata-only demo for human inspection. Gate D is not "
                "passed; product_judgment_evidence remains blocking. It uses "
                "fixed local fixture-style metadata and performs no real meeting "
                "access, private content reads, capture, live delivery, timed "
                "runner, deletion/export, participation, or answer behavior."
            ),
        }

    fake_module.build_local_alpha_dashboard_demo_dry_run = fake_build_dry_run
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(
        [
            "local-alpha-dashboard-demo",
            "--dry-run",
            "--host",
            "localhost",
            "--port",
            "8086",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert received == {"host": "localhost", "port": 8086}
    assert json.loads(captured.out)["url"] == "http://localhost:8086"


def test_local_alpha_dashboard_inspection_command_delegates_to_helper(
    capsys,
    monkeypatch,
) -> None:
    module_name = "async_scholar.ui.local_alpha_dashboard_demo"
    fake_module = types.ModuleType(module_name)
    called: dict[str, bool] = {}

    def fake_build_summary() -> str:
        called["summary"] = True
        return _valid_inspection_summary()

    fake_module.build_local_alpha_dashboard_inspection_summary = fake_build_summary
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(["local-alpha-dashboard-inspection"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert captured.out == _valid_inspection_summary()
    assert called == {"summary": True}


def test_local_alpha_dashboard_static_demo_command_delegates_to_helper(
    capsys,
    monkeypatch,
    tmp_path: Path,
) -> None:
    module_name = "async_scholar.ui.local_alpha_dashboard_demo"
    fake_module = types.ModuleType(module_name)
    called: dict[str, bool] = {}
    output = tmp_path / "dashboard.html"

    def fake_build_html() -> str:
        called["html"] = True
        return _valid_static_demo_html()

    fake_module.build_local_alpha_dashboard_static_demo_html = fake_build_html
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(["local-alpha-dashboard-static-demo", "--output", str(output)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == "local alpha dashboard static demo written\n"
    assert captured.err == ""
    assert called == {"html": True}
    assert output.read_text(encoding="utf-8") == _valid_static_demo_html()


def test_local_alpha_dashboard_demo_rejects_malformed_helper_payload(
    capsys,
    monkeypatch,
) -> None:
    module_name = "async_scholar.ui.local_alpha_dashboard_demo"
    fake_module = types.ModuleType(module_name)

    def fake_build_dry_run(*, host: str, port: int) -> dict[str, object]:
        return {
            "demo_kind": "local_alpha_dashboard_demo",
            "url": "https://meet.example.edu/class-room?token=private",
            "host": host,
            "port": port,
            "dry_run": True,
            "server_started": False,
            "browser_opened": False,
            "gate_d_status": "not_passed",
            "product_judgment_evidence_status": "blocking",
            "manual_product_judgment_required": True,
            "product_promise_alpha_pass_claimed": False,
            "metadata_only_demo_sources": True,
            "private_data_read": False,
            "audio_capture_performed": False,
            "browser_automation_performed": False,
            "live_delivery_performed": False,
            "scheduler_loop_performed": False,
            "deletion_or_export_performed": False,
            "real_online_monitoring_performed": False,
            "autonomous_participation_performed": False,
            "academic_answer_behavior_performed": False,
            "safety_summary": "Traceback (most recent call last) .env token",
        }

    fake_module.build_local_alpha_dashboard_demo_dry_run = fake_build_dry_run
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(["local-alpha-dashboard-demo", "--dry-run"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == f"{DEMO_ERROR}\n"
    _assert_output_safe(captured.out, captured.err)


def test_local_alpha_dashboard_inspection_rejects_malformed_helper_output(
    capsys,
    monkeypatch,
) -> None:
    module_name = "async_scholar.ui.local_alpha_dashboard_demo"
    fake_module = types.ModuleType(module_name)

    def fake_build_summary() -> str:
        return "Traceback C:\\Users\\student\\.env token Product Promise Alpha passed"

    fake_module.build_local_alpha_dashboard_inspection_summary = fake_build_summary
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(["local-alpha-dashboard-inspection"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == f"{INSPECTION_ERROR}\n"
    _assert_inspection_output_safe(captured.out, captured.err)


def test_local_alpha_dashboard_static_demo_rejects_malformed_helper_output(
    capsys,
    monkeypatch,
    tmp_path: Path,
) -> None:
    module_name = "async_scholar.ui.local_alpha_dashboard_demo"
    fake_module = types.ModuleType(module_name)
    output = tmp_path / "dashboard.html"

    def fake_build_html() -> str:
        return "Traceback C:\\Users\\student\\.env token Product Promise Alpha passed"

    fake_module.build_local_alpha_dashboard_static_demo_html = fake_build_html
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(["local-alpha-dashboard-static-demo", "--output", str(output)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == f"{STATIC_ERROR}\n"
    assert not output.exists()
    _assert_static_output_safe(captured.out, captured.err, "")


def test_local_alpha_dashboard_inspection_sanitizes_helper_failure(
    capsys,
    monkeypatch,
) -> None:
    module_name = "async_scholar.ui.local_alpha_dashboard_demo"
    fake_module = types.ModuleType(module_name)

    def fake_build_summary() -> str:
        raise RuntimeError("C:\\Users\\student\\.env token traceback")

    fake_module.build_local_alpha_dashboard_inspection_summary = fake_build_summary
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(["local-alpha-dashboard-inspection"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == f"{INSPECTION_ERROR}\n"
    _assert_inspection_output_safe(captured.out, captured.err)


def test_local_alpha_dashboard_static_demo_sanitizes_helper_failure(
    capsys,
    monkeypatch,
    tmp_path: Path,
) -> None:
    module_name = "async_scholar.ui.local_alpha_dashboard_demo"
    fake_module = types.ModuleType(module_name)
    output = tmp_path / "dashboard.html"

    def fake_build_html() -> str:
        raise RuntimeError("C:\\Users\\student\\.env token traceback")

    fake_module.build_local_alpha_dashboard_static_demo_html = fake_build_html
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(["local-alpha-dashboard-static-demo", "--output", str(output)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == f"{STATIC_ERROR}\n"
    assert not output.exists()
    _assert_static_output_safe(captured.out, captured.err, "")


def test_local_alpha_dashboard_static_demo_rejects_invalid_output_target(
    capsys,
    monkeypatch,
    tmp_path: Path,
) -> None:
    module_name = "async_scholar.ui.local_alpha_dashboard_demo"
    fake_module = types.ModuleType(module_name)

    def fake_build_html() -> str:
        return _valid_static_demo_html()

    fake_module.build_local_alpha_dashboard_static_demo_html = fake_build_html
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(
        ["local-alpha-dashboard-static-demo", "--output", str(tmp_path)]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == f"{STATIC_ERROR}\n"
    assert str(tmp_path) not in captured.err


def test_local_alpha_dashboard_static_demo_rejects_existing_output_file(
    capsys,
    monkeypatch,
    tmp_path: Path,
) -> None:
    module_name = "async_scholar.ui.local_alpha_dashboard_demo"
    fake_module = types.ModuleType(module_name)
    output = tmp_path / "dashboard.html"
    output.write_text("existing", encoding="utf-8")

    def fake_build_html() -> str:
        return _valid_static_demo_html()

    fake_module.build_local_alpha_dashboard_static_demo_html = fake_build_html
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(["local-alpha-dashboard-static-demo", "--output", str(output)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == f"{STATIC_ERROR}\n"
    assert output.read_text(encoding="utf-8") == "existing"


def test_local_alpha_dashboard_static_demo_rejects_missing_parent(
    capsys,
    monkeypatch,
    tmp_path: Path,
) -> None:
    module_name = "async_scholar.ui.local_alpha_dashboard_demo"
    fake_module = types.ModuleType(module_name)
    output = tmp_path / "missing" / "dashboard.html"

    def fake_build_html() -> str:
        return _valid_static_demo_html()

    fake_module.build_local_alpha_dashboard_static_demo_html = fake_build_html
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(["local-alpha-dashboard-static-demo", "--output", str(output)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == f"{STATIC_ERROR}\n"
    assert not output.exists()


def test_local_alpha_dashboard_static_demo_rejects_uri_output(
    capsys,
    monkeypatch,
) -> None:
    module_name = "async_scholar.ui.local_alpha_dashboard_demo"
    fake_module = types.ModuleType(module_name)

    def fake_build_html() -> str:
        return _valid_static_demo_html()

    fake_module.build_local_alpha_dashboard_static_demo_html = fake_build_html
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(
        ["local-alpha-dashboard-static-demo", "--output", "file:///tmp/demo.html"]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == f"{STATIC_ERROR}\n"
    assert "file://" not in captured.err


def test_local_alpha_dashboard_demo_live_mode_delegates_without_dry_run_output(
    capsys,
    monkeypatch,
) -> None:
    module_name = "async_scholar.ui.local_alpha_dashboard_demo"
    fake_module = types.ModuleType(module_name)
    received: dict[str, object] = {}

    def fake_build_dry_run(*, host: str, port: int) -> dict[str, object]:
        return _valid_dry_run_payload(host=host, port=port)

    def fake_run_demo(*, host: str, port: int) -> None:
        received["host"] = host
        received["port"] = port

    fake_module.build_local_alpha_dashboard_demo_dry_run = fake_build_dry_run
    fake_module.run_local_alpha_dashboard_demo = fake_run_demo
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(
        [
            "local-alpha-dashboard-demo",
            "--host",
            "127.0.0.1",
            "--port",
            "8086",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""
    assert received == {"host": "127.0.0.1", "port": 8086}


def test_local_alpha_dashboard_demo_live_mode_sanitizes_startup_failure(
    capsys,
    monkeypatch,
) -> None:
    module_name = "async_scholar.ui.local_alpha_dashboard_demo"
    fake_module = types.ModuleType(module_name)

    def fake_build_dry_run(*, host: str, port: int) -> dict[str, object]:
        return _valid_dry_run_payload(host=host, port=port)

    def fake_run_demo(*, host: str, port: int) -> None:
        raise OSError("C:\\Users\\student\\.env token traceback")

    fake_module.build_local_alpha_dashboard_demo_dry_run = fake_build_dry_run
    fake_module.run_local_alpha_dashboard_demo = fake_run_demo
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(["local-alpha-dashboard-demo"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == f"{DEMO_ERROR}\n"
    _assert_output_safe(captured.out, captured.err)


def test_local_alpha_dashboard_demo_live_mode_sanitizes_unexpected_failure(
    capsys,
    monkeypatch,
) -> None:
    module_name = "async_scholar.ui.local_alpha_dashboard_demo"
    fake_module = types.ModuleType(module_name)

    def fake_build_dry_run(*, host: str, port: int) -> dict[str, object]:
        return _valid_dry_run_payload(host=host, port=port)

    def fake_run_demo(*, host: str, port: int) -> None:
        raise Exception("C:\\Users\\student\\.env token traceback")

    fake_module.build_local_alpha_dashboard_demo_dry_run = fake_build_dry_run
    fake_module.run_local_alpha_dashboard_demo = fake_run_demo
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(["local-alpha-dashboard-demo"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == f"{DEMO_ERROR}\n"
    _assert_output_safe(captured.out, captured.err)


def test_local_alpha_dashboard_demo_sanitizes_import_failure(
    capsys,
    monkeypatch,
) -> None:
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "async_scholar.ui.local_alpha_dashboard_demo":
            raise ImportError("C:\\Users\\student\\.env token traceback")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    exit_code = cli.main(["local-alpha-dashboard-demo", "--dry-run"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == f"{DEMO_ERROR}\n"


def test_local_alpha_dashboard_inspection_sanitizes_import_failure(
    capsys,
    monkeypatch,
) -> None:
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "async_scholar.ui.local_alpha_dashboard_demo":
            raise ImportError("C:\\Users\\student\\.env token traceback")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    exit_code = cli.main(["local-alpha-dashboard-inspection"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == f"{INSPECTION_ERROR}\n"


def test_local_alpha_dashboard_static_demo_sanitizes_import_failure(
    capsys,
    monkeypatch,
    tmp_path: Path,
) -> None:
    real_import = builtins.__import__
    output = tmp_path / "dashboard.html"

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "async_scholar.ui.local_alpha_dashboard_demo":
            raise ImportError("C:\\Users\\student\\.env token traceback")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    exit_code = cli.main(["local-alpha-dashboard-static-demo", "--output", str(output)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == f"{STATIC_ERROR}\n"
    assert not output.exists()


def _valid_dry_run_payload(*, host: str, port: int) -> dict[str, object]:
    return {
        "demo_kind": "local_alpha_dashboard_demo",
        "url": f"http://{host}:{port}",
        "host": host,
        "port": port,
        "dry_run": True,
        "server_started": False,
        "browser_opened": False,
        "gate_d_status": "not_passed",
        "product_judgment_evidence_status": "blocking",
        "manual_product_judgment_required": True,
        "product_promise_alpha_pass_claimed": False,
        "metadata_only_demo_sources": True,
        "private_data_read": False,
        "audio_capture_performed": False,
        "browser_automation_performed": False,
        "live_delivery_performed": False,
        "scheduler_loop_performed": False,
        "deletion_or_export_performed": False,
        "real_online_monitoring_performed": False,
        "autonomous_participation_performed": False,
        "academic_answer_behavior_performed": False,
        "safety_summary": (
            "Local metadata-only demo for human inspection. Gate D is not "
            "passed; product_judgment_evidence remains blocking. It uses "
            "fixed local fixture-style metadata and performs no real meeting "
            "access, private content reads, capture, live delivery, timed "
            "runner, deletion/export, participation, or answer behavior."
        ),
    }


def _valid_inspection_summary() -> str:
    return (
        "AsyncScholar local alpha inspection\n"
        "Server started: no\n"
        "Browser opened: no\n"
        "Gate D safety\n"
        "Gate D not passed\n"
        "Blocked on product_judgment_evidence\n"
        "Human product judgment: deferred\n"
        "Satisfactory evidence: 9\n"
        "Missing evidence: 0\n"
        "Blocking evidence: product_judgment_evidence\n"
        "Ready for gate review: no\n"
        "Manual judgment required: yes\n"
        "Manual judgment recorded: no\n"
        "Session status\n"
        "Run status: Completed\n"
        "Source kind: Fixture demo\n"
        "Segments: 5\n"
        "Events: 2\n"
        "Detected events\n"
        "Attendance prompt - 42s - 94% confidence\n"
        "Important event - 185s - 88% confidence\n"
        "Alert preview\n"
        "Urgent alert | Review confirmation before acting. | Severity: Urgent | "
        "Status: Pending | Confirmation required\n"
        "Archive and reviewer\n"
        "Local archive summary | Reviewer available | Events: 2 | Alerts: 1 | "
        "Updated unknown | Reviewer artifact metadata only.\n"
        "Safety boundary\n"
        "Local alpha demo only: no real meeting, private meeting data, "
        "audio capture, live delivery, participation, or academic answers.\n"
    )


def _valid_static_demo_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>AsyncScholar local alpha static demo</title>
</head>
<body>
  <main>
    <h1>AsyncScholar local alpha static demo</h1>
    <p>Server started: no</p>
    <p>Browser opened: no</p>
    <section>
      <h2>Gate D safety</h2>
      <p>Gate D not passed</p>
      <p>Blocked on product_judgment_evidence</p>
      <p>Human product judgment: deferred</p>
      <p>Manual judgment required: yes</p>
      <p>Manual judgment recorded: no</p>
    </section>
    <section>
      <h2>Session status</h2>
      <p>Run status: Completed</p>
      <p>Source kind: Fixture demo</p>
    </section>
    <section>
      <h2>Detected events</h2>
      <p>Attendance prompt - 42s - 94% confidence</p>
      <p>Important event - 185s - 88% confidence</p>
    </section>
    <section>
      <h2>Alert preview</h2>
      <p>Urgent alert | Status: Pending | Confirmation required</p>
    </section>
    <section>
      <h2>Archive and reviewer</h2>
      <p>Local archive summary | Reviewer artifact metadata only.</p>
    </section>
    <section>
      <h2>Safety boundary</h2>
      <p>Local alpha demo only.</p>
    </section>
  </main>
</body>
</html>
"""


def _assert_output_safe(stdout: str, stderr: str) -> None:
    combined = f"{stdout}\n{stderr}".lower()
    for forbidden in (
        "good morning",
        "meet.example",
        "token",
        "cookie",
        ".env",
        "auth",
        "browser profile",
        "traceback",
        ".wav",
        ".mp4",
        "c:\\",
        "gate d passed",
        "product promise alpha passed",
        "product judgment evidence satisfied",
        "live delivery performed",
        "autonomous participation",
        "academic answer",
    ):
        assert forbidden not in combined


def _assert_inspection_output_safe(stdout: str, stderr: str) -> None:
    combined = f"{stdout}\n{stderr}".lower()
    for forbidden in (
        "good morning",
        "meet.example",
        "token",
        "cookie",
        ".env",
        "auth",
        "browser profile",
        "traceback",
        ".wav",
        ".mp4",
        "c:\\",
        "gate d passed",
        "product promise alpha passed",
        "product judgment evidence satisfied",
        "live delivery performed",
        "autonomous participation",
    ):
        assert forbidden not in combined


def _assert_static_output_safe(stdout: str, stderr: str, html: str) -> None:
    combined = f"{stdout}\n{stderr}\n{html}".lower()
    for forbidden in (
        "good morning",
        "meet.example",
        "token",
        "cookie",
        ".env",
        "auth",
        "browser profile",
        "traceback",
        ".wav",
        ".mp4",
        "c:\\",
        "gate d passed",
        "product promise alpha passed",
        "product judgment evidence satisfied",
        "server started: yes",
        "browser opened: yes",
        "live delivery performed",
        "autonomous participation",
    ):
        assert forbidden not in combined
