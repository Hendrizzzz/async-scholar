from __future__ import annotations

import ast
import inspect
import json

import pytest

from async_scholar import delivery_path_smoke
from async_scholar.delivery_path_smoke import (
    DELIVERY_PATH_SMOKE_ERROR,
    build_local_delivery_path_smoke,
)

EXPECTED_DELIVERY_PATH_SMOKE_RESULT = {
    "delivery_path_evidence_status": "satisfactory",
    "desktop_path_status": "sent",
    "gate_d_pass_claimed": False,
    "live_delivery_performed": False,
    "network_performed": False,
    "product_promise_alpha_pass_claimed": False,
    "smoke_kind": "local_delivery_path",
    "subprocess_performed": False,
    "telegram_path_status": "sent",
}


def test_local_delivery_path_smoke_builds_allowlisted_satisfactory_summary() -> None:
    result = build_local_delivery_path_smoke()

    assert result == EXPECTED_DELIVERY_PATH_SMOKE_RESULT
    assert list(result) == list(EXPECTED_DELIVERY_PATH_SMOKE_RESULT)
    assert json.loads(json.dumps(result)) == result
    _assert_delivery_path_smoke_output_is_safe(result)


def test_local_delivery_path_smoke_accepts_no_private_or_free_form_input() -> None:
    assert inspect.signature(build_local_delivery_path_smoke).parameters == {}


def test_local_delivery_path_smoke_composes_adapters_with_fake_boundaries(
    monkeypatch,
) -> None:
    seen: dict[str, object] = {}

    def fake_desktop(
        event_type: str,
        command_runner,
        *,
        platform_name: str | None = None,
    ) -> object:
        seen["desktop_event_type"] = event_type
        seen["desktop_platform_name"] = platform_name
        seen["desktop_runner_result"] = command_runner(
            ["private command must not be recorded"],
            shell=False,
            timeout=10.0,
        ).returncode
        return type("DesktopResult", (), {"status": "sent"})()

    def fake_telegram(
        event_type: str,
        *,
        bot_token: str | None,
        chat_id: str | int | None,
        opener,
    ) -> dict[str, object]:
        seen["telegram_event_type"] = event_type
        seen["telegram_has_token"] = isinstance(bot_token, str) and bool(bot_token)
        seen["telegram_has_chat_id"] = isinstance(chat_id, str) and bool(chat_id)
        seen["telegram_opener_result"] = opener(
            object(),
            timeout=10.0,
        ).status
        return {"status": "sent"}

    monkeypatch.setattr(
        delivery_path_smoke,
        "dispatch_desktop_notification",
        fake_desktop,
    )
    monkeypatch.setattr(
        delivery_path_smoke,
        "dispatch_telegram_alert_notification",
        fake_telegram,
    )

    result = build_local_delivery_path_smoke()

    assert result == EXPECTED_DELIVERY_PATH_SMOKE_RESULT
    assert seen == {
        "desktop_event_type": "attendance_prompt",
        "desktop_platform_name": "win32",
        "desktop_runner_result": 0,
        "telegram_event_type": "attendance_prompt",
        "telegram_has_token": True,
        "telegram_has_chat_id": True,
        "telegram_opener_result": 200,
    }


def test_local_delivery_path_smoke_fails_closed_if_adapter_status_changes(
    monkeypatch,
) -> None:
    def fake_desktop(*args, **kwargs) -> object:
        return type("DesktopResult", (), {"status": "failed"})()

    monkeypatch.setattr(
        delivery_path_smoke,
        "dispatch_desktop_notification",
        fake_desktop,
    )

    with pytest.raises(ValueError, match=DELIVERY_PATH_SMOKE_ERROR) as exc_info:
        build_local_delivery_path_smoke()

    assert str(exc_info.value) == DELIVERY_PATH_SMOKE_ERROR
    assert exc_info.value.__cause__ is None


def test_local_delivery_path_smoke_sanitizes_underlying_failures(monkeypatch) -> None:
    def fake_telegram(*args, **kwargs) -> dict[str, object]:
        raise RuntimeError("C:\\Users\\student\\.env BOT_TOKEN=secret traceback")

    monkeypatch.setattr(
        delivery_path_smoke,
        "dispatch_telegram_alert_notification",
        fake_telegram,
    )

    with pytest.raises(ValueError, match=DELIVERY_PATH_SMOKE_ERROR) as exc_info:
        build_local_delivery_path_smoke()

    assert str(exc_info.value) == DELIVERY_PATH_SMOKE_ERROR
    assert exc_info.value.__cause__ is None
    assert "BOT_TOKEN" not in str(exc_info.value)
    assert "secret" not in str(exc_info.value)
    assert "Users" not in str(exc_info.value)


def test_local_delivery_path_smoke_source_has_only_fake_delivery_boundaries() -> None:
    source = inspect.getsource(delivery_path_smoke)
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
        "subprocess",
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

    assert "dispatch_desktop_notification" in source
    assert "command_runner=fake_runner" in source
    assert 'platform_name="win32"' in source
    assert "dispatch_telegram_alert_notification" in source
    assert "opener=fake_opener" in source
    assert "bot_token=" in source
    assert "chat_id=" in source

    for forbidden_fragment in (
        "getenv",
        "environ",
        "expanduser",
        "read_text",
        "write_text",
        "mkdir",
        "unlink",
        "remove",
        "rmdir",
        "rmtree",
        "dispatch_alert",
        "urlopen(",
        "subprocess.run",
        "powershell",
        "requests",
        "httpx",
        "socket",
        "playwright",
        "selenium",
        "webbrowser",
        "sounddevice",
        "faster_whisper",
        "loopback",
        "browser",
        "cookie",
        "profile",
        "meeting",
        "transcript",
        "question",
        "sleep",
        "timer(",
        "threading",
        "asyncio",
        "__import__",
        "eval(",
        "exec(",
    ):
        assert forbidden_fragment not in source_lower


def _assert_delivery_path_smoke_output_is_safe(result: dict[str, object]) -> None:
    assert result["live_delivery_performed"] is False
    assert result["network_performed"] is False
    assert result["subprocess_performed"] is False
    assert result["gate_d_pass_claimed"] is False
    assert result["product_promise_alpha_pass_claimed"] is False

    serialized = json.dumps(result).lower()
    assert set(result) == {
        "smoke_kind",
        "desktop_path_status",
        "telegram_path_status",
        "delivery_path_evidence_status",
        "live_delivery_performed",
        "network_performed",
        "subprocess_performed",
        "gate_d_pass_claimed",
        "product_promise_alpha_pass_claimed",
    }
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
        "google",
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
        "browser",
        "profile",
        "transcript",
        "audio",
        "camera",
        "raw",
        "exception",
        "traceback",
        "powershell",
        "playwright",
        "loopback",
        "gate d passed",
        "product promise alpha passed",
    ):
        assert forbidden_fragment not in serialized
