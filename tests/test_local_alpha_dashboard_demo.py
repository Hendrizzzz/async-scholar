from __future__ import annotations

import importlib
import inspect
import json
import subprocess
import sys
import textwrap

import pytest

PRIVATE_VALUES = (
    "Good morning, everyone. I am going to take attendance",
    "https://meet.example.edu/class-room?token=private",
    r"C:\Users\student\data\sessions\fixture\events.jsonl",
    r"C:\private\lecture.wav",
    r"C:\private\lecture.mp4",
    "secret.env",
    "cookie-value",
    "token-value",
    "auth-state",
    "browser profile",
    "Traceback (most recent call last)",
    r"C:\models\private-model.bin",
    r"C:\generated\clip.png",
)


def test_dashboard_demo_module_import_is_safe() -> None:
    code = textwrap.dedent(
        """
        import importlib
        import json
        import sys

        before = set(sys.modules)
        importlib.import_module("async_scholar.ui.local_alpha_dashboard_demo")
        loaded = set(sys.modules) - before
        prefixes = (
            "fastapi",
            "nicegui",
            "async_scholar.demo",
            "async_scholar.rules",
            "async_scholar.artifacts",
            "async_scholar.alert_dispatch",
            "async_scholar.desktop_notifier",
            "async_scholar.telegram_notifier",
            "async_scholar.scheduler",
            "async_scholar.browser",
            "async_scholar.audio",
            "async_scholar.stt",
        )
        forbidden = sorted(
            name
            for name in loaded
            if any(
                name == prefix or name.startswith(f"{prefix}.")
                for prefix in prefixes
            )
        )
        print(json.dumps(forbidden))
        raise SystemExit(bool(forbidden))
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads(completed.stdout) == []

    source = inspect.getsource(_demo_module()).casefold()
    for forbidden in (
        "async_scholar.demo",
        "run_fixture_demo",
        "load_transcript",
        "data/",
        "data\\",
        ".env",
        "cookie",
        "token",
        "playwright",
        "selenium",
        "audio",
        "stt",
        "vad",
        "scheduler",
        "telegram",
        "desktop_notifier",
    ):
        assert forbidden not in source


def test_ui_package_lazy_export_for_dashboard_demo_is_safe() -> None:
    code = textwrap.dedent(
        """
        import importlib
        import json
        import sys

        package = importlib.import_module("async_scholar.ui")
        assert "build_local_alpha_dashboard_demo_dry_run" in package.__all__
        before = set(sys.modules)
        build = package.build_local_alpha_dashboard_demo_dry_run
        loaded = set(sys.modules) - before
        prefixes = ("fastapi", "nicegui", "async_scholar.demo", "async_scholar.audio")
        forbidden = sorted(
            name
            for name in loaded
            if any(
                name == prefix or name.startswith(f"{prefix}.")
                for prefix in prefixes
            )
        )
        print(json.dumps({"callable": callable(build), "forbidden": forbidden}))
        raise SystemExit(bool(forbidden))
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads(completed.stdout) == {"callable": True, "forbidden": []}


def test_build_demo_sources_are_deterministic_and_metadata_only() -> None:
    demo = _demo_module()
    first = demo.build_local_alpha_dashboard_demo_sources()
    second = demo.build_local_alpha_dashboard_demo_sources()

    assert first == second
    assert first.session_status.status()["run_status"] == "completed"
    assert first.session_status.status()["source_kind"] == "fixture_demo"
    assert first.session_status.status()["segment_count"] == 5
    assert first.session_status.status()["event_count"] == 2
    assert first.events()[0]["event_type"] == "attendance_prompt"
    assert first.alerts.alerts()[0]["status"] == "pending"
    assert first.alerts.alerts()[0]["confirmation_required"] is True
    assert first.archive.items()[0]["title"] == "Local archive summary"
    assert first.gate_d["product_judgment_evidence_status"] == "blocking"
    assert first.gate_d["blocking_evidence"] == ["product_judgment_evidence"]
    assert first.gate_d["satisfactory_evidence_count"] == 9
    assert first.gate_d["missing_evidence_count"] == 0
    assert first.gate_d["ready_for_gate_review"] is False
    assert first.gate_d["manual_product_judgment_required"] is True
    assert first.gate_d["manual_product_judgment_recorded"] is False
    assert first.gate_d["gate_d_pass_claimed"] is False
    assert first.gate_d["product_promise_alpha_pass_claimed"] is False

    exposed = repr(first)
    for private_value in PRIVATE_VALUES:
        assert private_value not in exposed


def test_dry_run_payload_is_safe_and_loopback_only() -> None:
    demo = _demo_module()

    payload = demo.build_local_alpha_dashboard_demo_dry_run(
        host="127.0.0.1",
        port=8086,
    )

    assert tuple(payload) == demo.LOCAL_ALPHA_DASHBOARD_DEMO_DRY_RUN_KEYS
    assert payload["demo_kind"] == "local_alpha_dashboard_demo"
    assert payload["url"] == "http://127.0.0.1:8086"
    assert payload["host"] == "127.0.0.1"
    assert payload["port"] == 8086
    assert payload["dry_run"] is True
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
    assert payload["safety_summary"] == demo.LOCAL_ALPHA_DASHBOARD_DEMO_SAFETY_SUMMARY

    serialized = json.dumps(payload, sort_keys=True)
    for private_value in PRIVATE_VALUES:
        assert private_value not in serialized


@pytest.mark.parametrize(
    "host",
    [
        "0.0.0.0",
        "192.168.1.22",
        "example.com",
        r"C:\Users\student\token-secret-auth-profile",
        "",
    ],
)
def test_dry_run_rejects_non_loopback_hosts_without_echo(host: str) -> None:
    demo = _demo_module()

    with pytest.raises(
        ValueError, match="local alpha dashboard demo could not be built"
    ):
        demo.build_local_alpha_dashboard_demo_dry_run(host=host, port=8086)


@pytest.mark.parametrize("port", [0, -1, 65536, "8086", True])
def test_dry_run_rejects_invalid_ports(port: object) -> None:
    demo = _demo_module()

    with pytest.raises(
        ValueError, match="local alpha dashboard demo could not be built"
    ):
        demo.build_local_alpha_dashboard_demo_dry_run(host="127.0.0.1", port=port)


def _demo_module():
    return importlib.import_module("async_scholar.ui.local_alpha_dashboard_demo")
