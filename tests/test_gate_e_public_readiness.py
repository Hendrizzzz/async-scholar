from __future__ import annotations

import ast
import builtins
import inspect
import json
from pathlib import Path

import pytest

from async_scholar.gate_e_public_readiness import (
    GATE_E_PUBLIC_READINESS_ERROR,
    build_gate_e_public_readiness_preflight,
)

EXPECTED_GATE_E_PUBLIC_READINESS_DEFAULT = {
    "preflight_kind": "gate_e_public_readiness",
    "mode": "dry_run_report_only",
    "gate_d_scope_status": "narrow_local_fixture_to_reviewer_pass_recorded",
    "gate_e_status": "human_approval_required",
    "decision": "blocked",
    "reason": "required_gate_e_preflight_items_missing_or_blocking",
    "ready_for_human_gate_e_review": False,
    "human_gate_e_approval_required": True,
    "human_gate_e_approval_status": "missing",
    "public_docs_boundary_review_status": "missing",
    "secret_and_private_data_review_status": "missing",
    "generated_artifact_review_status": "missing",
    "ignored_file_review_status": "missing",
    "push_merge_release_plan_review_status": "missing",
    "missing_review_items": [
        "public_docs_boundary_review",
        "secret_and_private_data_review",
        "generated_artifact_review",
        "ignored_file_review",
        "push_merge_release_plan_review",
        "human_gate_e_approval",
    ],
    "missing_review_item_count": 6,
    "blocking_review_items": [],
    "blocking_review_item_count": 0,
    "satisfactory_review_item_count": 0,
    "public_release_approved": False,
    "push_approved": False,
    "merge_approved": False,
    "public_github_approval_claimed": False,
    "publish_performed": False,
    "push_performed": False,
    "merge_performed": False,
    "browser_or_server_launched": False,
    "browser_automation_performed": False,
    "playwright_or_in_app_browser_performed": False,
    "screenshot_trace_video_download_performed": False,
    "auth_profile_accessed": False,
    "cookie_accessed": False,
    "private_data_read": False,
    "audio_capture_performed": False,
    "hardware_access_performed": False,
    "loopback_capture_performed": False,
    "live_delivery_performed": False,
    "scheduler_background_execution_performed": False,
    "deletion_or_export_performed": False,
    "dependency_change_performed": False,
    "autonomous_participation_performed": False,
    "academic_answer_behavior_performed": False,
    "product_promise_alpha_scope_broadened": False,
}


def test_gate_e_public_readiness_default_fails_closed_with_exact_output() -> None:
    payload = build_gate_e_public_readiness_preflight()

    assert type(payload) is dict
    assert payload == EXPECTED_GATE_E_PUBLIC_READINESS_DEFAULT
    assert list(payload) == list(EXPECTED_GATE_E_PUBLIC_READINESS_DEFAULT)
    assert json.loads(json.dumps(payload)) == payload
    _assert_gate_e_public_readiness_output_is_safe(payload)


def test_gate_e_public_readiness_accepts_only_keyword_review_statuses() -> None:
    signature = inspect.signature(build_gate_e_public_readiness_preflight)

    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )


def test_gate_e_public_readiness_pass_like_inputs_still_require_human_gate() -> None:
    payload = build_gate_e_public_readiness_preflight(
        public_docs_boundary_review_status="satisfactory",
        secret_and_private_data_review_status="satisfactory",
        generated_artifact_review_status="satisfactory",
        ignored_file_review_status="satisfactory",
        push_merge_release_plan_review_status="satisfactory",
    )

    assert payload["decision"] == "blocked"
    assert payload["reason"] == "human_gate_e_approval_required"
    assert payload["ready_for_human_gate_e_review"] is True
    assert payload["human_gate_e_approval_required"] is True
    assert payload["human_gate_e_approval_status"] == "missing"
    assert payload["missing_review_items"] == ["human_gate_e_approval"]
    assert payload["missing_review_item_count"] == 1
    assert payload["blocking_review_items"] == []
    assert payload["blocking_review_item_count"] == 0
    assert payload["satisfactory_review_item_count"] == 5
    assert payload["public_release_approved"] is False
    assert payload["push_approved"] is False
    assert payload["merge_approved"] is False
    assert payload["public_github_approval_claimed"] is False
    _assert_gate_e_public_readiness_output_is_safe(payload)


def test_gate_e_public_readiness_reports_blockers_without_approving_release() -> None:
    payload = build_gate_e_public_readiness_preflight(
        public_docs_boundary_review_status="satisfactory",
        secret_and_private_data_review_status="blocking",
        generated_artifact_review_status="satisfactory",
        ignored_file_review_status="missing",
        push_merge_release_plan_review_status="satisfactory",
    )

    assert payload["decision"] == "blocked"
    assert payload["reason"] == "required_gate_e_preflight_items_missing_or_blocking"
    assert payload["ready_for_human_gate_e_review"] is False
    assert payload["missing_review_items"] == [
        "ignored_file_review",
        "human_gate_e_approval",
    ]
    assert payload["missing_review_item_count"] == 2
    assert payload["blocking_review_items"] == ["secret_and_private_data_review"]
    assert payload["blocking_review_item_count"] == 1
    assert payload["satisfactory_review_item_count"] == 3
    assert payload["public_release_approved"] is False
    assert payload["push_approved"] is False
    assert payload["merge_approved"] is False
    _assert_gate_e_public_readiness_output_is_safe(payload)


