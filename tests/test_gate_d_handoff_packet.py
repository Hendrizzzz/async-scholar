from __future__ import annotations

import ast
import builtins
import inspect
import json
from pathlib import Path

import pytest

from async_scholar.gate_d_handoff_packet import (
    GATE_D_HANDOFF_PACKET_ERROR,
    build_local_gate_d_handoff_packet,
)
from async_scholar.gate_d_local_evidence_bundle import (
    build_local_gate_d_smoke_evidence_bundle,
)
from async_scholar.gate_d_product_judgment_packet import (
    build_local_gate_d_product_judgment_packet,
)

EXPECTED_GATE_D_HANDOFF_PACKET = {
    "packet_kind": "local_gate_d_handoff_packet",
    "handoff_packet_status": "ready_for_manual_review",
    "handoff_packet_scope_status": "metadata_only",
    "local_gate_d_bundle_status": "blocked",
    "product_judgment_packet_status": "ready_for_manual_review",
    "manual_product_judgment_required": True,
    "manual_product_judgment_recorded": False,
    "review_requires_human_product_judgment": True,
    "review_can_be_completed_by_ai": False,
    "ready_for_gate_review": False,
    "readiness_decision": "blocked",
    "readiness_reason": "required_gate_d_readiness_evidence_missing_or_blocking",
    "gap_decision": "gaps_present",
    "gap_reason": "required_gate_d_evidence_gaps_present",
    "missing_evidence": [],
    "missing_evidence_count": 0,
    "blocking_evidence": [
        "product_judgment_evidence",
    ],
    "blocking_evidence_count": 1,
    "satisfactory_evidence_count": 9,
    "product_judgment_evidence_status": "blocking",
    "gate_d_pass_claimed": False,
    "product_promise_alpha_pass_claimed": False,
    "real_online_monitoring_performed": False,
    "browser_automation_performed": False,
    "auth_profile_accessed": False,
    "cookie_accessed": False,
    "private_data_read": False,
    "audio_capture_performed": False,
    "recording_performed": False,
    "vad_execution_performed": False,
    "stt_execution_performed": False,
    "model_loaded": False,
    "scheduler_execution_performed": False,
    "live_delivery_performed": False,
    "cleanup_or_deletion_performed": False,
    "export_performed": False,
    "dependency_change_performed": False,
    "online_monitoring_approved": False,
    "transcript_usefulness_claimed": False,
    "local_microphone_quality_claimed": False,
    "live_alert_delivery_claimed": False,
    "browser_readiness_claimed": False,
    "scheduler_execution_claimed": False,
    "participation_approval_claimed": False,
    "autonomous_participation_performed": False,
    "academic_answer_behavior_performed": False,
}


def test_local_gate_d_handoff_packet_returns_exact_allowlist() -> None:
    payload = build_local_gate_d_handoff_packet()

    assert type(payload) is dict
    assert payload == EXPECTED_GATE_D_HANDOFF_PACKET
    assert list(payload) == list(EXPECTED_GATE_D_HANDOFF_PACKET)
    assert json.loads(json.dumps(payload)) == payload
    _assert_handoff_packet_output_is_safe(payload)


def test_local_gate_d_handoff_packet_accepts_no_input() -> None:
    signature = inspect.signature(build_local_gate_d_handoff_packet)

    assert signature.parameters == {}


def test_local_gate_d_handoff_packet_composes_expected_delegates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, bool] = {}

    def fake_bundle() -> dict[str, object]:
        seen["bundle"] = True
        return build_local_gate_d_smoke_evidence_bundle()

    def fake_product_packet() -> dict[str, object]:
        seen["product_packet"] = True
        return build_local_gate_d_product_judgment_packet()

    monkeypatch.setattr(
        "async_scholar.gate_d_handoff_packet._build_bundle_payload",
        fake_bundle,
    )
    monkeypatch.setattr(
        "async_scholar.gate_d_handoff_packet._build_product_judgment_packet_payload",
        fake_product_packet,
    )

    payload = build_local_gate_d_handoff_packet()

    assert seen == {"bundle": True, "product_packet": True}
    assert payload == EXPECTED_GATE_D_HANDOFF_PACKET


def test_local_gate_d_handoff_packet_sanitizes_malformed_bundle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_bundle() -> dict[str, object]:
        return {"private": "C:/Users/student/token-secret-auth-profile"}

    monkeypatch.setattr(
        "async_scholar.gate_d_handoff_packet._build_bundle_payload",
        fake_bundle,
    )

    with pytest.raises(ValueError) as exc_info:
        build_local_gate_d_handoff_packet()

    assert str(exc_info.value) == GATE_D_HANDOFF_PACKET_ERROR
    assert exc_info.value.__cause__ is None
    _assert_error_is_sanitized(str(exc_info.value))


