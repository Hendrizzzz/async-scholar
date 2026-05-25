from __future__ import annotations

import ast
import builtins
import inspect
import json
import sys
import types
from pathlib import Path

import pytest

from async_scholar.gate_d_local_evidence_bundle import (
    GATE_D_LOCAL_EVIDENCE_BUNDLE_ERROR,
    build_local_gate_d_smoke_evidence_bundle,
)

EXPECTED_GATE_D_LOCAL_EVIDENCE_BUNDLE = {
    "bundle_kind": "local_gate_d_smoke_evidence_bundle",
    "mic_diagnostics_after_reboot_status": "satisfactory",
    "alert_routing_status": "satisfactory",
    "security_review_status": "satisfactory",
    "policy_gate_tests_status": "satisfactory",
    "rollback_plan_for_loopback_playwright_spike_status": "satisfactory",
    "signal_quality_evidence_status": "satisfactory",
    "scheduler_lifecycle_evidence_status": "satisfactory",
    "delivery_path_evidence_status": "satisfactory",
    "monitoring_boundary_evidence_status": "satisfactory",
    "product_judgment_evidence_status": "missing",
    "missing_evidence": [
        "product_judgment_evidence",
    ],
    "missing_evidence_count": 1,
    "blocking_evidence": [],
    "blocking_evidence_count": 0,
    "satisfactory_evidence_count": 9,
    "ready_for_gate_review": False,
    "readiness_decision": "blocked",
    "readiness_reason": "required_gate_d_readiness_evidence_missing_or_blocking",
    "gap_decision": "gaps_present",
    "gap_reason": "required_gate_d_evidence_gaps_present",
    "live_delivery_performed": False,
    "real_online_monitoring_performed": False,
    "browser_automation_performed": False,
    "audio_capture_performed": False,
    "scheduler_execution_performed": False,
    "gate_d_pass_claimed": False,
    "product_promise_alpha_pass_claimed": False,
}


def test_local_gate_d_smoke_evidence_bundle_returns_exact_allowlisted_output() -> None:
    payload = build_local_gate_d_smoke_evidence_bundle()

    assert type(payload) is dict
    assert payload == EXPECTED_GATE_D_LOCAL_EVIDENCE_BUNDLE
    assert list(payload) == list(EXPECTED_GATE_D_LOCAL_EVIDENCE_BUNDLE)
    assert json.loads(json.dumps(payload)) == payload
    _assert_bundle_output_is_safe(payload)


def test_local_gate_d_smoke_evidence_bundle_accepts_no_input() -> None:
    assert inspect.signature(build_local_gate_d_smoke_evidence_bundle).parameters == {}


def test_local_gate_d_bundle_omits_raw_helper_payloads() -> None:
    payload = build_local_gate_d_smoke_evidence_bundle()

    raw_helper_keys = {
        "smoke_kind",
        "provider",
        "event_type_known",
        "severity",
        "status",
        "requires_confirmation",
        "delivery_performed",
        "error_kind",
        "decision",
        "reason",
        "start_authorization_status",
        "start_block_reason",
        "desktop_path_status",
        "telegram_path_status",
        "synthetic_fixture_status",
        "html_inspection_status",
        "session_history_status",
        "evidence_kind",
        "rollback_plan_document_status",
        "privacy_boundary_review_status",
        "explicit_invocation_boundary_status",
        "recorded_scalar_post_reboot_evidence_status",
        "ticket_126_public_open_evidence_status",
        "public_open_sample_rate_hz",
        "public_open_vad_segment_count",
        "public_open_stt_segment_count",
        "artifact_presence_checks_passed",
        "auth_profile_accessed",
        "device_name_exposed",
        "sqlite_accessed",
        "network_performed",
        "subprocess_performed",
        "readiness_kind",
        "summary_kind",
    }
    assert set(payload).isdisjoint(raw_helper_keys)


def test_local_gate_d_smoke_evidence_bundle_derives_statuses_from_nested_smokes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    _install_fake_modules(monkeypatch, seen)

    payload = build_local_gate_d_smoke_evidence_bundle()

    assert seen == {
        "alert_event_type": "attendance_prompt",
        "policy_called": True,
        "delivery_called": True,
        "monitoring_called": True,
        "mic_after_reboot_called": True,
        "signal_quality_called": True,
        "rollback_plan_called": True,
        "security_review_called": True,
        "scheduler_lifecycle_called": True,
        "readiness_statuses": _fixed_status_inputs(),
        "gap_statuses": _fixed_status_inputs(),
    }
    assert payload == EXPECTED_GATE_D_LOCAL_EVIDENCE_BUNDLE


