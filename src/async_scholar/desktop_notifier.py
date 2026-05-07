"""Desktop notification adapter for alert payloads."""

from __future__ import annotations

import base64
import re
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Literal

from async_scholar.alerts import build_alert_notification_payload

WINDOWS_NOTIFICATION_TIMEOUT_SECONDS = 10.0
_TITLE_LIMIT = 120
_BODY_LIMIT = 240
_ALLOWED_SEVERITIES = {"low", "normal", "urgent"}
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]+")
_WHITESPACE_RE = re.compile(r"\s+")

DesktopNotificationStatus = Literal["sent", "failed", "unsupported"]
DesktopNotificationErrorKind = Literal[
    "command_failed",
    "timeout",
    "os_error",
    "unsupported_platform",
]


@dataclass(frozen=True, slots=True)
class DesktopNotificationResult:
    """Sanitized result from the desktop notifier adapter."""

    status: DesktopNotificationStatus
    error_kind: DesktopNotificationErrorKind | None = None


CommandRunner = Callable[..., Any]


def dispatch_desktop_notification(
    event_type: str,
    command_runner: CommandRunner = subprocess.run,
    *,
    platform_name: str | None = None,
) -> DesktopNotificationResult:
    """Dispatch a Windows desktop notification for the alert payload.

    The adapter stays dependency-free and returns a coarse, allowlisted
    result that never includes command output or raw exception details.
    """

    if not _is_windows_platform(platform_name or sys.platform):
        return DesktopNotificationResult(
            status="unsupported",
            error_kind="unsupported_platform",
        )

    payload = build_alert_notification_payload(event_type)
    command = _build_windows_notification_command(payload)

    try:
        run_result = command_runner(
            command,
            shell=False,
            timeout=WINDOWS_NOTIFICATION_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return DesktopNotificationResult(status="failed", error_kind="timeout")
    except OSError:
        return DesktopNotificationResult(status="failed", error_kind="os_error")
    except subprocess.CalledProcessError:
        return DesktopNotificationResult(
            status="failed",
            error_kind="command_failed",
        )

    if _command_succeeded(run_result):
        return DesktopNotificationResult(status="sent")

    return DesktopNotificationResult(status="failed", error_kind="command_failed")


def _is_windows_platform(platform_name: str) -> bool:
    platform_key = platform_name.lower()
    return platform_key.startswith("win") or platform_key == "windows"


def _command_succeeded(run_result: Any) -> bool:
    returncode = getattr(run_result, "returncode", None)
    if returncode is None:
        return True

    try:
        return int(returncode) == 0
    except (TypeError, ValueError):
        return False


def _build_windows_notification_command(payload: Any) -> list[str]:
    severity = _coerce_severity(_payload_field(payload, "severity", "normal"))
    title = _sanitize_notification_text(
        _payload_field(payload, "title", "Lecture event"),
        fallback="Lecture event",
        limit=_TITLE_LIMIT,
    )
    body = _sanitize_notification_text(
        _payload_field(payload, "body", "Review the latest lecture alert."),
        fallback="Review the latest lecture alert.",
        limit=_BODY_LIMIT,
    )

    script_parts = [
        "$ErrorActionPreference = 'Stop'",
        "Add-Type -AssemblyName System.Windows.Forms",
        "Add-Type -AssemblyName System.Drawing",
        f"$severity = {_powershell_quote(severity)}",
        f"$title = {_powershell_quote(title)}",
        f"$body = {_powershell_quote(body)}",
        "$balloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Info",
        "$icon = [System.Drawing.SystemIcons]::Information",
        "if ($severity -eq 'urgent') {",
        "    $balloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Warning",
        "    $icon = [System.Drawing.SystemIcons]::Warning",
        "} elseif ($severity -eq 'low') {",
        "    $balloonTipIcon = [System.Windows.Forms.ToolTipIcon]::None",
        "}",
        "$notify = New-Object System.Windows.Forms.NotifyIcon",
        "$notify.Icon = $icon",
        "$notify.BalloonTipIcon = $balloonTipIcon",
        "$notify.BalloonTipTitle = $title",
        "$notify.BalloonTipText = $body",
        "$notify.Visible = $true",
        "$notify.ShowBalloonTip(5000)",
        "Start-Sleep -Milliseconds 200",
        "$notify.Dispose()",
    ]

    script = "; ".join(script_parts)
    encoded_script = base64.b64encode(script.encode("utf-16-le")).decode("ascii")

    return [
        "powershell.exe",
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-WindowStyle",
        "Hidden",
        "-ExecutionPolicy",
        "Bypass",
        "-EncodedCommand",
        encoded_script,
    ]


def _payload_field(payload: Any, key: str, fallback: str) -> str:
    value: Any
    if isinstance(payload, Mapping):
        value = payload.get(key, fallback)
    else:
        value = getattr(payload, key, fallback)
    return fallback if value is None else str(value)


def _coerce_severity(value: str) -> str:
    severity = _sanitize_notification_text(value, fallback="normal", limit=16).lower()
    if severity not in _ALLOWED_SEVERITIES:
        return "normal"
    return severity


def _sanitize_notification_text(value: str, *, fallback: str, limit: int) -> str:
    text = _CONTROL_CHARS_RE.sub(" ", value)
    text = _WHITESPACE_RE.sub(" ", text).strip()
    if not text:
        text = fallback
    if len(text) > limit:
        text = text[:limit].rstrip()
    return text


def _powershell_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"