def test_local_gate_d_handoff_packet_sanitizes_malformed_product_packet(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_product_packet() -> dict[str, object]:
        return {"private": "C:/Users/student/token-secret-auth-profile"}

    monkeypatch.setattr(
        "async_scholar.gate_d_handoff_packet._build_product_judgment_packet_payload",
        fake_product_packet,
    )

    with pytest.raises(ValueError) as exc_info:
        build_local_gate_d_handoff_packet()

    assert str(exc_info.value) == GATE_D_HANDOFF_PACKET_ERROR
    assert exc_info.value.__cause__ is None
    _assert_error_is_sanitized(str(exc_info.value))


def test_local_gate_d_handoff_packet_sanitizes_delegate_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_product_packet() -> dict[str, object]:
        raise RuntimeError("C:\\Users\\student\\.env BOT_TOKEN=secret traceback")

    monkeypatch.setattr(
        "async_scholar.gate_d_handoff_packet._build_product_judgment_packet_payload",
        fake_product_packet,
    )

    with pytest.raises(ValueError) as exc_info:
        build_local_gate_d_handoff_packet()

    assert str(exc_info.value) == GATE_D_HANDOFF_PACKET_ERROR
    assert exc_info.value.__cause__ is None
    _assert_error_is_sanitized(str(exc_info.value))


def test_local_gate_d_handoff_packet_isolated_from_caller_mutation() -> None:
    payload = build_local_gate_d_handoff_packet()
    missing_evidence = payload["missing_evidence"]
    blocking_evidence = payload["blocking_evidence"]

    assert isinstance(missing_evidence, list)
    assert isinstance(blocking_evidence, list)

    missing_evidence.append("private_meeting_data")
    blocking_evidence.append("C:/Users/student/token-secret-auth-profile")

    next_payload = build_local_gate_d_handoff_packet()

    assert next_payload == EXPECTED_GATE_D_HANDOFF_PACKET
    _assert_handoff_packet_output_is_safe(next_payload)


def test_local_gate_d_handoff_packet_output_privacy_guards() -> None:
    payload = build_local_gate_d_handoff_packet()

    assert payload["manual_product_judgment_required"] is True
    assert payload["manual_product_judgment_recorded"] is False
    assert payload["review_requires_human_product_judgment"] is True
    assert payload["review_can_be_completed_by_ai"] is False
    assert payload["ready_for_gate_review"] is False
    assert payload["missing_evidence"] == []
    assert payload["blocking_evidence"] == [
        "product_judgment_evidence",
    ]
    assert payload["product_judgment_evidence_status"] == "blocking"
    assert payload["gate_d_pass_claimed"] is False
    assert payload["product_promise_alpha_pass_claimed"] is False
    assert payload["real_online_monitoring_performed"] is False
    assert payload["browser_automation_performed"] is False
    assert payload["auth_profile_accessed"] is False
    assert payload["cookie_accessed"] is False
    assert payload["private_data_read"] is False
    assert payload["audio_capture_performed"] is False
    assert payload["recording_performed"] is False
    assert payload["vad_execution_performed"] is False
    assert payload["stt_execution_performed"] is False
    assert payload["model_loaded"] is False
    assert payload["scheduler_execution_performed"] is False
    assert payload["live_delivery_performed"] is False
    assert payload["cleanup_or_deletion_performed"] is False
    assert payload["export_performed"] is False
    assert payload["dependency_change_performed"] is False
    assert payload["online_monitoring_approved"] is False
    assert payload["autonomous_participation_performed"] is False
    assert payload["academic_answer_behavior_performed"] is False
    _assert_handoff_packet_output_is_safe(payload)


def test_local_gate_d_handoff_packet_source_guards() -> None:
    source = Path("src/async_scholar/gate_d_handoff_packet.py").read_text(
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

    assert imported_names == {
        "__future__",
        "typing",
        "async_scholar.gate_d_local_evidence_bundle",
        "async_scholar.gate_d_product_judgment_packet",
    }

    assert "build_local_gate_d_smoke_evidence_bundle" in source
    assert "build_local_gate_d_product_judgment_packet" in source
    assert "rollback_plan_for_loopback_playwright_spike_status" in source
    for forbidden_fragment in (
        "pathlib",
        "sqlite3",
        "open(",
        "read_text",
        "write_text",
        "mkdir",
        "unlink",
        "remove(",
        "rmdir",
        "rmtree",
        "subprocess.",
        "popen",
        "powershell",
        "socket",
        "urlopen(",
        "requests",
        "httpx",
        "import playwright",
        "selenium",
        "webbrowser",
        "sounddevice",
        "faster_whisper",
        "whisper",
        "torch",
        "microphone(",
        "system audio",
        "loopback_capture",
        "vad.",
        "stt.",
        "model_path",
        "record(",
        "recording.",
        "wave",
        "wav",
        "schedule_store",
        "scheduled_start",
        "session_window",
        "scheduler.",
        "archive_delete",
        "archive_export",
        "dispatch",
        "telegram",
        "desktop",
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


def test_local_gate_d_handoff_packet_does_not_touch_file_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_open(*args: object, **kwargs: object) -> object:
        raise AssertionError("production helper must not open files")

    monkeypatch.setattr(builtins, "open", fail_open)

    assert build_local_gate_d_handoff_packet() == EXPECTED_GATE_D_HANDOFF_PACKET


def _assert_handoff_packet_output_is_safe(payload: dict[str, object]) -> None:
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
        "chat",
        "raw",
        "exception",
        "traceback",
        "powershell",
        "playwright",
        "selenium",
        "sounddevice",
        "faster_whisper",
        "microphone name",
        "device name",
        "gate d passed",
        "product promise alpha passed",
        "online monitoring approved",
        "execution approved",
        "transcript text",
        "artifact path",
    ):
        assert forbidden_fragment not in combined_output


def _assert_error_is_sanitized(error_text: str) -> None:
    for forbidden_fragment in (
        "C:\\Users",
        "C:/Users",
        "student",
        ".env",
        "BOT_TOKEN",
        "secret",
        "token",
        "auth",
        "profile",
        "private",
        "traceback",
    ):
        assert forbidden_fragment not in error_text
