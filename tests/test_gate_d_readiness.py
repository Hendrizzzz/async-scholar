from __future__ import annotations

import inspect
import json

import pytest

from async_scholar.gate_d_readiness import (
    GATE_D_EVIDENCE_GAP_SUMMARY_ERROR,
    GATE_D_READINESS_ERROR,
    build_gate_d_evidence_gap_summary,
    build_gate_d_readiness_report,
)

READINESS_KEYS = (
    "readiness_kind",
    "mic_diagnostics_after_reboot_status",
    "alert_routing_status",
    "security_review_status",
    "policy_gate_tests_status",
    "rollback_plan_for_loopback_playwright_spike_status",
    "signal_quality_evidence_status",
    "scheduler_lifecycle_evidence_status",
    "delivery_path_evidence_status",
    "monitoring_boundary_evidence_status",
    "product_judgment_evidence_status",
    "ready_for_gate_review",
    "decision",
    "reason",
)
EVIDENCE_GAP_SUMMARY_KEYS = (
    "summary_kind",
    "mic_diagnostics_after_reboot_status",
    "alert_routing_status",
    "security_review_status",
    "policy_gate_tests_status",
    "rollback_plan_for_loopback_playwright_spike_status",
    "signal_quality_evidence_status",
    "scheduler_lifecycle_evidence_status",
    "delivery_path_evidence_status",
    "monitoring_boundary_evidence_status",
    "product_judgment_evidence_status",
    "missing_evidence",
    "missing_evidence_count",
    "blocking_evidence",
    "blocking_evidence_count",
    "satisfactory_evidence_count",
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
    signal_quality_evidence: object = "missing",
    scheduler_lifecycle_evidence: object = "missing",
    delivery_path_evidence: object = "missing",
    monitoring_boundary_evidence: object = "missing",
    product_judgment_evidence: object = "missing",
) -> dict[str, object]:
    return build_gate_d_readiness_report(
        mic_diagnostics_after_reboot=mic_diagnostics_after_reboot,
        alert_routing=alert_routing,
        security_review=security_review,
        policy_gate_tests=policy_gate_tests,
        rollback_plan_for_loopback_playwright_spike=(
            rollback_plan_for_loopback_playwright_spike
        ),
        signal_quality_evidence=signal_quality_evidence,
        scheduler_lifecycle_evidence=scheduler_lifecycle_evidence,
        delivery_path_evidence=delivery_path_evidence,
        monitoring_boundary_evidence=monitoring_boundary_evidence,
        product_judgment_evidence=product_judgment_evidence,
    )


def _build_gap(
    *,
    mic_diagnostics_after_reboot: object = "satisfactory",
    alert_routing: object = "satisfactory",
    security_review: object = "satisfactory",
    policy_gate_tests: object = "satisfactory",
    rollback_plan_for_loopback_playwright_spike: object = "satisfactory",
    signal_quality_evidence: object = "missing",
    scheduler_lifecycle_evidence: object = "missing",
    delivery_path_evidence: object = "missing",
    monitoring_boundary_evidence: object = "missing",
    product_judgment_evidence: object = "missing",
) -> dict[str, object]:
    return build_gate_d_evidence_gap_summary(
        mic_diagnostics_after_reboot=mic_diagnostics_after_reboot,
        alert_routing=alert_routing,
        security_review=security_review,
        policy_gate_tests=policy_gate_tests,
        rollback_plan_for_loopback_playwright_spike=(
            rollback_plan_for_loopback_playwright_spike
        ),
        signal_quality_evidence=signal_quality_evidence,
        scheduler_lifecycle_evidence=scheduler_lifecycle_evidence,
        delivery_path_evidence=delivery_path_evidence,
        monitoring_boundary_evidence=monitoring_boundary_evidence,
        product_judgment_evidence=product_judgment_evidence,
    )


def _all_ten_satisfactory() -> dict[str, object]:
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
        "product_judgment_evidence": "satisfactory",
    }


def _assert_readiness_error(**overrides: object) -> None:
    with pytest.raises(ValueError) as exc_info:
        _build(**overrides)
    assert str(exc_info.value) == GATE_D_READINESS_ERROR


def _assert_gap_summary_error(**overrides: object) -> None:
    with pytest.raises(ValueError) as exc_info:
        _build_gap(**overrides)
    assert str(exc_info.value) == GATE_D_EVIDENCE_GAP_SUMMARY_ERROR


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
        "sqlite",
        "checkpoint",
        "debug",
        "data/session",
        "traceback",
    ):
        assert forbidden_fragment not in combined_output


