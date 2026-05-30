"""Local alpha dashboard demo launcher with fixed safe sources."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Any

from async_scholar.ui.local_alpha_dashboard import (
    LocalAlphaDashboardSources,
    format_local_alpha_dashboard_inspection,
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
_STATIC_DEMO_SECTION_HEADINGS = (
    "Gate D safety",
    "Evidence digest",
    "Session status",
    "Detected events",
    "Alert preview",
    "Archive and reviewer",
    "Safety boundary",
)
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
_GATE_D_BLOCKER = "product_judgment_evidence"


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
        gate_d=_build_demo_gate_d_metadata(),
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


def build_local_alpha_dashboard_inspection_summary() -> str:
    """Build a no-server plain-text local alpha inspection summary."""

    return format_local_alpha_dashboard_inspection(
        build_local_alpha_dashboard_demo_sources()
    )


def build_local_alpha_dashboard_static_demo_html() -> str:
    """Build a standalone static HTML local alpha dashboard demo."""

    summary_lines = tuple(
        line for line in build_local_alpha_dashboard_inspection_summary().splitlines()
    )
    sections = _build_static_demo_sections(summary_lines)
    section_html = "\n".join(
        _render_static_demo_section(heading, lines) for heading, lines in sections
    )
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "  <title>AsyncScholar local alpha static demo</title>\n"
        "  <style>\n"
        "    body { margin: 0; font-family: Arial, sans-serif; "
        "background: #f7f8fa; color: #17202a; }\n"
        "    main { max-width: 960px; margin: 0 auto; padding: 40px 20px; }\n"
        "    h1 { font-size: 28px; margin: 0 0 16px; }\n"
        "    p { margin: 0; color: #4d5b6a; line-height: 1.5; }\n"
        "    .intro { margin: 0 0 24px; }\n"
        "    .dashboard { display: grid; grid-template-columns: repeat(2, "
        "minmax(0, 1fr)); gap: 14px; }\n"
        "    section { background: #ffffff; border: 1px solid #d8dee6; "
        "border-radius: 8px; padding: 16px; }\n"
        "    h2 { font-size: 16px; margin: 0 0 12px; color: #17202a; }\n"
        "    ol { margin: 0; padding: 0; list-style: none; display: grid; "
        "gap: 8px; }\n"
        "    li { border: 1px solid #edf0f4; border-radius: 6px; "
        "padding: 9px 10px; color: #324153; }\n"
        "    @media (max-width: 700px) { .dashboard { grid-template-columns: 1fr; } }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        "  <main>\n"
        "    <h1>AsyncScholar local alpha static demo</h1>\n"
        '    <p class="intro">No-server, no-browser export of the fixed local '
        "alpha story.</p>\n"
        '    <div class="dashboard">\n'
        f"{section_html}\n"
        "    </div>\n"
        "  </main>\n"
        "</body>\n"
        "</html>\n"
    )


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


def _build_demo_gate_d_metadata() -> dict[str, object]:
    try:
        packet = _build_local_gate_d_handoff_packet()
    except Exception:
        return _fallback_gate_d_metadata()

    if not isinstance(packet, dict):
        return _fallback_gate_d_metadata()
    return {
        "product_judgment_evidence_status": "blocking",
        "blocking_evidence": [_GATE_D_BLOCKER],
        "satisfactory_evidence_count": _safe_demo_gate_d_count(
            packet.get("satisfactory_evidence_count")
        ),
        "missing_evidence_count": _safe_demo_gate_d_count(
            packet.get("missing_evidence_count")
        ),
        "ready_for_gate_review": False,
        "manual_product_judgment_required": True,
        "manual_product_judgment_recorded": False,
        "gate_d_pass_claimed": False,
        "product_promise_alpha_pass_claimed": False,
    }


def _fallback_gate_d_metadata() -> dict[str, object]:
    return {
        "product_judgment_evidence_status": "blocking",
        "blocking_evidence": [_GATE_D_BLOCKER],
        "satisfactory_evidence_count": 0,
        "missing_evidence_count": 0,
        "ready_for_gate_review": False,
        "manual_product_judgment_required": True,
        "manual_product_judgment_recorded": False,
        "gate_d_pass_claimed": False,
        "product_promise_alpha_pass_claimed": False,
    }


def _safe_demo_gate_d_count(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return min(max(value, 0), 9999)
    return 0


def _build_static_demo_sections(
    summary_lines: tuple[str, ...],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    intro_lines: list[str] = []
    grouped: dict[str, list[str]] = {
        heading: [] for heading in _STATIC_DEMO_SECTION_HEADINGS
    }
    current_heading: str | None = None

    for line in summary_lines[1:]:
        if line in grouped:
            current_heading = line
            continue
        if current_heading is None:
            intro_lines.append(line)
            continue
        grouped[current_heading].append(line)

    if intro_lines:
        grouped["Session status"] = intro_lines + grouped["Session status"]
    grouped["Evidence digest"] = list(_build_static_demo_evidence_digest_lines())

    return tuple(
        (heading, tuple(grouped[heading])) for heading in _STATIC_DEMO_SECTION_HEADINGS
    )


def _render_static_demo_section(heading: str, lines: tuple[str, ...]) -> str:
    if lines:
        items = "\n".join(
            f"          <li>{escape(line, quote=True)}</li>" for line in lines
        )
        body = f"        <ol>\n{items}\n        </ol>\n"
    else:
        body = "        <p>Metadata unavailable.</p>\n"
    return (
        "      <section>\n"
        f"        <h2>{escape(heading, quote=True)}</h2>\n"
        f"{body}"
        "      </section>"
    )


def _build_static_demo_evidence_digest_lines() -> tuple[str, ...]:
    digest = _build_static_demo_evidence_digest()
    return (
        f"Handoff status: {digest['handoff_status']}",
        f"Local bundle status: {digest['local_bundle_status']}",
        f"Satisfactory evidence: {digest['satisfactory_evidence_count']}",
        f"Missing evidence: {digest['missing_evidence_count']}",
        f"Blocking evidence: {digest['blocking_evidence']}",
        "Manual product judgment required: "
        f"{digest['manual_product_judgment_required']}",
        "Manual product judgment recorded: "
        f"{digest['manual_product_judgment_recorded']}",
        f"AI can complete product judgment: {digest['review_can_be_completed_by_ai']}",
    )


def _build_static_demo_evidence_digest() -> dict[str, object]:
    try:
        packet = _build_local_gate_d_handoff_packet()
    except Exception:
        return _fallback_static_demo_evidence_digest()

    if not isinstance(packet, dict):
        return _fallback_static_demo_evidence_digest()
    if packet.get("product_judgment_evidence_status") != "blocking":
        return _fallback_static_demo_evidence_digest()
    if packet.get("handoff_packet_status") != "ready_for_manual_review":
        return _fallback_static_demo_evidence_digest()
    if packet.get("local_gate_d_bundle_status") != "blocked":
        return _fallback_static_demo_evidence_digest()
    if packet.get("manual_product_judgment_required") is not True:
        return _fallback_static_demo_evidence_digest()
    if packet.get("manual_product_judgment_recorded") is not False:
        return _fallback_static_demo_evidence_digest()
    if packet.get("review_can_be_completed_by_ai") is not False:
        return _fallback_static_demo_evidence_digest()
    if packet.get("gate_d_pass_claimed") is True:
        return _fallback_static_demo_evidence_digest()
    if packet.get("product_promise_alpha_pass_claimed") is True:
        return _fallback_static_demo_evidence_digest()
    blockers = packet.get("blocking_evidence")
    if (
        not isinstance(blockers, list | tuple)
        or len(blockers) != 1
        or blockers[0] != _GATE_D_BLOCKER
    ):
        return _fallback_static_demo_evidence_digest()

    return {
        "handoff_status": "Ready for manual review",
        "local_bundle_status": "Blocked",
        "satisfactory_evidence_count": _safe_demo_gate_d_count(
            packet.get("satisfactory_evidence_count")
        ),
        "missing_evidence_count": _safe_demo_gate_d_count(
            packet.get("missing_evidence_count")
        ),
        "blocking_evidence": _GATE_D_BLOCKER,
        "manual_product_judgment_required": "yes",
        "manual_product_judgment_recorded": "no",
        "review_can_be_completed_by_ai": "no",
    }


def _fallback_static_demo_evidence_digest() -> dict[str, object]:
    return {
        "handoff_status": "Ready for manual review",
        "local_bundle_status": "Blocked",
        "satisfactory_evidence_count": 0,
        "missing_evidence_count": 0,
        "blocking_evidence": _GATE_D_BLOCKER,
        "manual_product_judgment_required": "yes",
        "manual_product_judgment_recorded": "no",
        "review_can_be_completed_by_ai": "no",
    }


def _build_local_gate_d_handoff_packet() -> dict[str, object]:
    from async_scholar.gate_d_handoff_packet import build_local_gate_d_handoff_packet

    return build_local_gate_d_handoff_packet()


__all__ = [
    "LOCAL_ALPHA_DASHBOARD_DEMO_DRY_RUN_KEYS",
    "LOCAL_ALPHA_DASHBOARD_DEMO_ERROR",
    "LOCAL_ALPHA_DASHBOARD_DEMO_HOSTS",
    "LOCAL_ALPHA_DASHBOARD_DEMO_SAFETY_SUMMARY",
    "build_local_alpha_dashboard_demo_dry_run",
    "build_local_alpha_dashboard_demo_sources",
    "build_local_alpha_dashboard_inspection_summary",
    "build_local_alpha_dashboard_static_demo_html",
    "render_local_alpha_dashboard_demo_page",
    "run_local_alpha_dashboard_demo",
]
