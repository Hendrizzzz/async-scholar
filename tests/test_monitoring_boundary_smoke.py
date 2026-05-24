from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from async_scholar import monitoring_boundary_smoke as smoke

EXPECTED_MONITORING_BOUNDARY_SMOKE = {
    "smoke_kind": "local_monitoring_boundary",
    "synthetic_fixture_status": "built",
    "html_inspection_status": "inspected",
    "session_history_status": "summarized",
    "monitoring_boundary_evidence_status": "satisfactory",
    "real_online_monitoring_performed": False,
    "browser_automation_performed": False,
    "auth_profile_accessed": False,
    "network_performed": False,
    "audio_capture_performed": False,
    "gate_d_pass_claimed": False,
    "product_promise_alpha_pass_claimed": False,
}


def test_monitoring_boundary_smoke_returns_exact_allowlisted_output() -> None:
    payload = smoke.build_local_monitoring_boundary_smoke()

    assert payload == EXPECTED_MONITORING_BOUNDARY_SMOKE
    assert set(payload) == set(EXPECTED_MONITORING_BOUNDARY_SMOKE)


def test_monitoring_boundary_smoke_accepts_no_input() -> None:
    signature = inspect.signature(smoke.build_local_monitoring_boundary_smoke)

    assert signature.parameters == {}


def test_monitoring_boundary_smoke_collapses_malformed_delegated_behavior(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_inspect_fake_meeting_session_html(html_text: str) -> object:
        raise ValueError(
            "C:\\Users\\student\\token-secret-auth-profile raw html selector"
        )

    monkeypatch.setattr(
        smoke,
        "inspect_fake_meeting_session_html",
        fake_inspect_fake_meeting_session_html,
    )

    with pytest.raises(RuntimeError) as error:
        smoke.build_local_monitoring_boundary_smoke()

    assert str(error.value) == "monitoring boundary smoke could not be built"
    for forbidden_fragment in (
        "C:\\Users",
        "student",
        "token",
        "secret",
        "auth",
        "profile",
        "raw html",
        "selector",
    ):
        assert forbidden_fragment not in str(error.value)


def test_monitoring_boundary_smoke_uses_only_safe_fake_meeting_boundaries() -> None:
    source = inspect.getsource(smoke.build_local_monitoring_boundary_smoke)

    assert "build_fake_meeting_fixture" in source
    assert "to_html_document" in source
    assert "inspect_fake_meeting_session_html" in source
    assert "build_fake_meeting_session_history_summary" in source
    assert "build_fake_meeting_session_awareness_event" not in source


def test_monitoring_boundary_smoke_source_avoids_forbidden_surfaces() -> None:
    source = Path("src/async_scholar/monitoring_boundary_smoke.py").read_text(
        encoding="utf-8"
    )

    for forbidden_fragment in (
        "playwright",
        "selenium",
        "webdriver",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "webbrowser",
        "sounddevice",
        "pyaudio",
        "microphone",
        "camera",
        "cookie_file",
        "auth_state",
        "profile_dir",
        "browser_profile",
        "token",
        "credential",
        "meeting_url",
        "notify",
        "dispatch",
        "scheduler",
        "delete",
        "export",
        "academic_answer",
        "participation",
        ".open(",
        "read_text",
        "write_text",
        "mkdir",
        "unlink",
        "remove(",
        "rmdir",
        "rmtree",
        "sleep",
        "Timer(",
        "threading",
        "asyncio",
    ):
        assert forbidden_fragment not in source.lower()


def test_monitoring_boundary_smoke_output_omits_private_payload_surfaces() -> None:
    combined_output = repr(smoke.build_local_monitoring_boundary_smoke()).lower()

    for forbidden_fragment in (
        "fixture_id",
        "title",
        "participant",
        "synthetic instructor",
        "synthetic learner",
        "raw_html",
        "<html",
        "data-async",
        "selector",
        "message",
        "event",
        "source",
        "provider",
        "url",
        "path",
        "credential",
        "token",
        "cookie",
        "auth-profile",
        "meeting",
        "transcript",
        "audio data",
        "exception",
        "traceback",
    ):
        assert forbidden_fragment not in combined_output
