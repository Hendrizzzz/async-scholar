from __future__ import annotations

import builtins
import json
import subprocess
import sys
import types

from async_scholar import __main__ as cli

DEMO_ERROR = "local alpha dashboard demo could not be built"


def test_module_help_lists_local_alpha_dashboard_demo() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "async_scholar", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "local-alpha-dashboard-demo" in result.stdout


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