def test_gate_d_readiness_reports_ready_when_all_statuses_pass() -> None:
    result = _build(**_all_ten_satisfactory())

    assert type(result) is dict
    assert tuple(result) == READINESS_KEYS
    assert result == {
        "readiness_kind": "gate_d_readiness",
        "mic_diagnostics_after_reboot_status": "satisfactory",
        "alert_routing_status": "satisfactory",
        "security_review_status": "satisfactory",
        "policy_gate_tests_status": "satisfactory",
        "rollback_plan_for_loopback_playwright_spike_status": "satisfactory",
        "signal_quality_evidence_status": "satisfactory",
        "scheduler_lifecycle_evidence_status": "satisfactory",
        "delivery_path_evidence_status": "satisfactory",
        "monitoring_boundary_evidence_status": "satisfactory",
        "product_judgment_evidence_status": "satisfactory",
        "ready_for_gate_review": True,
        "decision": "ready_for_gate_review",
        "reason": "all_required_gate_d_readiness_evidence_satisfactory",
    }
    _assert_payload_is_safe(result)


def test_gate_d_readiness_defaults_new_categories_to_missing() -> None:
    result = _build()

    assert result["signal_quality_evidence_status"] == "missing"
    assert result["scheduler_lifecycle_evidence_status"] == "missing"
    assert result["delivery_path_evidence_status"] == "missing"
    assert result["monitoring_boundary_evidence_status"] == "missing"
    assert result["product_judgment_evidence_status"] == "missing"
    assert result["ready_for_gate_review"] is False
    assert result["decision"] == "blocked"
    _assert_payload_is_safe(result)


@pytest.mark.parametrize(
    ("field_name", "expected_status"),
    (
        ("mic_diagnostics_after_reboot", "missing"),
        ("alert_routing", "blocking"),
        ("security_review", "missing"),
        ("policy_gate_tests", "blocking"),
        ("rollback_plan_for_loopback_playwright_spike", "missing"),
        ("signal_quality_evidence", "blocking"),
        ("scheduler_lifecycle_evidence", "missing"),
        ("delivery_path_evidence", "blocking"),
        ("monitoring_boundary_evidence", "missing"),
        ("product_judgment_evidence", "blocking"),
    ),
)
def test_gate_d_readiness_blocks_each_missing_or_blocking_category(
    field_name: str,
    expected_status: str,
) -> None:
    statuses = _all_ten_satisfactory()
    statuses[field_name] = expected_status

    result = _build(**statuses)

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
        ("signal_quality_evidence", "C:\\Users\\student\\token-secret-auth-profile"),
        ("scheduler_lifecycle_evidence", "satisfactory\n"),
        ("delivery_path_evidence", "https://provider.example/target"),
        ("monitoring_boundary_evidence", "../browser-profile"),
        ("product_judgment_evidence", "product promise alpha passed"),
    ),
)
def test_gate_d_readiness_rejects_malformed_values(
    field_name: str,
    bad_value: object,
) -> None:
    _assert_readiness_error(**{field_name: bad_value})


def test_gate_d_evidence_gap_summary_reports_no_gaps_when_all_statuses_pass() -> None:
    result = _build_gap(**_all_ten_satisfactory())

    assert type(result) is dict
    assert tuple(result) == EVIDENCE_GAP_SUMMARY_KEYS
    assert result == {
        "summary_kind": "gate_d_evidence_gap_summary",
        "mic_diagnostics_after_reboot_status": "satisfactory",
        "alert_routing_status": "satisfactory",
        "security_review_status": "satisfactory",
        "policy_gate_tests_status": "satisfactory",
        "rollback_plan_for_loopback_playwright_spike_status": "satisfactory",
        "signal_quality_evidence_status": "satisfactory",
        "scheduler_lifecycle_evidence_status": "satisfactory",
        "delivery_path_evidence_status": "satisfactory",
        "monitoring_boundary_evidence_status": "satisfactory",
        "product_judgment_evidence_status": "satisfactory",
        "missing_evidence": [],
        "missing_evidence_count": 0,
        "blocking_evidence": [],
        "blocking_evidence_count": 0,
        "satisfactory_evidence_count": 10,
        "decision": "no_gaps",
        "reason": "all_gate_d_evidence_categories_satisfactory",
    }
    _assert_payload_is_safe(result)


