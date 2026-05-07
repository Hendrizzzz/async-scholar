from __future__ import annotations

import base64
import subprocess
from dataclasses import asdict
from types import SimpleNamespace

import pytest

from async_scholar import desktop_notifier


def test_dispatch_desktop_notification_windows_success_uses_payload_and_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    def fake_builder(event_type: str) -> dict[str, object]:
        seen["event_type"] = event_type
        return {
            "severity": "urgent",
            "title": "Urgent lecture alert",
            "body": "Please review the latest alert.",
            "requires_confirmation": True,
        }

    def fake_runner(
        command: list[str],
        *,
        shell: bool,
        timeout: float,
    ) -> SimpleNamespace:
        seen["command"] = list(command)
        seen["shell"] = shell
        seen["timeout"] = timeout
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(
        desktop_notifier,
        "build_alert_notification_payload",
        fake_builder,
    )

    result = desktop_notifier.dispatch_desktop_notification(
        "attendance_prompt",
        fake_runner,
        platform_name="win32",
    )

    assert asdict(result) == {"status": "sent", "error_kind": None}
    assert seen["event_type"] == "attendance_prompt"
    assert seen["shell"] is False
    assert seen["timeout"] == pytest.approx(
        desktop_notifier.WINDOWS_NOTIFICATION_TIMEOUT_SECONDS,
    )

    command = seen["command"]
    assert command[0] == "powershell.exe"
    assert "-NoProfile" in command
    assert "-NonInteractive" in command
    assert "-WindowStyle" in command
    assert "-EncodedCommand" in command

    encoded_script = command[command.index("-EncodedCommand") + 1]
    script = base64.b64decode(encoded_script).decode("utf-16-le")
    assert "Urgent lecture alert" in script
    assert "Please review the latest alert." in script
    assert "'urgent'" in script
    assert "attendance_prompt" not in script
    assert "attendance_prompt" not in encoded_script


def test_dispatch_desktop_notification_windows_failure_returns_failed_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_builder(event_type: str) -> dict[str, object]:
        assert event_type == "name_call"
        return {
            "severity": "normal",
            "title": "Lecture event",
            "body": "Review the latest lecture alert.",
            "requires_confirmation": True,
        }

    def fake_runner(
        command: list[str],
        *,
        shell: bool,
        timeout: float,
    ) -> SimpleNamespace:
        return SimpleNamespace(returncode=7)

    monkeypatch.setattr(
        desktop_notifier,
        "build_alert_notification_payload",
        fake_builder,
    )

    result = desktop_notifier.dispatch_desktop_notification(
        "name_call",
        fake_runner,
        platform_name="win32",
    )

    assert asdict(result) == {"status": "failed", "error_kind": "command_failed"}


def test_dispatch_desktop_notification_unsupported_platform_skips_runner_and_builder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"builder": False, "runner": False}

    def fake_builder(event_type: str) -> dict[str, object]:
        calls["builder"] = True
        return {
            "severity": "normal",
            "title": "Lecture event",
            "body": "Review the latest lecture alert.",
            "requires_confirmation": True,
        }

    def fake_runner(
        command: list[str],
        *,
        shell: bool,
        timeout: float,
    ) -> SimpleNamespace:
        calls["runner"] = True
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(
        desktop_notifier,
        "build_alert_notification_payload",
        fake_builder,
    )

    result = desktop_notifier.dispatch_desktop_notification(
        "attendance_prompt",
        fake_runner,
        platform_name="linux",
    )

    assert asdict(result) == {
        "status": "unsupported",
        "error_kind": "unsupported_platform",
    }
    assert calls == {"builder": False, "runner": False}


def test_dispatch_desktop_notification_timeout_returns_failed_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_builder(event_type: str) -> dict[str, object]:
        return {
            "severity": "normal",
            "title": "Lecture event",
            "body": "Review the latest lecture alert.",
            "requires_confirmation": True,
        }

    def fake_runner(command: list[str], *, shell: bool, timeout: float) -> None:
        raise subprocess.TimeoutExpired(cmd=command, timeout=timeout)

    monkeypatch.setattr(
        desktop_notifier,
        "build_alert_notification_payload",
        fake_builder,
    )

    result = desktop_notifier.dispatch_desktop_notification(
        "deadline_mention",
        fake_runner,
        platform_name="win32",
    )

    assert asdict(result) == {"status": "failed", "error_kind": "timeout"}


def test_dispatch_desktop_notification_os_error_returns_failed_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_builder(event_type: str) -> dict[str, object]:
        return {
            "severity": "normal",
            "title": "Lecture event",
            "body": "Review the latest lecture alert.",
            "requires_confirmation": True,
        }

    def fake_runner(command: list[str], *, shell: bool, timeout: float) -> None:
        raise OSError("powershell not found")

    monkeypatch.setattr(
        desktop_notifier,
        "build_alert_notification_payload",
        fake_builder,
    )

    result = desktop_notifier.dispatch_desktop_notification(
        "task_prompt",
        fake_runner,
        platform_name="win32",
    )

    assert asdict(result) == {"status": "failed", "error_kind": "os_error"}


def test_dispatch_desktop_notification_suspicious_unknown_event_type_is_not_echoed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    suspicious_event_type = (
        "source-segment-id=seg-9 transcript=C:\\private\\recordings\\lecture.wav "
        "token=abc123 session=session-7"
    )
    seen: dict[str, object] = {}

    def fake_builder(event_type: str) -> dict[str, object]:
        seen["event_type"] = event_type
        return {
            "severity": "normal",
            "title": "Lecture event",
            "body": "Review the latest lecture alert.",
            "requires_confirmation": True,
        }

    def fake_runner(
        command: list[str],
        *,
        shell: bool,
        timeout: float,
    ) -> SimpleNamespace:
        seen["command"] = list(command)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(
        desktop_notifier,
        "build_alert_notification_payload",
        fake_builder,
    )

    result = desktop_notifier.dispatch_desktop_notification(
        suspicious_event_type,
        fake_runner,
        platform_name="win32",
    )

    assert asdict(result) == {"status": "sent", "error_kind": None}
    assert seen["event_type"] == suspicious_event_type
    command_text = " ".join(seen["command"])
    assert suspicious_event_type not in command_text
    assert "lecture.wav" not in command_text
    assert "token=abc123" not in command_text
