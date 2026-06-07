from __future__ import annotations

import builtins
import inspect
import json
import subprocess
import sys
import types
from pathlib import Path

import async_scholar.__main__ as cli

GATE_E_PUBLIC_READINESS_ERROR = "gate e public readiness could not be built"
EXPECTED_GATE_E_PUBLIC_READINESS_CURRENT_STATUS_KWARGS = {
    "public_docs_boundary_review_status": "satisfactory",
    "secret_and_private_data_review_status": "satisfactory",
    "generated_artifact_review_status": "satisfactory",
    "ignored_file_review_status": "satisfactory",
    "push_merge_release_plan_review_status": "satisfactory",
}
EXPECTED_GATE_E_PUBLIC_READINESS_CURRENT_STATUS = {
    "preflight_kind": "gate_e_public_readiness",
    "mode": "dry_run_report_only",
    "gate_d_scope_status": "narrow_local_fixture_to_reviewer_pass_recorded",
    "gate_e_status": "human_approval_required",
    "decision": "blocked",
    "reason": "human_gate_e_approval_required",
    "ready_for_human_gate_e_review": True,
    "human_gate_e_approval_required": True,
    "human_gate_e_approval_status": "missing",
    "public_docs_boundary_review_status": "satisfactory",
    "secret_and_private_data_review_status": "satisfactory",
    "generated_artifact_review_status": "satisfactory",
    "ignored_file_review_status": "satisfactory",
    "push_merge_release_plan_review_status": "satisfactory",
    "missing_review_items": [
        "human_gate_e_approval",
    ],
    "missing_review_item_count": 1,
    "blocking_review_items": [],
    "blocking_review_item_count": 0,
    "satisfactory_review_item_count": 5,
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


def test_top_level_help_lists_gate_e_public_readiness_command() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "async_scholar", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "gate-e-public-readiness" in result.stdout


def test_gate_e_public_readiness_help_stays_lazy(monkeypatch) -> None:
    module_name = "async_scholar.gate_e_public_readiness"
    monkeypatch.delitem(sys.modules, module_name, raising=False)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "gate-e-public-readiness",
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "usage: async_scholar gate-e-public-readiness" in result.stdout
    assert "--dry-run" in result.stdout
    assert module_name not in sys.modules


def test_gate_e_public_readiness_dry_run_prints_compact_json() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "gate-e-public-readiness",
            "--dry-run",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    expected_line = json.dumps(
        EXPECTED_GATE_E_PUBLIC_READINESS_CURRENT_STATUS,
        sort_keys=True,
        separators=(",", ":"),
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout == f"{expected_line}\n"
    _assert_gate_e_public_readiness_output_is_safe(result.stdout, result.stderr)


def test_gate_e_public_readiness_dry_run_does_not_create_files(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "gate-e-public-readiness",
            "--dry-run",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    assert list(tmp_path.iterdir()) == []
    _assert_gate_e_public_readiness_output_is_safe(result.stdout, result.stderr)


def test_gate_e_public_readiness_requires_dry_run_safely() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "async_scholar", "gate-e-public-readiness"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == f"{GATE_E_PUBLIC_READINESS_ERROR}\n"


def test_gate_e_public_readiness_rejects_extra_arguments_safely() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "gate-e-public-readiness",
            "--dry-run",
            "C:\\Users\\student\\token-secret-auth-profile",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == f"{GATE_E_PUBLIC_READINESS_ERROR}\n"
    _assert_error_is_sanitized(result.stderr)


def test_gate_e_public_readiness_misordered_uses_fixed_error() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "--private-path",
            "C:\\Users\\student\\token-secret-auth-profile",
            "gate-e-public-readiness",
            "--dry-run",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == f"{GATE_E_PUBLIC_READINESS_ERROR}\n"
    _assert_error_is_sanitized(result.stderr)


def test_gate_e_public_readiness_sanitizes_import_failure(
    capsys,
    monkeypatch,
) -> None:
    real_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "async_scholar.gate_e_public_readiness":
            raise ImportError(
                "C:\\Users\\student\\.env BOT_TOKEN=secret import traceback"
            )
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    exit_code = cli.main(["gate-e-public-readiness", "--dry-run"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == f"{GATE_E_PUBLIC_READINESS_ERROR}\n"
    _assert_error_is_sanitized(captured.err)


def test_gate_e_public_readiness_sanitizes_malformed_helper_output(
    capsys,
    monkeypatch,
) -> None:
    module_name = "async_scholar.gate_e_public_readiness"
    fake_module = types.ModuleType(module_name)

    def fake_build_gate_e_public_readiness_preflight(
        **kwargs: object,
    ) -> dict[str, object]:
        _assert_gate_e_public_readiness_current_status_kwargs(kwargs)
        return {"private": object()}

    fake_module.build_gate_e_public_readiness_preflight = (
        fake_build_gate_e_public_readiness_preflight
    )
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(["gate-e-public-readiness", "--dry-run"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == f"{GATE_E_PUBLIC_READINESS_ERROR}\n"


def test_gate_e_public_readiness_sanitizes_json_malformed_output(
    capsys,
    monkeypatch,
) -> None:
    module_name = "async_scholar.gate_e_public_readiness"
    fake_module = types.ModuleType(module_name)

    def fake_build_gate_e_public_readiness_preflight(
        **kwargs: object,
    ) -> dict[str, object]:
        _assert_gate_e_public_readiness_current_status_kwargs(kwargs)
        return {"private": "C:/Users/student/token-secret-auth-profile"}

    fake_module.build_gate_e_public_readiness_preflight = (
        fake_build_gate_e_public_readiness_preflight
    )
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(["gate-e-public-readiness", "--dry-run"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == f"{GATE_E_PUBLIC_READINESS_ERROR}\n"
    _assert_error_is_sanitized(captured.err)


def test_gate_e_public_readiness_rejects_broad_approval_payload(
    capsys,
    monkeypatch,
) -> None:
    module_name = "async_scholar.gate_e_public_readiness"
    fake_module = types.ModuleType(module_name)

    def fake_build_gate_e_public_readiness_preflight(
        **kwargs: object,
    ) -> dict[str, object]:
        _assert_gate_e_public_readiness_current_status_kwargs(kwargs)
        payload = dict(EXPECTED_GATE_E_PUBLIC_READINESS_CURRENT_STATUS)
        payload["public_release_approved"] = True
        payload["push_approved"] = True
        payload["merge_approved"] = True
        return payload

    fake_module.build_gate_e_public_readiness_preflight = (
        fake_build_gate_e_public_readiness_preflight
    )
    monkeypatch.setitem(sys.modules, module_name, fake_module)

    exit_code = cli.main(["gate-e-public-readiness", "--dry-run"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == f"{GATE_E_PUBLIC_READINESS_ERROR}\n"


def test_gate_e_public_readiness_handler_stays_thin() -> None:
    source = inspect.getsource(cli._run_gate_e_public_readiness_command)

    assert "build_gate_e_public_readiness_preflight" in source
    assert "ImportError" in source
    assert "except" in source
    for forbidden_fragment in (
        "Path",
        "open(",
        "read_text",
        "write_text",
        "mkdir",
        "unlink",
        "remove",
        "rmdir",
        "rmtree",
        "subprocess",
        "socket",
        "requests",
        "httpx",
        "playwright",
        "selenium",
        "webbrowser",
        "sounddevice",
        "microphone",
        "sleep",
        "timer",
    ):
        assert forbidden_fragment not in source


def _assert_gate_e_public_readiness_output_is_safe(
    stdout: str,
    stderr: str,
) -> None:
    payload = json.loads(stdout)
    assert payload["human_gate_e_approval_required"] is True
    assert payload["decision"] == "blocked"
    assert payload["public_release_approved"] is False
    assert payload["push_approved"] is False
    assert payload["merge_approved"] is False
    assert payload["public_github_approval_claimed"] is False
    assert payload["publish_performed"] is False
    assert payload["push_performed"] is False
    assert payload["merge_performed"] is False
    assert payload["browser_or_server_launched"] is False
    assert payload["browser_automation_performed"] is False
    assert payload["playwright_or_in_app_browser_performed"] is False
    assert payload["screenshot_trace_video_download_performed"] is False
    assert payload["auth_profile_accessed"] is False
    assert payload["cookie_accessed"] is False
    assert payload["private_data_read"] is False
    assert payload["audio_capture_performed"] is False
    assert payload["hardware_access_performed"] is False
    assert payload["loopback_capture_performed"] is False
    assert payload["live_delivery_performed"] is False
    assert payload["scheduler_background_execution_performed"] is False
    assert payload["deletion_or_export_performed"] is False
    assert payload["dependency_change_performed"] is False
    assert payload["autonomous_participation_performed"] is False
    assert payload["academic_answer_behavior_performed"] is False
    assert payload["product_promise_alpha_scope_broadened"] is False
    assert set(payload) == set(EXPECTED_GATE_E_PUBLIC_READINESS_CURRENT_STATUS)

    combined_output = f"{stdout}\n{stderr}".lower()
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


def _assert_gate_e_public_readiness_current_status_kwargs(
    kwargs: dict[str, object],
) -> None:
    assert kwargs == EXPECTED_GATE_E_PUBLIC_READINESS_CURRENT_STATUS_KWARGS