def test_local_gate_d_bundle_maps_missing_and_satisfactory_categories() -> None:
    payload = build_local_gate_d_smoke_evidence_bundle()

    satisfactory_statuses = [
        key
        for key, value in payload.items()
        if key.endswith("_status") and value == "satisfactory"
    ]
    missing_statuses = [
        key
        for key, value in payload.items()
        if key.endswith("_status") and value == "missing"
    ]
    assert satisfactory_statuses == [
        "mic_diagnostics_after_reboot_status",
        "alert_routing_status",
        "security_review_status",
        "policy_gate_tests_status",
        "rollback_plan_for_loopback_playwright_spike_status",
        "signal_quality_evidence_status",
        "scheduler_lifecycle_evidence_status",
        "delivery_path_evidence_status",
        "monitoring_boundary_evidence_status",
    ]
    assert missing_statuses == [
        "product_judgment_evidence_status",
    ]
    assert payload["missing_evidence"] == [
        "product_judgment_evidence",
    ]
    assert payload["blocking_evidence"] == []


def test_local_gate_d_smoke_evidence_bundle_reports_blocked_readiness_and_gaps() -> (
    None
):
    payload = build_local_gate_d_smoke_evidence_bundle()

    assert payload["ready_for_gate_review"] is False
    assert payload["readiness_decision"] == "blocked"
    assert payload["readiness_reason"] == (
        "required_gate_d_readiness_evidence_missing_or_blocking"
    )
    assert payload["gap_decision"] == "gaps_present"
    assert payload["gap_reason"] == "required_gate_d_evidence_gaps_present"
    assert payload["missing_evidence_count"] == 1
    assert payload["blocking_evidence_count"] == 0
    assert payload["satisfactory_evidence_count"] == 9


def test_local_gate_d_smoke_evidence_bundle_sanitizes_helper_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    helper_module = types.ModuleType("async_scholar.delivery_path_smoke")

    def fake_build_local_delivery_path_smoke() -> dict[str, object]:
        raise RuntimeError("C:\\Users\\student\\.env BOT_TOKEN=secret traceback")

    helper_module.build_local_delivery_path_smoke = fake_build_local_delivery_path_smoke
    monkeypatch.setitem(
        sys.modules,
        "async_scholar.delivery_path_smoke",
        helper_module,
    )

    with pytest.raises(ValueError) as exc_info:
        build_local_gate_d_smoke_evidence_bundle()

    assert str(exc_info.value) == GATE_D_LOCAL_EVIDENCE_BUNDLE_ERROR
    assert exc_info.value.__cause__ is None
    _assert_error_is_sanitized(str(exc_info.value))


def test_local_gate_d_smoke_evidence_bundle_sanitizes_import_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "async_scholar.monitoring_boundary_smoke":
            raise ImportError(
                "C:\\Users\\student\\.env BOT_TOKEN=secret import traceback"
            )
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ValueError) as exc_info:
        build_local_gate_d_smoke_evidence_bundle()

    assert str(exc_info.value) == GATE_D_LOCAL_EVIDENCE_BUNDLE_ERROR
    assert exc_info.value.__cause__ is None
    _assert_error_is_sanitized(str(exc_info.value))


def test_local_gate_d_smoke_evidence_bundle_sanitizes_malformed_delegated_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}
    modules = _install_fake_modules(monkeypatch, seen)

    def fake_build_gate_d_readiness_report(**statuses: object) -> dict[str, object]:
        return {
            **_expected_readiness_report(statuses),
            "ready_for_gate_review": True,
        }

    modules[
        "async_scholar.gate_d_readiness"
    ].build_gate_d_readiness_report = fake_build_gate_d_readiness_report

    with pytest.raises(ValueError) as exc_info:
        build_local_gate_d_smoke_evidence_bundle()

    assert str(exc_info.value) == GATE_D_LOCAL_EVIDENCE_BUNDLE_ERROR
    assert exc_info.value.__cause__ is None


