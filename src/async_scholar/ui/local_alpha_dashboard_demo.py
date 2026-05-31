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
    "Manual review status",
    "Demo review checklist",
    "Human judgment next step",
    "Session status",
    "Demo source status",
    "Local demo launch",
    "Demo verification status",
    "Backend evidence trail",
    "Local alpha demo runbook",
    "Demo timeline",
    "Detected events",
    "Alert preview",
    "Confirmation queue",
    "Action controls",
    "Archive review status",
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
_STATIC_DEMO_TIMELINE_LINES = (
    "Fixture source prepared",
    "Session completed",
    "Event detected",
    "Alert awaiting confirmation",
    "Archive/reviewer metadata ready",
    "Gate D blocked",
)
_STATIC_DEMO_CONFIRMATION_QUEUE_LINES = (
    "User confirmation required",
    "Alert status: pending",
    "Participation action sent: no",
    "Autonomous participation: no",
    "Live delivery: no",
    "Academic answer behavior: no",
)
_STATIC_DEMO_ACTION_CONTROL_LINES = (
    "Action: Review alert confirmation",
    "Action: Send participation action",
    "Action: Open archive reviewer",
    "Action: Record product judgment",
    "User confirmation required",
    "Alert delivery live: no",
    "Participation action sent: no",
    "Autonomous participation: no",
    "Academic answer behavior: no",
    "Gate D not passed",
    "Product Promise Alpha not passed",
)
_STATIC_DEMO_ARCHIVE_REVIEW_STATUS_LINES = (
    "Archive artifacts: metadata only",
    "Reviewer summary: metadata only",
    "Detected events archived: 2",
    "Alert previews archived: pending confirmation",
    "Transcript text displayed: no",
    "Recording displayed: no",
    "Private paths displayed: no",
    "Delete/export execution: no",
    "Gate D not passed",
    "Product Promise Alpha not passed",
)
_STATIC_DEMO_MANUAL_REVIEW_STATUS_LINES = (
    "Review packet: local metadata only",
    "Human product judgment: required",
    "Final product judgment recorded: no",
    "AI can complete product judgment: no",
    "Gate D blocker: product_judgment_evidence",
    "Private data needed for review: no",
    "Live services needed for review: no",
    "Action execution allowed: no",
    "Product Promise Alpha not passed",
)
_STATIC_DEMO_REVIEW_CHECKLIST_LINES = (
    "Session status visible: yes",
    "Detected event summary visible: yes",
    "Alert preview requires confirmation: yes",
    "Archive/reviewer metadata visible: yes",
    "Gate D blocker visible: product_judgment_evidence",
    "Human product judgment required: yes",
    "Action execution allowed: no",
    "Product Promise Alpha not passed",
)
_STATIC_DEMO_HUMAN_JUDGMENT_NEXT_STEP_LINES = (
    "Manual inspection required: yes",
    "Product judgment recorded: no",
    "AI can complete product judgment: no",
    "AI can record product judgment: no",
    "product_judgment_evidence remains blocking",
    "Action execution allowed: no",
    "Product Promise Alpha not passed",
)
_STATIC_DEMO_LOCAL_LAUNCH_LINES = (
    "Static demo entrypoint: scripts/run_local_alpha_dashboard_static_demo.ps1",
    "CLI export command: local-alpha-dashboard-static-demo --output local-html-file",
    "Server started: no",
    "Browser opened: no",
    "Live delivery: no",
    "Private data read: no",
    "Gate D not passed",
    "Product Promise Alpha not passed",
)
_STATIC_DEMO_SOURCE_STATUS_LINES = (
    "Session source: fixed fixture metadata",
    "Event source: fixed fixture metadata",
    "Alert source: fixed fixture metadata",
    "Archive source: fixed fixture metadata",
    "Gate D source: local handoff metadata",
    "Transcript source: not displayed",
    "Recording source: not displayed",
    "Private source data read: no",
    "Source refresh required: no",
    "Product Promise Alpha not passed",
)
_STATIC_DEMO_VERIFICATION_STATUS_LINES = (
    "Static artifact: generated locally",
    "Source mode: fixed fixture metadata",
    "Server required: no",
    "Browser required: no",
    "Inspection command: local-alpha-dashboard-inspection",
    "Static export command: local-alpha-dashboard-static-demo --output local-html-file",
    "Gate D evidence bundle: blocked",
    "Blocking evidence: product_judgment_evidence",
    "Manual product judgment required: yes",
    "Product Promise Alpha not passed",
)
_STATIC_DEMO_BACKEND_EVIDENCE_TRAIL_LINES = (
    "Fixture/local demo evidence: existing CLI surfaces",
    "Inspection summary: local-alpha-dashboard-inspection",
    "Static export: local-alpha-dashboard-static-demo --output local-html-file",
    "Gate D evidence bundle: gate-d-local-evidence-bundle",
    "Gate D handoff packet: gate-d-handoff-packet-local",
    "Artifact access performed: no",
    "Command execution performed by page: no",
    "Private data required: no",
    "product_judgment_evidence remains blocking",
    "Product Promise Alpha not passed",
)
_STATIC_DEMO_RUNBOOK_LINES = (
    "1. Run fixture/local demo evidence",
    "2. Inspect dashboard safety status",
    "3. Export static local alpha dashboard",
    "4. Review Gate D evidence bundle",
    "5. Review Gate D handoff packet",
    "Commands are copied manually; the page executes none",
    "Artifacts are not opened by the page",
    "Private data required: no",
    "product_judgment_evidence remains blocking",
    "Product Promise Alpha not passed",
)
_STATIC_DEMO_SUMMARY_STATUS_STRIP_LINES = (
    "Gate D: blocked",
    "Product judgment: deferred",
    "Session: completed",
    "Detected events: 2",
    "Alert: pending confirmation",
    "Live delivery: no",
)
_UNSAFE_STATIC_DEMO_TEXT_MARKERS = (
    "traceback",
    "sec" + "ret",
    "." + "env",
    "coo" + "kie",
    "tok" + "en",
    "au" + "th",
    "pro" + "file",
    "meet.",
    "http:",
    "https:",
    "file:",
    "\\\\",
    "c:\\",
    ":/",
    ".jsonl",
    ".wav",
    ".mp4",
    ".png",
    "transcript",
    "gate d: passed",
    "product promise alpha: passed",
    "product_judgment_evidence_status: satisfactory",
    "server started: yes",
    "browser opened: yes",
    "live delivery: yes",
    "private data read: yes",
    "gate d passed",
    "product promise alpha passed",
    "product judgment evidence satisfied",
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
    status_strip_html = _render_static_demo_summary_status_strip(
        _safe_static_demo_summary_status_strip_lines()
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
        "    .summary-status-strip { display: flex; flex-wrap: wrap; "
        "gap: 8px; margin: 0 0 16px; }\n"
        "    .summary-status-strip span { border: 1px solid #d8dee6; "
        "border-radius: 6px; padding: 7px 9px; background: #ffffff; "
        "color: #324153; font-size: 14px; }\n"
        "    .dashboard { display: grid; grid-template-columns: repeat(2, "
        "minmax(0, 1fr)); gap: 14px; }\n"
        "    section { background: #ffffff; border: 1px solid #d8dee6; "
        "border-radius: 8px; padding: 16px; }\n"
        "    h2 { font-size: 16px; margin: 0 0 12px; color: #17202a; }\n"
        "    ol { margin: 0; padding: 0; list-style: none; display: grid; "
        "gap: 8px; }\n"
        "    li { border: 1px solid #edf0f4; border-radius: 6px; "
        "padding: 9px 10px; color: #324153; }\n"
        "    button { width: 100%; border: 1px solid #d8dee6; "
        "border-radius: 6px; padding: 9px 10px; background: #edf0f4; "
        "color: #667384; text-align: left; font: inherit; }\n"
        "    button:disabled { cursor: not-allowed; opacity: 1; }\n"
        "    @media (max-width: 700px) { .dashboard { grid-template-columns: 1fr; } }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        "  <main>\n"
        "    <h1>AsyncScholar local alpha static demo</h1>\n"
        '    <p class="intro">No-server, no-browser export of the fixed local '
        "alpha story.</p>\n"
        f"{status_strip_html}\n"
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
    grouped["Manual review status"] = list(_safe_static_demo_manual_review_lines())
    grouped["Demo review checklist"] = list(_safe_static_demo_review_checklist_lines())
    grouped["Human judgment next step"] = list(
        _safe_static_demo_human_judgment_next_step_lines()
    )
    grouped["Demo source status"] = list(_safe_static_demo_source_status_lines())
    grouped["Local demo launch"] = list(_safe_static_demo_local_launch_lines())
    grouped["Demo verification status"] = list(
        _safe_static_demo_verification_status_lines()
    )
    grouped["Backend evidence trail"] = list(
        _safe_static_demo_backend_evidence_trail_lines()
    )
    grouped["Local alpha demo runbook"] = list(_safe_static_demo_runbook_lines())
    grouped["Demo timeline"] = list(_safe_static_demo_timeline_lines())
    grouped["Confirmation queue"] = list(_safe_static_demo_confirmation_queue_lines())
    grouped["Action controls"] = list(_safe_static_demo_action_control_lines())
    grouped["Archive review status"] = list(
        _safe_static_demo_archive_review_status_lines()
    )

    return tuple(
        (heading, tuple(grouped[heading])) for heading in _STATIC_DEMO_SECTION_HEADINGS
    )


def _render_static_demo_section(heading: str, lines: tuple[str, ...]) -> str:
    if lines:
        items = "\n".join(_render_static_demo_item(line) for line in lines)
        body = f"        <ol>\n{items}\n        </ol>\n"
    else:
        body = "        <p>Metadata unavailable.</p>\n"
    return (
        "      <section>\n"
        f"        <h2>{escape(heading, quote=True)}</h2>\n"
        f"{body}"
        "      </section>"
    )


def _render_static_demo_item(line: str) -> str:
    if line.startswith("Action: "):
        body = _render_static_demo_action_control_item(line.removeprefix("Action: "))
    elif line == "Autonomous participation: no":
        body = (
            f"<span>{escape('Autonomous', quote=True)}</span> "
            f"<span>{escape('participation: no', quote=True)}</span>"
        )
    else:
        body = escape(line, quote=True)
    return f"          <li>{body}</li>"


def _render_static_demo_action_control_item(label: str) -> str:
    safe_label = escape(label, quote=True)
    return f'<button type="button" disabled aria-disabled="true">{safe_label}</button>'


def _render_static_demo_summary_status_strip(lines: tuple[str, ...]) -> str:
    items = "".join(
        f"<span>{escape(line, quote=True)}</span>"
        for line in _safe_static_demo_summary_status_strip_lines_from(lines)
    )
    return f'    <div class="summary-status-strip">{items}</div>'


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


def _safe_static_demo_timeline_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_timeline_lines()
    except Exception:
        return _STATIC_DEMO_TIMELINE_LINES
    if lines != _STATIC_DEMO_TIMELINE_LINES:
        return _STATIC_DEMO_TIMELINE_LINES
    if any(_static_demo_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_TIMELINE_LINES
    return lines


def _build_static_demo_timeline_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_TIMELINE_LINES


def _safe_static_demo_confirmation_queue_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_confirmation_queue_lines()
    except Exception:
        return _STATIC_DEMO_CONFIRMATION_QUEUE_LINES
    if lines != _STATIC_DEMO_CONFIRMATION_QUEUE_LINES:
        return _STATIC_DEMO_CONFIRMATION_QUEUE_LINES
    if any(_static_demo_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_CONFIRMATION_QUEUE_LINES
    return lines


def _build_static_demo_confirmation_queue_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_CONFIRMATION_QUEUE_LINES


def _safe_static_demo_action_control_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_action_control_lines()
    except Exception:
        return _STATIC_DEMO_ACTION_CONTROL_LINES
    if lines != _STATIC_DEMO_ACTION_CONTROL_LINES:
        return _STATIC_DEMO_ACTION_CONTROL_LINES
    if any(_static_demo_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_ACTION_CONTROL_LINES
    return lines


def _build_static_demo_action_control_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_ACTION_CONTROL_LINES


def _safe_static_demo_archive_review_status_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_archive_review_status_lines()
    except Exception:
        return _STATIC_DEMO_ARCHIVE_REVIEW_STATUS_LINES
    if lines != _STATIC_DEMO_ARCHIVE_REVIEW_STATUS_LINES:
        return _STATIC_DEMO_ARCHIVE_REVIEW_STATUS_LINES
    if any(_static_demo_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_ARCHIVE_REVIEW_STATUS_LINES
    return lines


def _build_static_demo_archive_review_status_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_ARCHIVE_REVIEW_STATUS_LINES


def _safe_static_demo_manual_review_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_manual_review_status_lines()
    except Exception:
        return _STATIC_DEMO_MANUAL_REVIEW_STATUS_LINES
    if lines != _STATIC_DEMO_MANUAL_REVIEW_STATUS_LINES:
        return _STATIC_DEMO_MANUAL_REVIEW_STATUS_LINES
    if any(_static_demo_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_MANUAL_REVIEW_STATUS_LINES
    return lines


def _build_static_demo_manual_review_status_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_MANUAL_REVIEW_STATUS_LINES


def _safe_static_demo_review_checklist_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_review_checklist_lines()
    except Exception:
        return _STATIC_DEMO_REVIEW_CHECKLIST_LINES
    if lines != _STATIC_DEMO_REVIEW_CHECKLIST_LINES:
        return _STATIC_DEMO_REVIEW_CHECKLIST_LINES
    if any(_static_demo_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_REVIEW_CHECKLIST_LINES
    return lines


def _build_static_demo_review_checklist_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_REVIEW_CHECKLIST_LINES


def _safe_static_demo_human_judgment_next_step_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_human_judgment_next_step_lines()
    except Exception:
        return _STATIC_DEMO_HUMAN_JUDGMENT_NEXT_STEP_LINES
    if lines != _STATIC_DEMO_HUMAN_JUDGMENT_NEXT_STEP_LINES:
        return _STATIC_DEMO_HUMAN_JUDGMENT_NEXT_STEP_LINES
    if any(_static_demo_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_HUMAN_JUDGMENT_NEXT_STEP_LINES
    return lines


def _build_static_demo_human_judgment_next_step_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_HUMAN_JUDGMENT_NEXT_STEP_LINES


def _safe_static_demo_source_status_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_source_status_lines()
    except Exception:
        return _STATIC_DEMO_SOURCE_STATUS_LINES
    if lines != _STATIC_DEMO_SOURCE_STATUS_LINES:
        return _STATIC_DEMO_SOURCE_STATUS_LINES
    if any(_static_demo_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_SOURCE_STATUS_LINES
    return lines


def _build_static_demo_source_status_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_SOURCE_STATUS_LINES


def _safe_static_demo_local_launch_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_local_launch_lines()
    except Exception:
        return _STATIC_DEMO_LOCAL_LAUNCH_LINES
    if lines != _STATIC_DEMO_LOCAL_LAUNCH_LINES:
        return _STATIC_DEMO_LOCAL_LAUNCH_LINES
    if any(_static_demo_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_LOCAL_LAUNCH_LINES
    return lines


def _build_static_demo_local_launch_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_LOCAL_LAUNCH_LINES


def _safe_static_demo_verification_status_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_verification_status_lines()
    except Exception:
        return _STATIC_DEMO_VERIFICATION_STATUS_LINES
    if lines != _STATIC_DEMO_VERIFICATION_STATUS_LINES:
        return _STATIC_DEMO_VERIFICATION_STATUS_LINES
    if any(_static_demo_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_VERIFICATION_STATUS_LINES
    return lines


def _build_static_demo_verification_status_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_VERIFICATION_STATUS_LINES


def _safe_static_demo_backend_evidence_trail_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_backend_evidence_trail_lines()
    except Exception:
        return _STATIC_DEMO_BACKEND_EVIDENCE_TRAIL_LINES
    if lines != _STATIC_DEMO_BACKEND_EVIDENCE_TRAIL_LINES:
        return _STATIC_DEMO_BACKEND_EVIDENCE_TRAIL_LINES
    if any(_static_demo_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_BACKEND_EVIDENCE_TRAIL_LINES
    return lines


def _build_static_demo_backend_evidence_trail_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_BACKEND_EVIDENCE_TRAIL_LINES


def _safe_static_demo_runbook_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_runbook_lines()
    except Exception:
        return _STATIC_DEMO_RUNBOOK_LINES
    if lines != _STATIC_DEMO_RUNBOOK_LINES:
        return _STATIC_DEMO_RUNBOOK_LINES
    if any(_static_demo_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_RUNBOOK_LINES
    return lines


def _build_static_demo_runbook_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_RUNBOOK_LINES


def _safe_static_demo_summary_status_strip_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_summary_status_strip_lines()
    except Exception:
        return _STATIC_DEMO_SUMMARY_STATUS_STRIP_LINES
    return _safe_static_demo_summary_status_strip_lines_from(lines)


def _build_static_demo_summary_status_strip_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_SUMMARY_STATUS_STRIP_LINES


def _safe_static_demo_summary_status_strip_lines_from(
    lines: tuple[str, ...],
) -> tuple[str, ...]:
    if lines != _STATIC_DEMO_SUMMARY_STATUS_STRIP_LINES:
        return _STATIC_DEMO_SUMMARY_STATUS_STRIP_LINES
    if any(_static_demo_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_SUMMARY_STATUS_STRIP_LINES
    return lines


def _static_demo_text_is_unsafe(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return True
    lowered = value.casefold()
    if lowered.startswith("/") or lowered.startswith("\\"):
        return True
    if (
        len(lowered) >= 3
        and lowered[0].isalpha()
        and lowered[1] == ":"
        and lowered[2] in ("/", "\\")
    ):
        return True
    return any(marker in lowered for marker in _UNSAFE_STATIC_DEMO_TEXT_MARKERS)


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
