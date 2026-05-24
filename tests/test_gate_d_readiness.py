from __future__ import annotations

import inspect
import json

import pytest

from async_scholar.gate_d_readiness import (
    GATE_D_READINESS_ERROR,
    build_gate_d_readiness_report,
)

READINESS_KEYS = (
    "readiness_kind",
    "mic_diagnostics_after_reboot_status",
    "alert_routing_status",
    "security_review_status",
    "policy_gate_tests_status",
    "rollback_plan_for_loopback_playwright_spike_status",
    "ready_for_gate_review",
    "decision",
    "reason",
)


def _build(
    *,
    mic_diagnostics_after_reboot: object = "satisfactory",
    alert_routing: object = "satisfactory",
    security_review: object = "satisfactory",
    policy_gate_tests: object = "satisfactory",
    rollback_plan_for_loopback_playwright_spike: object = "satisfactory",
) -> dict[str, object]:
    return build_gate_d_readiness_report(
        mic_diagnostics_after_reboot=mic_diagnostics_after_reboot,
        alert_routing=alert_routing,
        security_review=security_review,
        policy_gate_tests=policy_gate_tests,
        rollback_plan_for_loopback_playwright_spike=(
            rollback_plan_for_loopback_playwright_spike
        ),
    )


def _assert_readiness_error(**overrides: object) -> None:
    with pytest.raises(ValueError) as exc_info:
        _build(**overrides)
    assert str(exc_info.value) == GATE_D_READINESS_ERROR


def _assert_payload_is_safe(*payloads: object) -> None:
    combined_output = json.dumps(payloads, sort_keys=True).lower()
    for forbidden_fragment in (
        "gate d passed",
        "product promise alpha passed",
        "online monitoring approved",
        "execution approved",
        "user approval",
        "transcript",
        "recording",
        "audio",
        "browser",
        "cookie",
        "auth",
        "profile",
        "meeting url",
        "meet.google",
        "token",
        "secret",
        "path",
        "sqlite",
        "checkpoint",
        "debug",
        "data/session",
        "traceback",
    ):
        assert forbidden_fragment not in combined_output


def test_gate_d_readiness_reports_ready_when_all_statuses_pass() -> None:
    result = _build()

    assert type(result) is dict
    assert tuple(result) == READINESS_KEYS
    assert result == {
        "readiness_kind": "gate_d_readiness",
        "mic_diagnostics_after_reboot_status": "satisfactory",
        "alert_routing_status": "satisfactory",
        "security_review_status": "satisfactory",
        "policy_gate_tests_status": "satisfactory",
        "rollback_plan_for_loopback_playwright_spike_status": "satisfactory",
        "ready_for_gate_review": True,
        "decision": "ready_for_gate_review",
        "reason": "all_required_gate_d_readiness_evidence_satisfactory",
    }
    _assert_payload_is_safe(result)


@pytest.mark.parametrize(
    ("field_name", "expected_status"),
    (
        ("mic_diagnostics_after_reboot", "missing"),
        ("alert_routing", "blocking"),
        ("security_review", "missing"),
        ("policy_gate_tests", "blocking"),
        ("rollback_plan_for_loopback_playwright_spike", "missing"),
    ),
)
def test_gate_d_readiness_blocks_each_missing_or_blocking_category(
    field_name: str,
    expected_status: str,
) -> None:
    result = _build(**{field_name: expected_status})

    assert result[f"{field_name}_status"] == expected_status
    assert result["ready_for_gate_review"] is False
    assert result["decision"] == "blocked"
    assert result["reason"] == "required_gate_d_readiness_evidence_missing_or_blocking"
    _assert_payload_is_safe(result)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("mic_diagnostics_after_reboot", ""),
        ("alert_routing", " yes "),
        ("security_review", "passed"),
        ("policy_gate_tests", True),
        ("rollback_plan_for_loopback_playwright_spike", ["satisfactory"]),
    ),
)
def test_gate_d_readiness_rejects_malformed_values(
    field_name: str,
    bad_value: object,
) -> None:
    _assert_readiness_error(**{field_name: bad_value})


def test_gate_d_readiness_source_guards_forbidden_surfaces() -> None:
    import async_scholar.gate_d_readiness as gate_d_readiness

    source = inspect.getsource(gate_d_readiness)

    assert "build_gate_d_readiness_report" in source
    for forbidden_fragment in (
        "Path",
        "open(",
        "read_text",
        "write_text",
        "sqlite",
        "jsonl",
        "transcript",
        "recording",
        "async_playwright",
        "chromium",
        "selenium",
        "webbrowser",
        "requests",
        "httpx",
        "sounddevice",
        "faster_whisper",
        "vad",
        "stt",
        "subprocess",
        "sleep",
        "Timer(",
        "threading",
        "asyncio",
        "telegram",
        "desktop",
        "notify",
        "delete",
        "archive_export",
        "write_stored_session_window",
        "gate d passed",
        "product promise alpha passed",
    ):
        assert forbidden_fragment not in source