def test_local_gate_d_smoke_evidence_bundle_source_guards_forbidden_surfaces() -> None:
    source = Path("src/async_scholar/gate_d_local_evidence_bundle.py").read_text(
        encoding="utf-8"
    )
    source_lower = source.lower()
    parsed = ast.parse(source)

    imported_names: set[str] = set()
    for node in ast.walk(parsed):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_names.add(node.module)

    for forbidden_import in (
        "os",
        "pathlib",
        "sqlite3",
        "subprocess.",
        "popen",
        "socket",
        "urllib",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "webbrowser",
        "sounddevice",
        "asyncio",
        "threading",
        "time",
    ):
        assert forbidden_import not in imported_names

    assert "build_local_alert_routing_smoke" in source
    assert '"attendance_prompt"' in source
    assert "build_local_policy_gate_smoke" in source
    assert "build_local_delivery_path_smoke" in source
    assert "build_local_monitoring_boundary_smoke" in source
    assert "build_local_gate_d_mic_diagnostics_after_reboot_evidence" in source
    assert "build_local_gate_d_signal_quality_evidence" in source
    assert "build_local_gate_d_rollback_plan_evidence" in source
    assert "build_local_gate_d_security_review_evidence" in source
    assert "build_local_gate_d_scheduler_lifecycle_evidence" in source
    assert "build_gate_d_readiness_report" in source
    assert "build_gate_d_evidence_gap_summary" in source

    for forbidden_fragment in (
        "build_local_session_window_lifecycle_smoke",
        "schedule_store",
        "scheduled_start",
        "dispatch_alert",
        "dispatch_desktop_notification",
        "dispatch_telegram_alert_notification",
        "write_stored_session_window",
        "build_stored_session_window",
        "archive_export",
        "archive_delete",
        "open(",
        "read_text",
        "write_text",
        "mkdir",
        "unlink",
        "remove(",
        "rmdir",
        "rmtree",
        "urlopen(",
        "subprocess.",
        "popen",
        "powershell",
        "requests",
        "httpx",
        "socket",
        "selenium",
        "webbrowser",
        "sounddevice",
        "faster_whisper",
        "microphone(",
        "cookie_jar",
        "cookie_file",
        "profile_dir",
        "browser_profile",
        "meeting_url",
        ".sleep(",
        "sleep(",
        "timer(",
        "threading",
        "asyncio",
        "__import__",
        "eval(",
        "exec(",
    ):
        assert forbidden_fragment not in source_lower


def test_local_gate_d_smoke_evidence_bundle_output_privacy_guards() -> None:
    payload = build_local_gate_d_smoke_evidence_bundle()

    assert payload["live_delivery_performed"] is False
    assert payload["real_online_monitoring_performed"] is False
    assert payload["browser_automation_performed"] is False
    assert payload["audio_capture_performed"] is False
    assert payload["scheduler_execution_performed"] is False
    assert payload["gate_d_pass_claimed"] is False
    assert payload["product_promise_alpha_pass_claimed"] is False
    _assert_bundle_output_is_safe(payload)