def test_gate_e_public_readiness_rejects_unknown_status_safely() -> None:
    with pytest.raises(ValueError) as exc_info:
        build_gate_e_public_readiness_preflight(
            public_docs_boundary_review_status="approved"
        )

    assert str(exc_info.value) == GATE_E_PUBLIC_READINESS_ERROR
    assert exc_info.value.__cause__ is None
    _assert_error_is_sanitized(str(exc_info.value))


def test_gate_e_public_readiness_sanitizes_malformed_internal_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_payload(**kwargs: object) -> dict[str, object]:
        return {"private": "C:/Users/student/token-secret-auth-profile"}

    monkeypatch.setattr(
        "async_scholar.gate_e_public_readiness._build_payload",
        fake_payload,
    )

    with pytest.raises(ValueError) as exc_info:
        build_gate_e_public_readiness_preflight()

    assert str(exc_info.value) == GATE_E_PUBLIC_READINESS_ERROR
    assert exc_info.value.__cause__ is None
    _assert_error_is_sanitized(str(exc_info.value))


def test_gate_e_public_readiness_sanitizes_internal_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_payload(**kwargs: object) -> dict[str, object]:
        raise RuntimeError("C:\\Users\\student\\.env BOT_TOKEN=secret traceback")

    monkeypatch.setattr(
        "async_scholar.gate_e_public_readiness._build_payload",
        fake_payload,
    )

    with pytest.raises(ValueError) as exc_info:
        build_gate_e_public_readiness_preflight()

    assert str(exc_info.value) == GATE_E_PUBLIC_READINESS_ERROR
    assert exc_info.value.__cause__ is None
    _assert_error_is_sanitized(str(exc_info.value))


def test_gate_e_public_readiness_does_not_touch_runtime_file_io(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_open(*args: object, **kwargs: object) -> object:
        raise AssertionError("Gate E preflight helper must not open files")

    monkeypatch.setattr(builtins, "open", fail_open)

    assert build_gate_e_public_readiness_preflight() == (
        EXPECTED_GATE_E_PUBLIC_READINESS_DEFAULT
    )


def test_gate_e_public_readiness_source_guards_forbidden_surfaces() -> None:
    source = Path("src/async_scholar/gate_e_public_readiness.py").read_text(
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

    assert imported_names == {"__future__", "typing"}

    for forbidden_fragment in (
        "pathlib",
        "os.",
        "environ",
        "open(",
        "read_text",
        "write_text",
        "mkdir",
        "unlink",
        "remove(",
        "rmdir",
        "rmtree",
        "subprocess",
        "popen",
        "powershell",
        "socket",
        "urlopen(",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "webbrowser",
        "browser.new",
        "chromium",
        "firefox",
        "auth_state",
        "profile_dir",
        "browser_profile",
        "meeting_url",
        "google",
        "meet.",
        "sounddevice",
        "microphone",
        "system audio",
        "scheduler.",
        "scheduler_execute",
        "scheduler_loop",
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


def _assert_gate_e_public_readiness_output_is_safe(
    payload: dict[str, object],
) -> None:
    combined_output = json.dumps(payload, sort_keys=True).lower()
    for false_flag in (
        "public_release_approved",
        "push_approved",
        "merge_approved",
        "public_github_approval_claimed",
        "publish_performed",
        "push_performed",
        "merge_performed",
        "browser_or_server_launched",
        "browser_automation_performed",
        "playwright_or_in_app_browser_performed",
        "screenshot_trace_video_download_performed",
        "auth_profile_accessed",
        "cookie_accessed",
        "private_data_read",
        "audio_capture_performed",
        "hardware_access_performed",
        "loopback_capture_performed",
        "live_delivery_performed",
        "scheduler_background_execution_performed",
        "deletion_or_export_performed",
        "dependency_change_performed",
        "autonomous_participation_performed",
        "academic_answer_behavior_performed",
        "product_promise_alpha_scope_broadened",
    ):
        assert payload[false_flag] is False

    assert payload["human_gate_e_approval_required"] is True
    assert payload["decision"] == "blocked"

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
        "meeting link",
        "meet.example",
        "meet.google",
        "http://",
        "https://",
        "c:\\",
        "\\\\server",
        "/users",
        ".env",
        "token",
        "raw",
        "exception",
        "traceback",
        "powershell",
        "public release approved",
        "push approved",
        "merge approved",
        "safe to publish",
        "product promise alpha passed",
        "online monitoring approved",
    ):
        assert forbidden_fragment not in combined_output


def _assert_error_is_sanitized(error_text: str) -> None:
    for forbidden_fragment in (
        "C:\\Users",
        "C:/Users",
        "student",
        ".env",
        "BOT_TOKEN",
        "token",
        "secret",
        "auth",
        "profile",
        "traceback",
    ):
        assert forbidden_fragment not in error_text
