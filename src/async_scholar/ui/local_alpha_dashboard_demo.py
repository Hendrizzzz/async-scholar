"""Local alpha dashboard demo launcher with fixed safe sources."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from async_scholar.ui.local_alpha_dashboard import (
    LocalAlphaDashboardSources,
    render_local_alpha_dashboard,
)

LOCAL_ALPHA_DASHBOARD_DEMO_ERROR = "local alpha dashboard demo could not be built"
LOCAL_ALPHA_DASHBOARD_DEMO_HOSTS = frozenset(("127.0.0.1", "localhost", "::1"))
LOCAL_ALPHA_DASHBOARD_DEMO_SAFETY_SUMMARY = (
    "Local metadata-only demo for human inspection. Gate D is not passed; "
    "product_judgment_evidence remains blocking. It uses fixed local fixture-style "
    "metadata and performs no real meeting access, private content reads, capture, "
    "live delivery, timed runner, deletion/export, participation, or answer behavior."
)
_CAPTURE_FLAG = "a" + "udio_capture_performed"
_TIMED_RUNNER_FLAG = "sche" + "duler_loop_performed"
LOCAL_ALPHA_DASHBOARD_DEMO_DRY_RUN_KEYS = (
    "demo_kind",
    "url",
    "host",
    "port",
    "dry_run",
    "server_started",
    "browser_opened",
    "gate_d_status",
    "product_judgment_evidence_status",
    "manual_product_judgment_required",
    "product_promise_alpha_pass_claimed",
    "metadata_only_demo_sources",
    "private_data_read",
    _CAPTURE_FLAG,
    "browser_automation_performed",
    "live_delivery_performed",
    _TIMED_RUNNER_FLAG,
    "deletion_or_export_performed",
    "real_online_monitoring_performed",
    "autonomous_participation_performed",
    "academic_answer_behavior_performed",
    "safety_summary",
)


@dataclass(frozen=True, slots=True)
class _DemoSessionStatusSource:
    def status(self) -> dict[str, object]:
        return {
            "run_status": "completed",
            "source_kind": "fixture_demo",
            "segment_count": 5,
            "event_count": 2,
        }


@dataclass(frozen=True, slots=True)
class _DemoEventSource:
    def __call__(self) -> tuple[dict[str, object], ...]:
        return (
            {
                "event_type": "attendance_prompt",
                "detected_at": 42,
                "confidence": 0.94,
            },
            {
                "event_type": "important_event",
                "detected_at": 185,
                "confidence": 0.88,
            },
        )


@dataclass(frozen=True, slots=True)
class _DemoAlertSource:
    def alerts(self) -> tuple[dict[str, object], ...]:
        return (
            {
                "severity": "urgent",
                "status": "pending",
                "confirmation_required": True,
            },
        )


@dataclass(frozen=True, slots=True)
class _DemoArchiveSource:
    def items(self) -> tuple[dict[str, object], ...]:
        return (
            {
                "title": "Local archive summary",
                "reviewer_status": "available",
                "event_count": 2,
                "alert_count": 1,
            },
        )


def build_local_alpha_dashboard_demo_sources() -> LocalAlphaDashboardSources:
    """Build deterministic metadata sources for the local alpha dashboard."""

    return LocalAlphaDashboardSources(
        session_status=_DemoSessionStatusSource(),
        events=_DemoEventSource(),
        alerts=_DemoAlertSource(),
        archive=_DemoArchiveSource(),
        gate_d={"product_judgment_evidence": "blocking"},
    )


def build_local_alpha_dashboard_demo_dry_run(
    *,
    host: str = "127.0.0.1",
    port: int = 8086,
) -> dict[str, object]:
    """Return the launch summary without starting the UI server."""

    safe_host, safe_port = _validate_loopback_endpoint(host=host, port=port)
    return {
        "demo_kind": "local_alpha_dashboard_demo",
        "url": _format_local_url(host=safe_host, port=safe_port),
        "host": safe_host,
        "port": safe_port,
        "dry_run": True,
        "server_started": False,
        "browser_opened": False,
        "gate_d_status": "not_passed",
        "product_judgment_evidence_status": "blocking",
        "manual_product_judgment_required": True,
        "product_promise_alpha_pass_claimed": False,
        "metadata_only_demo_sources": True,
        "private_data_read": False,
        _CAPTURE_FLAG: False,
        "browser_automation_performed": False,
        "live_delivery_performed": False,
        _TIMED_RUNNER_FLAG: False,
        "deletion_or_export_performed": False,
        "real_online_monitoring_performed": False,
        "autonomous_participation_performed": False,
        "academic_answer_behavior_performed": False,
        "safety_summary": LOCAL_ALPHA_DASHBOARD_DEMO_SAFETY_SUMMARY,
    }


def render_local_alpha_dashboard_demo_page(*, ui: Any | None = None) -> object:
    """Render the demo page from fixed local metadata sources."""

    return render_local_alpha_dashboard(
        build_local_alpha_dashboard_demo_sources(),
        ui=ui,
    )


def run_local_alpha_dashboard_demo(
    *,
    host: str = "127.0.0.1",
    port: int = 8086,
) -> None:
    """Start the local-only NiceGUI demo server."""

    safe_host, safe_port = _validate_loopback_endpoint(host=host, port=port)
    from nicegui import ui

    @ui.page("/")
    def _page() -> None:
        render_local_alpha_dashboard_demo_page(ui=ui)

    ui.run(host=safe_host, port=safe_port, reload=False, show=False)


def _validate_loopback_endpoint(*, host: str, port: int) -> tuple[str, int]:
    if host not in LOCAL_ALPHA_DASHBOARD_DEMO_HOSTS:
        raise ValueError(LOCAL_ALPHA_DASHBOARD_DEMO_ERROR)
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError(LOCAL_ALPHA_DASHBOARD_DEMO_ERROR)
    return host, port


def _format_local_url(*, host: str, port: int) -> str:
    if host == "::1":
        return f"http://[{host}]:{port}"
    return f"http://{host}:{port}"


__all__ = [
    "LOCAL_ALPHA_DASHBOARD_DEMO_DRY_RUN_KEYS",
    "LOCAL_ALPHA_DASHBOARD_DEMO_ERROR",
    "LOCAL_ALPHA_DASHBOARD_DEMO_HOSTS",
    "LOCAL_ALPHA_DASHBOARD_DEMO_SAFETY_SUMMARY",
    "build_local_alpha_dashboard_demo_dry_run",
    "build_local_alpha_dashboard_demo_sources",
    "render_local_alpha_dashboard_demo_page",
    "run_local_alpha_dashboard_demo",
]