def _install_fake_modules(
    monkeypatch: pytest.MonkeyPatch,
    seen: dict[str, object],
) -> dict[str, types.ModuleType]:
    modules: dict[str, types.ModuleType] = {}

    alert_module = types.ModuleType("async_scholar.alert_routing_smoke")

    def fake_build_local_alert_routing_smoke(event_type: str) -> dict[str, object]:
        seen["alert_event_type"] = event_type
        return {
            "decision": "delivered",
            "delivery_performed": True,
            "event_type_known": True,
            "requires_confirmation": True,
            "smoke_kind": "local_alert_routing",
            "status": "sent",
        }

    alert_module.build_local_alert_routing_smoke = fake_build_local_alert_routing_smoke
    modules["async_scholar.alert_routing_smoke"] = alert_module

    policy_module = types.ModuleType("async_scholar.policy_gate_smoke")

    def fake_build_local_policy_gate_smoke() -> dict[str, object]:
        seen["policy_called"] = True
        return {
            "declined_confirmation_blocks_authorization": True,
            "policy_gate_tests_status": "satisfactory",
            "smoke_kind": "local_policy_gate",
        }

    policy_module.build_local_policy_gate_smoke = fake_build_local_policy_gate_smoke
    modules["async_scholar.policy_gate_smoke"] = policy_module

    delivery_module = types.ModuleType("async_scholar.delivery_path_smoke")

    def fake_build_local_delivery_path_smoke() -> dict[str, object]:
        seen["delivery_called"] = True
        return {
            "delivery_path_evidence_status": "satisfactory",
            "live_delivery_performed": False,
            "network_performed": False,
            "smoke_kind": "local_delivery_path",
        }

    delivery_module.build_local_delivery_path_smoke = (
        fake_build_local_delivery_path_smoke
    )
    modules["async_scholar.delivery_path_smoke"] = delivery_module

    monitoring_module = types.ModuleType("async_scholar.monitoring_boundary_smoke")

    def fake_build_local_monitoring_boundary_smoke() -> dict[str, object]:
        seen["monitoring_called"] = True
        return {
            "audio_capture_performed": False,
            "browser_automation_performed": False,
            "monitoring_boundary_evidence_status": "satisfactory",
            "real_online_monitoring_performed": False,
            "smoke_kind": "local_monitoring_boundary",
        }

    monitoring_module.build_local_monitoring_boundary_smoke = (
        fake_build_local_monitoring_boundary_smoke
    )
    modules["async_scholar.monitoring_boundary_smoke"] = monitoring_module

    mic_module = types.ModuleType(
        "async_scholar.gate_d_mic_diagnostics_after_reboot_evidence"
    )

    def fake_build_local_gate_d_mic_diagnostics_after_reboot_evidence() -> dict[
        str, object
    ]:
        seen["mic_after_reboot_called"] = True
        return {
            "academic_answer_behavior_performed": False,
            "artifact_created": False,
            "artifact_read": False,
            "audio_capture_performed": False,
            "auth_profile_accessed": False,
            "autonomous_participation_performed": False,
            "browser_automation_performed": False,
            "cleanup_or_deletion_performed": False,
            "cookie_accessed": False,
            "dependency_change_performed": False,
            "device_name_exposed": False,
            "evidence_kind": "local_gate_d_mic_diagnostics_after_reboot_evidence",
            "export_performed": False,
            "file_io_performed": False,
            "gate_d_pass_claimed": False,
            "live_delivery_performed": False,
            "mic_diagnostics_after_reboot_status": "satisfactory",
            "network_performed": False,
            "private_data_read": False,
            "private_path_exposed": False,
            "product_promise_alpha_pass_claimed": False,
            "recording_performed": False,
            "scheduler_execution_performed": False,
            "signal_quality_claimed": False,
            "stt_performed": False,
            "transcript_text_exposed": False,
            "transcript_usefulness_claimed": False,
            "vad_performed": False,
        }

    mic_module.build_local_gate_d_mic_diagnostics_after_reboot_evidence = (
        fake_build_local_gate_d_mic_diagnostics_after_reboot_evidence
    )
    modules["async_scholar.gate_d_mic_diagnostics_after_reboot_evidence"] = mic_module

    signal_module = types.ModuleType("async_scholar.gate_d_signal_quality_evidence")

    def fake_build_local_gate_d_signal_quality_evidence() -> dict[str, object]:
        seen["signal_quality_called"] = True
        return {
            "academic_answer_behavior_performed": False,
            "artifact_created": False,
            "artifact_presence_checks_passed": True,
            "artifact_read": False,
            "audio_capture_performed": False,
            "auth_profile_accessed": False,
            "autonomous_participation_performed": False,
            "browser_automation_performed": False,
            "cleanup_or_deletion_performed": False,
            "cookie_accessed": False,
            "dependency_change_performed": False,
            "download_performed": False,
            "evidence_kind": "local_gate_d_public_open_signal_quality_evidence",
            "export_performed": False,
            "file_io_performed": False,
            "gate_d_pass_claimed": False,
            "hardware_or_device_enumeration_performed": False,
            "live_alert_delivery_claimed": False,
            "live_delivery_performed": False,
            "local_microphone_quality_claimed": False,
            "metadata_only_evidence_status": "documented",
            "model_loaded": False,
            "network_performed": False,
            "no_live_delivery_claim_status": "documented",
            "no_local_microphone_quality_claim_status": "documented",
            "no_real_online_monitoring_claim_status": "documented",
            "no_transcript_usefulness_claim_status": "documented",
            "private_data_read": False,
            "product_promise_alpha_pass_claimed": False,
            "public_open_duration_seconds": 68.370375,
            "public_open_elapsed_seconds": 4.515231,
            "public_open_evidence_status": "documented",
            "public_open_real_time_factor": 0.066041,
            "public_open_sample_rate_hz": 16000,
            "public_open_stt_segment_count": 16,
            "public_open_vad_segment_count": 32,
            "real_online_monitoring_claimed": False,
            "recording_performed": False,
            "scheduler_execution_performed": False,
            "signal_quality_evidence_status": "satisfactory",
            "stt_execution_performed": False,
            "subprocess_performed": False,
            "ticket_126_public_open_evidence_status": "documented",
            "transcript_usefulness_claimed": False,
            "vad_execution_performed": False,
        }

    signal_module.build_local_gate_d_signal_quality_evidence = (
        fake_build_local_gate_d_signal_quality_evidence
    )
    modules["async_scholar.gate_d_signal_quality_evidence"] = signal_module

    rollback_module = types.ModuleType("async_scholar.gate_d_rollback_plan_evidence")

    def fake_build_local_gate_d_rollback_plan_evidence() -> dict[str, object]:
        seen["rollback_plan_called"] = True
        return {
            "audio_capture_performed": False,
            "browser_automation_performed": False,
            "evidence_kind": "local_gate_d_rollback_plan_evidence",
            "external_platform_accessed": False,
            "gate_d_pass_claimed": False,
            "loopback_capture_performed": False,
            "network_performed": False,
            "product_promise_alpha_pass_claimed": False,
            "profile_state_accessed": False,
            "rollback_plan_for_loopback_playwright_spike_status": "satisfactory",
        }

    rollback_module.build_local_gate_d_rollback_plan_evidence = (
        fake_build_local_gate_d_rollback_plan_evidence
    )
    modules["async_scholar.gate_d_rollback_plan_evidence"] = rollback_module

    security_module = types.ModuleType("async_scholar.gate_d_security_review_evidence")

    def fake_build_local_gate_d_security_review_evidence() -> dict[str, object]:
        seen["security_review_called"] = True
        return {
            "academic_answer_behavior_performed": False,
            "audio_capture_performed": False,
            "auth_profile_accessed": False,
            "autonomous_participation_performed": False,
            "browser_automation_performed": False,
            "cleanup_or_deletion_performed": False,
            "cookie_accessed": False,
            "dependency_change_performed": False,
            "evidence_kind": "local_gate_d_security_review_evidence",
            "export_performed": False,
            "gate_d_pass_claimed": False,
            "live_delivery_performed": False,
            "loopback_capture_performed": False,
            "network_performed": False,
            "private_data_read": False,
            "product_promise_alpha_pass_claimed": False,
            "public_github_approval_claimed": False,
            "scheduler_execution_performed": False,
            "security_review_status": "satisfactory",
            "subprocess_performed": False,
            "timer_or_sleep_used": False,
        }

    security_module.build_local_gate_d_security_review_evidence = (
        fake_build_local_gate_d_security_review_evidence
    )
    modules["async_scholar.gate_d_security_review_evidence"] = security_module

    lifecycle_module = types.ModuleType(
        "async_scholar.gate_d_scheduler_lifecycle_evidence"
    )

    def fake_build_local_gate_d_scheduler_lifecycle_evidence() -> dict[str, object]:
        seen["scheduler_lifecycle_called"] = True
        return {
            "academic_answer_behavior_performed": False,
            "audio_capture_performed": False,
            "auth_profile_accessed": False,
            "autonomous_participation_performed": False,
            "background_loop_performed": False,
            "browser_automation_performed": False,
            "cleanup_or_deletion_performed": False,
            "cookie_accessed": False,
            "daemon_or_recurring_job_performed": False,
            "dependency_change_performed": False,
            "evidence_kind": "local_gate_d_scheduler_lifecycle_evidence",
            "export_performed": False,
            "file_io_performed": False,
            "gate_d_pass_claimed": False,
            "live_delivery_performed": False,
            "loopback_capture_performed": False,
            "network_performed": False,
            "private_data_read": False,
            "product_promise_alpha_pass_claimed": False,
            "scheduler_execution_performed": False,
            "scheduler_lifecycle_evidence_status": "satisfactory",
            "scheduler_lifecycle_smoke_performed": False,
            "scheduler_runtime_imported": False,
            "sqlite_accessed": False,
            "subprocess_performed": False,
            "timer_or_sleep_used": False,
        }

    lifecycle_module.build_local_gate_d_scheduler_lifecycle_evidence = (
        fake_build_local_gate_d_scheduler_lifecycle_evidence
    )
    modules["async_scholar.gate_d_scheduler_lifecycle_evidence"] = lifecycle_module

    readiness_module = types.ModuleType("async_scholar.gate_d_readiness")

    def fake_build_gate_d_readiness_report(**statuses: object) -> dict[str, object]:
        seen["readiness_statuses"] = statuses
        return _expected_readiness_report(statuses)

    def fake_build_gate_d_evidence_gap_summary(**statuses: object) -> dict[str, object]:
        seen["gap_statuses"] = statuses
        return _expected_gap_summary(statuses)

    readiness_module.build_gate_d_readiness_report = fake_build_gate_d_readiness_report
    readiness_module.build_gate_d_evidence_gap_summary = (
        fake_build_gate_d_evidence_gap_summary
    )
    modules["async_scholar.gate_d_readiness"] = readiness_module

    for module_name, module in modules.items():
        monkeypatch.setitem(sys.modules, module_name, module)
    return modules


