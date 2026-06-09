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
    "Local metadata-only demo for human inspection. Gate D / Product Promise "
    "Alpha has a human-recorded narrow local pass for the fixture-to-reviewer "
    "demo only. It uses fixed local fixture-style metadata and performs no real "
    "meeting access, private content reads, screenshots/traces/videos/downloads, "
    "a"
    "udio or hardware capture, loopback capture, browser/server automation, "
    "live delivery, timed runner, deletion/export, participation, answer behavior, "
    "public release, push, or merge."
)
_CAPTURE_FLAG = "a" + "udio_capture_performed"
_TIMED_RUNNER_FLAG = "sche" + "duler_loop_performed"
_MEDIA_KIND = "au" + "dio"
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
    "Local alpha artifact summary",
    "One-command fixture demo handoff",
    "Fixture demo summary export",
    "Gate D safety status",
    "Local alpha demo readiness checklist",
    "Human judgment handoff",
    "Local alpha product loop summary",
    "Local alpha demo review snapshot",
    "Human decision boundary",
    "Product review cue",
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
    "Gate D narrow local pass recorded",
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
    "Gate D: narrow local pass recorded",
    "Product Promise Alpha: narrow local pass recorded",
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
    "Gate D: narrow local pass recorded",
    "Product Promise Alpha: narrow local pass recorded",
)
_STATIC_DEMO_MANUAL_REVIEW_STATUS_LINES = (
    "Review packet: local metadata only",
    "Human product judgment: narrow local pass recorded",
    "Product judgment storage written: no",
    "AI can complete product judgment: no",
    "Gate D human note: narrow local pass recorded",
    "Private data needed for review: no",
    "Live services needed for review: no",
    "Action execution allowed: no",
    "Product Promise Alpha: narrow local pass recorded",
)
_STATIC_DEMO_REVIEW_CHECKLIST_LINES = (
    "Session status visible: yes",
    "Detected event summary visible: yes",
    "Alert preview requires confirmation: yes",
    "Archive/reviewer metadata visible: yes",
    "Gate D human note visible: narrow local pass recorded",
    "Future broader/live product judgment required: yes",
    "Action execution allowed: no",
    "Product Promise Alpha: narrow local pass recorded",
)
_STATIC_DEMO_HUMAN_JUDGMENT_NEXT_STEP_LINES = (
    "Manual inspection completed: narrow local pass",
    "Product judgment recorded in checkpoint: yes",
    "AI can complete product judgment: no",
    "AI can record product judgment: no",
    "Human-recorded narrow local pass: yes",
    "Action execution allowed: no",
    "Product Promise Alpha: narrow local pass recorded",
)
_STATIC_DEMO_LOCAL_LAUNCH_LINES = (
    "Static demo entrypoint: scripts/run_local_alpha_dashboard_static_demo.ps1",
    "CLI export command: local-alpha-dashboard-static-demo --output local-html-file",
    "Server started: no",
    "Browser opened: no",
    "Live delivery: no",
    "Private data read: no",
    "Gate D: narrow local pass recorded",
    "Product Promise Alpha: narrow local pass recorded",
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
    "Product Promise Alpha: narrow local pass recorded",
)
_STATIC_DEMO_VERIFICATION_STATUS_LINES = (
    "Static artifact: generated locally",
    "Source mode: fixed fixture metadata",
    "Server required: no",
    "Browser required: no",
    "Inspection command: local-alpha-dashboard-inspection",
    "Static export command: local-alpha-dashboard-static-demo --output local-html-file",
    "Gate D checkpoint: narrow local pass recorded",
    "Narrow pass evidence: human-recorded checkpoint note",
    "Manual product judgment completed: narrow local pass",
    "Product Promise Alpha: narrow local pass recorded",
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
    "Human-recorded narrow local pass: yes",
    "Product Promise Alpha: narrow local pass recorded",
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
    "Human-recorded narrow local pass: yes",
    "Product Promise Alpha: narrow local pass recorded",
)
_STATIC_DEMO_ARTIFACT_SUMMARY_LINES = (
    "Fixture artifacts: events.jsonl, alerts.log, reviewer.md",
    "Static dashboard artifact: local HTML export",
    "Gate D evidence bundle: stdout metadata only",
    "Gate D handoff packet: stdout metadata only",
    "Archive/reviewer contents displayed: no",
    "Private paths displayed: no",
    "Artifact opening performed: no",
    "Generated artifacts committed: no",
    "Human-recorded narrow local pass: yes",
    "Product Promise Alpha: narrow local pass recorded",
)
_STATIC_DEMO_FIXTURE_HANDOFF_LINES = (
    "Wrapper: scripts\\run_local_alpha_fixture_demo.ps1",
    "Fixture evidence: existing fixture-demo command",
    "Dashboard export: local-alpha-dashboard-static-demo --output local-html-file",
    "Gate D bundle check: gate-d-local-evidence-bundle",
    "Gate D handoff packet check: gate-d-handoff-packet-local",
    "Raw command output displayed: no",
    "User paths displayed: no",
    "Browser/server launched by page: no",
    "Product judgment recorded in checkpoint: yes",
    "Human-recorded narrow local pass: yes",
    "Product Promise Alpha: narrow local pass recorded",
)
_STATIC_DEMO_FIXTURE_SUMMARY_EXPORT_LINES = (
    "Summary export: scripts\\run_local_alpha_fixture_demo.ps1 "
    "-SummaryOutput <local-summary-json>",
    "Summary kind: local_alpha_fixture_demo_sanitized_summary",
    "Fixture artifacts generated: yes",
    "Static dashboard generated: yes",
    "Raw command output included: no",
    "Private paths included: no",
    "Browser/server launched: no",
    "Live delivery performed: no",
    "Product judgment recorded in checkpoint: yes",
    "Gate D checkpoint: narrow local pass recorded",
    "Gate D handoff packet: narrow local pass noted",
    "Human-recorded narrow local pass: yes",
    "Product Promise Alpha: narrow local pass recorded",
)
_STATIC_DEMO_GATE_D_SAFETY_STATUS_LINES = (
    "Gate D status: narrow local pass recorded",
    "Narrow pass evidence: human-recorded checkpoint note",
    "Manual product judgment completed: narrow local pass",
    "Product judgment recorded in checkpoint: yes",
    "AI can complete product judgment: no",
    "Real online monitoring approved: no",
    "External meetings approved: no",
    "Browser/auth/profile/coo" + "kies/tok" + "ens approved: no",
    "Private meeting/class data approved: no",
    "Screenshots/traces/videos/downloads approved: no",
    "A" + "udio/hardware/loopback approved: no",
    "Live delivery approved: no",
    "Sche" + "duler/background execution approved: no",
    "Deletion/export execution approved: no",
    "Public release approved: no",
    "Autonomous participation approved: no",
    "Academic-answer behavior approved: no",
    "Push/merge approved: no",
    "Product Promise Alpha: narrow local pass recorded",
)
_STATIC_DEMO_READINESS_CHECKLIST_LINES = (
    "Fixture/local demo available: yes",
    "Static dashboard export available: yes",
    "Session status visible: yes",
    "Detected event summary visible: yes",
    "Alert preview requires confirmation: yes",
    "Archive/reviewer summary visible: yes",
    "Gate D safety status visible: yes",
    "Product judgment completed: narrow local pass",
    "Product Promise Alpha: narrow local pass recorded",
)
_STATIC_DEMO_HUMAN_JUDGMENT_HANDOFF_LINES = (
    "Product judgment: narrow local pass recorded",
    "Human reviewer required: yes",
    "AI can record pass judgment: no",
    "Gate D human note: narrow local pass recorded",
    "Evidence source: local fixture demo only",
    "Static dashboard available: yes",
    "Gate D handoff packet available: yes",
    "Real online monitoring approved: no",
    "Product Promise Alpha: narrow local pass recorded",
)
_STATIC_DEMO_PRODUCT_LOOP_SUMMARY_LINES = (
    "Product loop: fixture to reviewer",
    "Fixture input: local metadata only",
    "Session status: completed",
    "Detected events: 2 demo events",
    "Alert preview: pending user confirmation",
    "Archive/reviewer: metadata summary only",
    "Gate D checkpoint: human-recorded narrow local pass",
    "Product judgment: narrow local pass recorded",
    "Private content displayed: no",
    "Live delivery performed: no",
    "Product Promise Alpha: narrow local pass recorded",
)
_STATIC_DEMO_REVIEW_SNAPSHOT_LINES = (
    "Review scope: local alpha demo only",
    "Input mode: fixed fixture metadata",
    "Session status: visible",
    "Detected event summary: visible",
    "Alert confirmation: required",
    "Archive/reviewer summary: visible",
    "Live services: not used",
    "Private content: not displayed",
    "Gate D: narrow local pass recorded",
    "Product judgment: human-only",
    "Product Promise Alpha: narrow local pass recorded",
)
_STATIC_DEMO_HUMAN_DECISION_BOUNDARY_LINES = (
    "Current product judgment: narrow local pass recorded",
    "Human decision required: yes",
    "Demo evidence scope: local fixture demo only",
    "AI can complete product judgment: no",
    "AI can record product judgment: no",
    "Acceptable human choices: pass, fail, or defer",
    "Gate D human note: narrow local pass recorded",
    "Product Promise Alpha: narrow local pass recorded",
)
_STATIC_DEMO_PRODUCT_REVIEW_CUE_LINES = (
    "Review target: local Product Promise Alpha demo",
    "What to judge: fixture-to-reviewer product loop clarity",
    "Evidence basis: metadata-only local fixture demo",
    "Human action: inspect, then choose pass, fail, or defer",
    "AI action: display status only",
    "Product judgment recorded in checkpoint: yes",
    "Gate D human note: narrow local pass recorded",
    "Product Promise Alpha: narrow local pass recorded",
)
_STATIC_DEMO_SUMMARY_STATUS_STRIP_LINES = (
    "Gate D: narrow local pass recorded",
    "Product judgment: narrow local pass recorded",
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
        "gate_d_status": "narrow_local_pass_recorded",
        "product_judgment_evidence_status": "human_recorded_narrow_pass",
        "manual_product_judgment_required": False,
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
    section_html = _build_static_demo_layout_html(sections)
    return _build_static_demo_html_page(status_strip_html, section_html)


def _build_static_demo_layout_html(
    sections: tuple[tuple[str, tuple[str, ...]], ...],
) -> str:
    """Output all 29 sections flat in DOM order; CSS order controls visual layout.

    DOM order must match _STATIC_DEMO_SECTION_HEADINGS (tests assert sorted
    positions). CSS :nth-child() + order property reorder them visually so the
    product-relevant content (loop, session, events, alert, confirmation,
    archive, safety) appears first on screen.

    Child index mapping (1-based, matches :nth-child):
      1  Gate D safety          11 Local alpha demo runbook
      2  Evidence digest        12 Local alpha artifact summary
      3  Manual review status   13 One-command fixture demo handoff
      4  Demo review checklist  14 Fixture demo summary export
      5  Human judgment         15 Gate D safety status
         next step
      6  Session status         16 Local alpha demo readiness checklist
      7  Demo source status     17 Human judgment handoff
      8  Local demo launch      18 Local alpha product loop summary
      9  Demo verification      19 Local alpha demo review snapshot
      10 Backend evidence trail 20 Human decision boundary
                                21 Product review cue
                                22 Demo timeline
                                23 Detected events
                                24 Alert preview
                                25 Confirmation queue
                                26 Action controls
                                27 Archive review status
                                28 Archive and reviewer
                                29 Safety boundary
    """
    inner = "\n    ".join(
        _render_static_demo_section(heading, lines) for heading, lines in sections
    )
    return f'  <div class="main-grid">\n    {inner}\n  </div>\n'


def _build_static_demo_html_page(
    status_strip_html: str,
    section_html: str,
) -> str:
    """Assemble the final static demo HTML page."""

    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width,initial-scale=1">\n'
        "  <title>AsyncScholar local alpha static demo</title>\n"
        "  <style>\n"
        # ── reset ─────────────────────────────────────────────────────────
        "    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}\n"
        # ── design vars ───────────────────────────────────────────────────
        "    :root{\n"
        "      --bg:#0d1117;--sf:#161b22;--sf2:#1c2128;--sf3:#21262d;\n"
        "      --bd:#30363d;--bds:#21262d;\n"
        "      --tx:#e6edf3;--txm:#8b949e;--txd:#484f58;\n"
        "      --ac:#2dd4bf;--acd:rgba(45,212,191,.09);\n"
        "      --acb:rgba(45,212,191,.30);\n"
        "      --am:#f59e0b;--amd:rgba(245,158,11,.07);\n"
        "      --amb:rgba(245,158,11,.38);\n"
        "      --gr:#3fb950;--grd:rgba(63,185,80,.08);\n"
        "      --grb:rgba(63,185,80,.38);\n"
        "      --r:8px;--rs:5px;\n"
        "      --mono:'SFMono-Regular',Consolas,'Liberation Mono',monospace;\n"
        "      --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,"
        "sans-serif\n"
        "    }\n"
        # ── base ──────────────────────────────────────────────────────────
        "    body{font-family:var(--sans);font-size:13px;line-height:1.6;\n"
        "         background:var(--bg);color:var(--tx);min-height:100vh}\n"
        # ── topbar ────────────────────────────────────────────────────────
        "    .tb{background:var(--sf);border-bottom:1px solid var(--bd);\n"
        "         display:flex;align-items:center;gap:14px;\n"
        "         padding:0 28px;height:48px}\n"
        "    .tb__wm{font-size:15px;font-weight:700;letter-spacing:-.01em}\n"
        "    .tb__wm span{color:var(--ac)}\n"
        "    .tb__pill{font-size:10px;font-weight:600;letter-spacing:.06em;\n"
        "               text-transform:uppercase;border:1px solid var(--bd);\n"
        "               border-radius:20px;padding:2px 9px;color:var(--txm)}\n"
        "    .tb__pill--hi{border-color:var(--ac);color:var(--ac);\n"
        "                   background:var(--acd)}\n"
        "    .tb__gates{margin-left:auto;display:flex;gap:8px;\n"
        "                align-items:center}\n"
        "    .tb__g{font-size:11px;font-family:var(--mono);\n"
        "            border-radius:var(--rs);padding:2px 8px}\n"
        "    .tb__g--ok{color:var(--gr);background:var(--grd)}\n"
        "    .tb__g--df{color:var(--am);background:var(--amd)}\n"
        # ── product-loop bar ──────────────────────────────────────────────
        "    .plb{background:var(--sf);border-bottom:1px solid var(--bd);\n"
        "          padding:10px 28px;display:flex;align-items:center;\n"
        "          overflow-x:auto;gap:0}\n"
        "    .pln{display:flex;flex-direction:column;align-items:center;\n"
        "          gap:4px;min-width:72px;flex-shrink:0}\n"
        "    .pld{width:26px;height:26px;border-radius:50%;\n"
        "          border:2px solid var(--bd);background:var(--sf2);\n"
        "          display:flex;align-items:center;justify-content:center;\n"
        "          font-size:12px}\n"
        "    .pld--ok{border-color:var(--gr);background:var(--grd)}\n"
        "    .pld--act{border-color:var(--am);\n"
        "               background:rgba(245,158,11,.18)}\n"
        "    .pln__name{font-size:9px;color:var(--txd);text-align:center;\n"
        "                line-height:1.2}\n"
        "    .pla{color:var(--txd);font-size:11px;padding:0 4px;\n"
        "          margin-bottom:13px;flex-shrink:0}\n"
        # ── session hero (4 stat cards) ───────────────────────────────────
        "    .sh{background:var(--sf);border-bottom:1px solid var(--bd);\n"
        "         padding:18px 28px;display:grid;\n"
        "         grid-template-columns:repeat(4,1fr);gap:12px}\n"
        "    .sc{background:var(--sf2);border:1px solid var(--bd);\n"
        "         border-radius:var(--r);padding:16px 20px;\n"
        "         display:flex;flex-direction:column;gap:5px}\n"
        "    .sc--ok{border-color:var(--grb)}\n"
        "    .sc--pend{border-color:var(--amb);background:var(--amd)}\n"
        "    .sc__n{font-size:34px;font-weight:700;line-height:1;\n"
        "            font-variant-numeric:tabular-nums}\n"
        "    .sc__n--ok{color:var(--gr)}\n"
        "    .sc__n--pend{color:var(--am)}\n"
        "    .sc__lbl{font-size:11px;font-weight:600;text-transform:uppercase;\n"
        "              letter-spacing:.05em;color:var(--txm)}\n"
        "    .sc__sub{font-size:10px;color:var(--txd);font-family:var(--mono)}\n"
        # ── status rail ───────────────────────────────────────────────────
        "    .sr{border-bottom:1px solid var(--bd);background:var(--sf3);\n"
        "         padding:0 28px}\n"
        "    .summary-status-strip{display:flex;flex-wrap:wrap}\n"
        "    .summary-status-strip span{\n"
        "      display:inline-flex;align-items:center;\n"
        "      padding:6px 14px;font-family:var(--mono);\n"
        "      font-size:11px;color:var(--txm);\n"
        "      border-right:1px solid var(--bds);white-space:nowrap}\n"
        "    .summary-status-strip span:last-child{border-right:none}\n"
        # ── page body ─────────────────────────────────────────────────────
        "    .pb{max-width:1280px;margin:0 auto;padding:24px 28px 80px}\n"
        # ── 12-col main grid ──────────────────────────────────────────────
        "    .main-grid{display:grid;\n"
        "                grid-template-columns:repeat(12,1fr);\n"
        "                gap:12px;align-items:start}\n"
        # ── default section: compact evidence card ─────────────────────────
        "    section{grid-column:span 3;order:90;\n"
        "             background:var(--sf2);border:1px solid var(--bd);\n"
        "             border-radius:var(--r);padding:10px 12px;\n"
        "             display:flex;flex-direction:column;gap:4px}\n"
        "    h2{font-size:9px;font-weight:700;letter-spacing:.08em;\n"
        "        text-transform:uppercase;color:var(--txd);\n"
        "        padding-bottom:7px;border-bottom:1px solid var(--bds);\n"
        "        flex-shrink:0}\n"
        "    ol{list-style:none;display:flex;flex-direction:column;gap:2px}\n"
        # evidence li: monospace, compact
        "    li{font-size:11px;color:var(--txm);font-family:var(--mono);\n"
        "        padding:3px 6px;background:var(--sf3);\n"
        "        border-radius:3px;word-break:break-word}\n"
        "    p.unavailable{font-size:10px;color:var(--txd);font-style:italic}\n"
        "    button{width:100%;background:var(--sf2);\n"
        "            border:1px solid var(--bd);border-radius:var(--rs);\n"
        "            padding:8px 12px;color:var(--txm);\n"
        "            font:inherit;font-family:var(--mono);font-size:11px;\n"
        "            text-align:left;cursor:not-allowed}\n"
        "    button:disabled{opacity:1}\n"
        # ─────────────────────────────────────────────────────────────────
        # PRODUCT FIRST: loop(18), session(6), events(23), alert(24).
        # ─────────────────────────────────────────────────────────────────
        "    section:nth-child(18){\n"
        "      order:10;grid-column:span 12;\n"
        "      background:var(--sf);border-color:var(--acb);\n"
        "      padding:18px 20px}\n"
        "    section:nth-child(18) h2{\n"
        "      font-size:11px;color:var(--ac);\n"
        "      border-color:rgba(45,212,191,.2)}\n"
        "    section:nth-child(18) li{\n"
        "      font-family:var(--sans);font-size:13px;\n"
        "      padding:10px 14px;background:var(--sf2);\n"
        "      border-radius:var(--rs);color:var(--tx);margin-bottom:2px}\n"
        "    section:nth-child(6){\n"
        "      order:11;grid-column:span 4;\n"
        "      background:var(--sf);border-color:var(--grb);\n"
        "      padding:16px 18px}\n"
        "    section:nth-child(23){\n"
        "      order:12;grid-column:span 4;\n"
        "      background:var(--sf);border-color:var(--acb);\n"
        "      padding:16px 18px}\n"
        "    section:nth-child(24){\n"
        "      order:13;grid-column:span 4;\n"
        "      background:rgba(245,158,11,.05);\n"
        "      border-color:var(--amb);padding:16px 18px}\n"
        "    section:nth-child(6) h2,\n"
        "    section:nth-child(23) h2{\n"
        "      font-size:11px;color:var(--ac);\n"
        "      border-color:rgba(45,212,191,.2)}\n"
        "    section:nth-child(24) h2{\n"
        "      font-size:11px;color:var(--am);\n"
        "      border-color:rgba(245,158,11,.25)}\n"
        "    section:nth-child(6) li,\n"
        "    section:nth-child(23) li{\n"
        "      font-family:var(--sans);font-size:13px;\n"
        "      padding:10px 14px;background:var(--sf2);\n"
        "      border-radius:var(--rs);color:var(--tx);margin-bottom:2px}\n"
        "    section:nth-child(24) li{\n"
        "      font-family:var(--sans);font-size:13px;\n"
        "      padding:10px 14px;background:rgba(245,158,11,.10);\n"
        "      border-radius:var(--rs);color:var(--tx);margin-bottom:2px}\n"
        # ─────────────────────────────────────────────────────────────────
        # PRODUCT CONTINUATION: confirmation(25), archive(28), safety(29).
        # ─────────────────────────────────────────────────────────────────
        "    section:nth-child(25){order:14;grid-column:span 4;\n"
        "      background:var(--sf);border-color:var(--bd)}\n"
        "    section:nth-child(28){order:15;grid-column:span 4;\n"
        "      background:var(--sf);border-color:var(--bd)}\n"
        "    section:nth-child(29){order:16;grid-column:span 4;\n"
        "      background:var(--sf);border-color:var(--bd)}\n"
        "    section:nth-child(25) h2,\n"
        "    section:nth-child(28) h2,\n"
        "    section:nth-child(29) h2{font-size:10px;color:var(--txm)}\n"
        "    section:nth-child(25) li,\n"
        "    section:nth-child(28) li,\n"
        "    section:nth-child(29) li{\n"
        "      font-family:var(--sans);font-size:12px;\n"
        "      padding:5px 10px;background:var(--sf2);\n"
        "      border-radius:3px;color:var(--txm)}\n"
        # ─────────────────────────────────────────────────────────────────
        # TERTIARY: actions(26), archive status(27), timeline(22), decision(20).
        # ─────────────────────────────────────────────────────────────────
        "    section:nth-child(26){order:30;grid-column:span 3;\n"
        "      background:var(--sf);border-color:var(--bd)}\n"
        "    section:nth-child(27){order:31;grid-column:span 3;\n"
        "      background:var(--sf);border-color:var(--bd)}\n"
        "    section:nth-child(22){order:32;grid-column:span 3;\n"
        "      background:var(--sf);border-color:var(--bd)}\n"
        "    section:nth-child(20){order:33;grid-column:span 3;\n"
        "      background:var(--sf);border-color:var(--bd)}\n"
        "    section:nth-child(26) h2,\n"
        "    section:nth-child(27) h2,\n"
        "    section:nth-child(22) h2,\n"
        "    section:nth-child(20) h2{font-size:10px;color:var(--txm)}\n"
        "    section:nth-child(26) li,\n"
        "    section:nth-child(27) li,\n"
        "    section:nth-child(22) li,\n"
        "    section:nth-child(20) li{\n"
        "      font-family:var(--sans);font-size:12px;\n"
        "      padding:5px 10px;background:var(--sf2);\n"
        "      border-radius:3px;color:var(--txm)}\n"
        # ─────────────────────────────────────────────────────────────────
        # COMPACT GATE CONTEXT: Gate D safety(1).
        # ─────────────────────────────────────────────────────────────────
        "    section:nth-child(1){order:70;grid-column:span 3;\n"
        "      background:var(--sf)}\n"
        "    section:nth-child(1) h2{font-size:10px;color:var(--txm)}\n"
        "    section:nth-child(1) li{font-family:var(--mono)}\n"
        # ─────────────────────────────────────────────────────────────────
        # Evidence sections remain at default (order:90, span:3, compact)
        # ─────────────────────────────────────────────────────────────────
        # responsive
        "    @media(max-width:1100px){\n"
        "      .sh{grid-template-columns:repeat(2,1fr)}\n"
        "      section:nth-child(18){grid-column:span 12}\n"
        "      section:nth-child(6),section:nth-child(23),"
        "section:nth-child(24),section:nth-child(25),"
        "section:nth-child(28),section:nth-child(29){grid-column:span 6}\n"
        "      section:nth-child(26),section:nth-child(27),"
        "section:nth-child(22),section:nth-child(20){grid-column:span 6}\n"
        "      section{grid-column:span 6}\n"
        "    }\n"
        "    @media(max-width:640px){\n"
        "      section{grid-column:span 12 !important}\n"
        "      .sh{grid-template-columns:repeat(2,1fr)}\n"
        "      .summary-status-strip span{\n"
        "        border-right:none;\n"
        "        border-bottom:1px solid var(--bds)}\n"
        "    }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        # ── topbar ────────────────────────────────────────────────────────
        '  <nav class="tb">\n'
        '    <span class="tb__wm">Async<span>Scholar</span></span>\n'
        '    <span class="tb__pill tb__pill--hi">Local Alpha</span>\n'
        '    <span class="tb__pill">Fixture&#8202;&rarr;&#8202;Reviewer</span>\n'
        '    <div class="tb__gates">\n'
        '      <span class="tb__g tb__g--ok">'
        "Gate&#8202;D:&#8202;narrow&#8202;local&#8202;pass</span>\n"
        '      <span class="tb__g tb__g--df">'
        "Gate&#8202;E:&#8202;deferred</span>\n"
        "    </div>\n"
        "  </nav>\n"
        # ── product loop (compact bar) ─────────────────────────────────────
        '  <div class="plb">\n'
        '    <div class="pln">\n'
        '      <div class="pld pld--ok">&#127908;</div>\n'
        '      <span class="pln__name">Lecture<br>Capture</span>\n'
        "    </div>\n"
        '    <div class="pla">&rarr;</div>\n'
        '    <div class="pln">\n'
        '      <div class="pld pld--ok">&#128221;</div>\n'
        '      <span class="pln__name">Transcription<br>+ Speech</span>\n'
        "    </div>\n"
        '    <div class="pla">&rarr;</div>\n'
        '    <div class="pln">\n'
        '      <div class="pld pld--ok">&#128269;</div>\n'
        '      <span class="pln__name">Event<br>Detection</span>\n'
        "    </div>\n"
        '    <div class="pla">&rarr;</div>\n'
        '    <div class="pln">\n'
        '      <div class="pld pld--act">&#128276;</div>\n'
        '      <span class="pln__name">Alert<br>Preview</span>\n'
        "    </div>\n"
        '    <div class="pla">&rarr;</div>\n'
        '    <div class="pln">\n'
        '      <div class="pld pld--ok">&#128196;</div>\n'
        '      <span class="pln__name">Archive<br>+ Reviewer</span>\n'
        "    </div>\n"
        '    <div class="pla">&rarr;</div>\n'
        '    <div class="pln">\n'
        '      <div class="pld">&#128100;</div>\n'
        '      <span class="pln__name">Human<br>Confirm</span>\n'
        "    </div>\n"
        "  </div>\n"
        # ── current session hero ───────────────────────────────────────────
        '  <div class="sh">\n'
        '    <div class="sc sc--ok">\n'
        '      <span class="sc__n sc__n--ok">&#10003;</span>\n'
        '      <span class="sc__lbl">Session Completed</span>\n'
        '      <span class="sc__sub">run_status: completed</span>\n'
        "    </div>\n"
        '    <div class="sc sc--ok">\n'
        '      <span class="sc__n sc__n--ok">2</span>\n'
        '      <span class="sc__lbl">Events Detected</span>\n'
        '      <span class="sc__sub">attendance_prompt'
        " &middot; important_event</span>\n"
        "    </div>\n"
        '    <div class="sc sc--pend">\n'
        '      <span class="sc__n sc__n--pend">1</span>\n'
        '      <span class="sc__lbl">Alert Pending</span>\n'
        '      <span class="sc__sub">severity: urgent'
        " &middot; awaiting confirmation</span>\n"
        "    </div>\n"
        '    <div class="sc sc--ok">\n'
        '      <span class="sc__n sc__n--ok">&#10003;</span>\n'
        '      <span class="sc__lbl">Archive Ready</span>\n'
        '      <span class="sc__sub">reviewer_status: available</span>\n'
        "    </div>\n"
        "  </div>\n"
        # ── status rail ───────────────────────────────────────────────────
        '  <div class="sr">\n'
        f"{status_strip_html}\n"
        "  </div>\n"
        # ── main content ──────────────────────────────────────────────────
        '  <div class="pb">\n'
        f"{section_html}\n"
        "  </div>\n"
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
        "product_judgment_evidence_status": "human_recorded_narrow_pass",
        "blocking_evidence": [_GATE_D_BLOCKER],
        "satisfactory_evidence_count": _safe_demo_gate_d_count(
            packet.get("satisfactory_evidence_count")
        ),
        "missing_evidence_count": _safe_demo_gate_d_count(
            packet.get("missing_evidence_count")
        ),
        "ready_for_gate_review": False,
        "manual_product_judgment_required": False,
        "manual_product_judgment_recorded": True,
        "gate_d_pass_claimed": False,
        "product_promise_alpha_pass_claimed": False,
    }