def test_gate_d_evidence_gap_summary_defaults_new_categories_to_missing() -> None:
    result = _build_gap()

    assert result["missing_evidence"] == [
        "signal_quality_evidence",
        "scheduler_lifecycle_evidence",
        "delivery_path_evidence",
        "monitoring_boundary_evidence",
        "product_judgment_evidence",
    ]
    assert result["missing_evidence_count"] == 5
    assert result["blocking_evidence"] == []
    assert result["blocking_evidence_count"] == 0
    assert result["satisfactory_evidence_count"] == 5
    assert result["decision"] == "gaps_present"
    _assert_payload_is_safe(result)


@pytest.mark.parametrize(
    ("field_name", "category"),
    (
        ("mic_diagnostics_after_reboot", "mic_diagnostics_after_reboot"),
        ("alert_routing", "alert_routing"),
        ("security_review", "security_review"),
        ("policy_gate_tests", "policy_gate_tests"),
        (
            "rollback_plan_for_loopback_playwright_spike",
            "rollback_plan_for_loopback_playwright_spike",
        ),
        ("signal_quality_evidence", "signal_quality_evidence"),
        ("scheduler_lifecycle_evidence", "scheduler_lifecycle_evidence"),
        ("delivery_path_evidence", "delivery_path_evidence"),
        ("monitoring_boundary_evidence", "monitoring_boundary_evidence"),
        ("product_judgment_evidence", "product_judgment_evidence"),
    ),
)
@pytest.mark.parametrize("status", ("missing", "blocking"))
def test_gate_d_evidence_gap_summary_lists_each_gap_category(
    field_name: str,
    category: str,
    status: str,
) -> None:
    statuses = _all_ten_satisfactory()
    statuses[field_name] = status

    result = _build_gap(**statuses)

    assert result[f"{field_name}_status"] == status
    assert result["decision"] == "gaps_present"
    assert result["reason"] == "required_gate_d_evidence_gaps_present"
    assert result["satisfactory_evidence_count"] == 9
    if status == "missing":
        assert result["missing_evidence"] == [category]
        assert result["missing_evidence_count"] == 1
        assert result["blocking_evidence"] == []
        assert result["blocking_evidence_count"] == 0
    else:
        assert result["missing_evidence"] == []
        assert result["missing_evidence_count"] == 0
        assert result["blocking_evidence"] == [category]
        assert result["blocking_evidence_count"] == 1
    _assert_payload_is_safe(result)


def test_gate_d_evidence_gap_summary_distinguishes_mixed_gaps() -> None:
    statuses = _all_ten_satisfactory()
    statuses.update(
        mic_diagnostics_after_reboot="missing",
        security_review="blocking",
        rollback_plan_for_loopback_playwright_spike="missing",
        scheduler_lifecycle_evidence="blocking",
        product_judgment_evidence="missing",
    )
    result = _build_gap(**statuses)

    assert result["missing_evidence"] == [
        "mic_diagnostics_after_reboot",
        "rollback_plan_for_loopback_playwright_spike",
        "product_judgment_evidence",
    ]
    assert result["missing_evidence_count"] == 3
    assert result["blocking_evidence"] == [
        "security_review",
        "scheduler_lifecycle_evidence",
    ]
    assert result["blocking_evidence_count"] == 2
    assert result["satisfactory_evidence_count"] == 5
    assert result["decision"] == "gaps_present"
    _assert_payload_is_safe(result)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("mic_diagnostics_after_reboot", ""),
        ("alert_routing", " yes "),
        ("security_review", "passed"),
        ("policy_gate_tests", True),
        ("rollback_plan_for_loopback_playwright_spike", ["satisfactory"]),
        ("signal_quality_evidence", "C:\\Users\\student\\token-secret-auth-profile"),
        ("scheduler_lifecycle_evidence", "satisfactory\n"),
        ("delivery_path_evidence", "https://provider.example/target"),
        ("monitoring_boundary_evidence", "../browser-profile"),
        ("product_judgment_evidence", "product promise alpha passed"),
    ),
)
def test_gate_d_evidence_gap_summary_rejects_malformed_values(
    field_name: str,
    bad_value: object,
) -> None:
    _assert_gap_summary_error(**{field_name: bad_value})


def test_gate_d_readiness_source_guards_forbidden_surfaces() -> None:
    import async_scholar.gate_d_readiness as gate_d_readiness

    source = inspect.getsource(gate_d_readiness)

    assert "build_gate_d_readiness_report" in source
    assert "build_gate_d_evidence_gap_summary" in source
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