def _fixed_status_inputs() -> dict[str, object]:
    return {
        "mic_diagnostics_after_reboot": "satisfactory",
        "alert_routing": "satisfactory",
        "security_review": "satisfactory",
        "policy_gate_tests": "satisfactory",
        "rollback_plan_for_loopback_playwright_spike": "satisfactory",
        "signal_quality_evidence": "satisfactory",
        "scheduler_lifecycle_evidence": "satisfactory",
        "delivery_path_evidence": "satisfactory",
        "monitoring_boundary_evidence": "satisfactory",
        "product_judgment_evidence": "missing",
    }


def _expected_readiness_report(statuses: dict[str, object]) -> dict[str, object]:
    return {
        "readiness_kind": "gate_d_readiness",
        "mic_diagnostics_after_reboot_status": statuses["mic_diagnostics_after_reboot"],
        "alert_routing_status": statuses["alert_routing"],
        "security_review_status": statuses["security_review"],
        "policy_gate_tests_status": statuses["policy_gate_tests"],
        "rollback_plan_for_loopback_playwright_spike_status": statuses[
            "rollback_plan_for_loopback_playwright_spike"
        ],
        "signal_quality_evidence_status": statuses["signal_quality_evidence"],
        "scheduler_lifecycle_evidence_status": statuses["scheduler_lifecycle_evidence"],
        "delivery_path_evidence_status": statuses["delivery_path_evidence"],
        "monitoring_boundary_evidence_status": statuses["monitoring_boundary_evidence"],
        "product_judgment_evidence_status": statuses["product_judgment_evidence"],
        "ready_for_gate_review": False,
        "decision": "blocked",
        "reason": "required_gate_d_readiness_evidence_missing_or_blocking",
    }