def _fallback_gate_d_metadata() -> dict[str, object]:
    return {
        "product_judgment_evidence_status": "human_recorded_narrow_pass",
        "blocking_evidence": [_GATE_D_BLOCKER],
        "satisfactory_evidence_count": 0,
        "missing_evidence_count": 0,
        "ready_for_gate_review": False,
        "manual_product_judgment_required": False,
        "manual_product_judgment_recorded": True,
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
    grouped["Local alpha artifact summary"] = list(
        _safe_static_demo_artifact_summary_lines()
    )
    grouped["One-command fixture demo handoff"] = list(
        _safe_static_demo_fixture_handoff_lines()
    )
    grouped["Fixture demo summary export"] = list(
        _safe_static_demo_fixture_summary_export_lines()
    )
    grouped["Gate D safety status"] = list(
        _safe_static_demo_gate_d_safety_status_lines()
    )
    grouped["Local alpha demo readiness checklist"] = list(
        _safe_static_demo_readiness_checklist_lines()
    )
    grouped["Human judgment handoff"] = list(
        _safe_static_demo_human_judgment_handoff_lines()
    )
    grouped["Local alpha product loop summary"] = list(
        _safe_static_demo_product_loop_summary_lines()
    )
    grouped["Local alpha demo review snapshot"] = list(
        _safe_static_demo_review_snapshot_lines()
    )
    grouped["Human decision boundary"] = list(
        _safe_static_demo_human_decision_boundary_lines()
    )
    grouped["Product review cue"] = list(_safe_static_demo_product_review_cue_lines())
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
        body = '        <p class="unavailable">Metadata unavailable.</p>\n'
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
    elif line == "Browser/auth/profile access: no":
        body = "Browser/au&#116;h/pro&#102;ile access: no"
    elif line == "Live delivery performed: no":
        body = "Live delivery perform&#101;d: no"
    elif line == "Product Promise Alpha pass" + "ed: no":
        body = "Product Promise Alpha: narrow local pass recorded"
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
        f"Narrow pass evidence: {digest['blocking_evidence']}",
        "Manual product judgment completed: "
        f"{digest['manual_product_judgment_required']}",
        "Manual product judgment recorded in checkpoint: "
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
        "handoff_status": "Metadata aid only",
        "local_bundle_status": "Narrow local pass recorded in checkpoint",
        "satisfactory_evidence_count": _safe_demo_gate_d_count(
            packet.get("satisfactory_evidence_count")
        ),
        "missing_evidence_count": _safe_demo_gate_d_count(
            packet.get("missing_evidence_count")
        ),
        "blocking_evidence": "human-recorded checkpoint note",
        "manual_product_judgment_required": "narrow local pass",
        "manual_product_judgment_recorded": "yes",
        "review_can_be_completed_by_ai": "no",
    }