def _expected_gap_summary(statuses: dict[str, object]) -> dict[str, object]:
    return {
        "summary_kind": "gate_d_evidence_gap_summary",
        "mic_diagnostics_after_reboot_status": statuses["mic_diagnostics_after_reboot"],
        "alert_routing_status": statuses["alert_routing"],
        "security_review_status": statuses["security_review"],
        "policy_gate_tests_status": statuses["policy_gate_tests"],
        "rollback_plan_for_loopback_playwright_spike_status": statuses[
            "rollback_plan_for_loopback_playwright_spike"
        ],
        "signal_quality_evidence_status": statuses["signal_quality_evidence"],
        "scheduler_lifecycle_evidence_status": statuses["scheduler_lifecycle_evidence"],
        "delivery_path_evidence_status": statuses["delivery_path_evidence"],
        "monitoring_boundary_evidence_status": statuses["monitoring_boundary_evidence"],
        "product_judgment_evidence_status": statuses["product_judgment_evidence"],
        "missing_evidence": EXPECTED_GATE_D_LOCAL_EVIDENCE_BUNDLE["missing_evidence"],
        "missing_evidence_count": 1,
        "blocking_evidence": [],
        "blocking_evidence_count": 0,
        "satisfactory_evidence_count": 9,
        "decision": "gaps_present",
        "reason": "required_gate_d_evidence_gaps_present",
    }


def _assert_bundle_output_is_safe(payload: dict[str, object]) -> None:
    combined_output = json.dumps(payload, sort_keys=True).lower()
    for forbidden_fragment in (
        "title",
        "body",
        "provider",
        "http_status",
        "message",
        "request",
        "url",
        "command",
        "event_id",
        "session_id",
        "source_segment",
        "course_id",
        "meeting",
        "meet.example",
        "meet.google",
        "http://",
        "https://",
        "c:\\",
        "\\\\server",
        "/users",
        ".env",
        "token",
        "secret",
        "chat",
        "cookie",
        "auth-profile",
        "raw",
        "exception",
        "traceback",
        "powershell",
        "gate d passed",
        "product promise alpha passed",
        "online monitoring approved",
        "execution approved",
    ):
        assert forbidden_fragment not in combined_output


def _assert_error_is_sanitized(error_text: str) -> None:
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        ".env",
        "BOT_TOKEN",
        "secret",
        "token",
        "traceback",
        "import",
    ):
        assert forbidden_fragment not in error_text