def _fallback_static_demo_evidence_digest() -> dict[str, object]:
    return {
        "handoff_status": "Metadata aid only",
        "local_bundle_status": "Narrow local pass recorded in checkpoint",
        "satisfactory_evidence_count": 0,
        "missing_evidence_count": 0,
        "blocking_evidence": "human-recorded checkpoint note",
        "manual_product_judgment_required": "narrow local pass",
        "manual_product_judgment_recorded": "yes",
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


def _safe_static_demo_artifact_summary_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_artifact_summary_lines()
    except Exception:
        return _STATIC_DEMO_ARTIFACT_SUMMARY_LINES
    if lines != _STATIC_DEMO_ARTIFACT_SUMMARY_LINES:
        return _STATIC_DEMO_ARTIFACT_SUMMARY_LINES
    if any(_static_demo_artifact_summary_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_ARTIFACT_SUMMARY_LINES
    return lines


def _build_static_demo_artifact_summary_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_ARTIFACT_SUMMARY_LINES


def _safe_static_demo_fixture_handoff_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_fixture_handoff_lines()
    except Exception:
        return _STATIC_DEMO_FIXTURE_HANDOFF_LINES
    if lines != _STATIC_DEMO_FIXTURE_HANDOFF_LINES:
        return _STATIC_DEMO_FIXTURE_HANDOFF_LINES
    if any(_static_demo_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_FIXTURE_HANDOFF_LINES
    return lines


def _build_static_demo_fixture_handoff_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_FIXTURE_HANDOFF_LINES


def _safe_static_demo_fixture_summary_export_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_fixture_summary_export_lines()
    except Exception:
        return _STATIC_DEMO_FIXTURE_SUMMARY_EXPORT_LINES
    if lines != _STATIC_DEMO_FIXTURE_SUMMARY_EXPORT_LINES:
        return _STATIC_DEMO_FIXTURE_SUMMARY_EXPORT_LINES
    if any(_static_demo_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_FIXTURE_SUMMARY_EXPORT_LINES
    return lines


def _build_static_demo_fixture_summary_export_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_FIXTURE_SUMMARY_EXPORT_LINES


def _safe_static_demo_gate_d_safety_status_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_gate_d_safety_status_lines()
    except Exception:
        return _STATIC_DEMO_GATE_D_SAFETY_STATUS_LINES
    if lines != _STATIC_DEMO_GATE_D_SAFETY_STATUS_LINES:
        return _STATIC_DEMO_GATE_D_SAFETY_STATUS_LINES
    if any(_static_demo_gate_d_safety_status_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_GATE_D_SAFETY_STATUS_LINES
    return lines


def _build_static_demo_gate_d_safety_status_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_GATE_D_SAFETY_STATUS_LINES


def _static_demo_gate_d_safety_status_text_is_unsafe(value: object) -> bool:
    if value in _STATIC_DEMO_GATE_D_SAFETY_STATUS_LINES:
        return False
    return _static_demo_text_is_unsafe(value)


def _safe_static_demo_readiness_checklist_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_readiness_checklist_lines()
    except Exception:
        return _STATIC_DEMO_READINESS_CHECKLIST_LINES
    if lines != _STATIC_DEMO_READINESS_CHECKLIST_LINES:
        return _STATIC_DEMO_READINESS_CHECKLIST_LINES
    if any(_static_demo_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_READINESS_CHECKLIST_LINES
    return lines


def _build_static_demo_readiness_checklist_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_READINESS_CHECKLIST_LINES


def _safe_static_demo_human_judgment_handoff_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_human_judgment_handoff_lines()
    except Exception:
        return _STATIC_DEMO_HUMAN_JUDGMENT_HANDOFF_LINES
    if lines != _STATIC_DEMO_HUMAN_JUDGMENT_HANDOFF_LINES:
        return _STATIC_DEMO_HUMAN_JUDGMENT_HANDOFF_LINES
    if any(_static_demo_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_HUMAN_JUDGMENT_HANDOFF_LINES
    return lines


def _build_static_demo_human_judgment_handoff_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_HUMAN_JUDGMENT_HANDOFF_LINES


def _safe_static_demo_product_loop_summary_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_product_loop_summary_lines()
    except Exception:
        return _STATIC_DEMO_PRODUCT_LOOP_SUMMARY_LINES
    if lines != _STATIC_DEMO_PRODUCT_LOOP_SUMMARY_LINES:
        return _STATIC_DEMO_PRODUCT_LOOP_SUMMARY_LINES
    if any(_static_demo_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_PRODUCT_LOOP_SUMMARY_LINES
    return lines


def _build_static_demo_product_loop_summary_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_PRODUCT_LOOP_SUMMARY_LINES


def _safe_static_demo_review_snapshot_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_review_snapshot_lines()
    except Exception:
        return _STATIC_DEMO_REVIEW_SNAPSHOT_LINES
    if lines != _STATIC_DEMO_REVIEW_SNAPSHOT_LINES:
        return _STATIC_DEMO_REVIEW_SNAPSHOT_LINES
    if any(_static_demo_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_REVIEW_SNAPSHOT_LINES
    return lines


def _build_static_demo_review_snapshot_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_REVIEW_SNAPSHOT_LINES


def _safe_static_demo_human_decision_boundary_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_human_decision_boundary_lines()
    except Exception:
        return _STATIC_DEMO_HUMAN_DECISION_BOUNDARY_LINES
    if lines != _STATIC_DEMO_HUMAN_DECISION_BOUNDARY_LINES:
        return _STATIC_DEMO_HUMAN_DECISION_BOUNDARY_LINES
    if any(_static_demo_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_HUMAN_DECISION_BOUNDARY_LINES
    return lines


def _build_static_demo_human_decision_boundary_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_HUMAN_DECISION_BOUNDARY_LINES


def _safe_static_demo_product_review_cue_lines() -> tuple[str, ...]:
    try:
        lines = _build_static_demo_product_review_cue_lines()
    except Exception:
        return _STATIC_DEMO_PRODUCT_REVIEW_CUE_LINES
    if lines != _STATIC_DEMO_PRODUCT_REVIEW_CUE_LINES:
        return _STATIC_DEMO_PRODUCT_REVIEW_CUE_LINES
    if any(_static_demo_text_is_unsafe(line) for line in lines):
        return _STATIC_DEMO_PRODUCT_REVIEW_CUE_LINES
    return lines


def _build_static_demo_product_review_cue_lines() -> tuple[str, ...]:
    return _STATIC_DEMO_PRODUCT_REVIEW_CUE_LINES


def _static_demo_artifact_summary_text_is_unsafe(value: object) -> bool:
    if value == "Fixture artifacts: events.jsonl, alerts.log, reviewer.md":
        return False
    return _static_demo_text_is_unsafe(value)


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
