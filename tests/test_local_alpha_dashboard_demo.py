from __future__ import annotations

import importlib
import inspect
import json
import re
import subprocess
import sys
import textwrap
from html import unescape

import pytest

PRIVATE_VALUES = (
    "Good morning, everyone. I am going to take attendance",
    "https://meet.example.edu/class-room?token=private",
    r"C:\Users\student\data\sessions\fixture\events.jsonl",
    r"C:\private\lecture.wav",
    r"C:\private\lecture.mp4",
    "secret.env",
    "cookie-value",
    "token-value",
    "auth-state",
    "browser profile",
    "Traceback (most recent call last)",
    r"C:\models\private-model.bin",
    r"C:\generated\clip.png",
)
STATIC_DEMO_RUNBOOK_LINES = (
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
STATIC_DEMO_ARTIFACT_SUMMARY_LINES = (
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
STATIC_DEMO_FIXTURE_HANDOFF_LINES = (
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
STATIC_DEMO_FIXTURE_SUMMARY_EXPORT_LINES = (
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
STATIC_DEMO_GATE_D_SAFETY_STATUS_LINES = (
    "Gate D status: narrow local pass recorded",
    "Narrow pass evidence: human-recorded checkpoint note",
    "Manual product judgment completed: narrow local pass",
    "Product judgment recorded in checkpoint: yes",
    "AI can complete product judgment: no",
    "Real online monitoring approved: no",
    "External meetings approved: no",
    "Browser/auth/profile/cookies/tokens approved: no",
    "Private meeting/class data approved: no",
    "Screenshots/traces/videos/downloads approved: no",
    "Audio/hardware/loopback approved: no",
    "Live delivery approved: no",
    "Scheduler/background execution approved: no",
    "Deletion/export execution approved: no",
    "Public release approved: no",
    "Autonomous participation approved: no",
    "Academic-answer behavior approved: no",
    "Push/merge approved: no",
    "Product Promise Alpha: narrow local pass recorded",
)
STATIC_DEMO_READINESS_CHECKLIST_LINES = (
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
STATIC_DEMO_HUMAN_JUDGMENT_HANDOFF_LINES = (
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
STATIC_DEMO_PRODUCT_LOOP_SUMMARY_LINES = (
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
STATIC_DEMO_REVIEW_SNAPSHOT_LINES = (
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
STATIC_DEMO_HUMAN_DECISION_BOUNDARY_LINES = (
    "Current product judgment: narrow local pass recorded",
    "Human decision required: yes",
    "Demo evidence scope: local fixture demo only",
    "AI can complete product judgment: no",
    "AI can record product judgment: no",
    "Acceptable human choices: pass, fail, or defer",
    "Gate D human note: narrow local pass recorded",
    "Product Promise Alpha: narrow local pass recorded",
)
STATIC_DEMO_PRODUCT_REVIEW_CUE_LINES = (
    "Review target: local Product Promise Alpha demo",
    "What to judge: fixture-to-reviewer product loop clarity",
    "Evidence basis: metadata-only local fixture demo",
    "Human action: inspect, then choose pass, fail, or defer",
    "AI action: display status only",
    "Product judgment recorded in checkpoint: yes",
    "Gate D human note: narrow local pass recorded",
    "Product Promise Alpha: narrow local pass recorded",
)


def test_dashboard_demo_module_import_is_safe() -> None:
    code = textwrap.dedent(
        """
        import importlib
        import json
        import sys

        before = set(sys.modules)
        importlib.import_module("async_scholar.ui.local_alpha_dashboard_demo")
        loaded = set(sys.modules) - before
        prefixes = (
            "fastapi",
            "nicegui",
            "async_scholar.demo",
            "async_scholar.rules",
            "async_scholar.artifacts",
            "async_scholar.alert_dispatch",
            "async_scholar.desktop_notifier",
            "async_scholar.telegram_notifier",
            "async_scholar.scheduler",
            "async_scholar.browser",
            "async_scholar.audio",
            "async_scholar.stt",
        )
        forbidden = sorted(
            name
            for name in loaded
            if any(
                name == prefix or name.startswith(f"{prefix}.")
                for prefix in prefixes
            )
        )
        print(json.dumps(forbidden))
        raise SystemExit(bool(forbidden))
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads(completed.stdout) == []

    source = inspect.getsource(_demo_module()).casefold()
    for forbidden in (
        "async_scholar.demo",
        "run_fixture_demo",
        "load_transcript",
        "data/",
        "data\\",
        ".env",
        "cookie",
        "token",
        "playwright",
        "selenium",
        "audio",
        "stt",
        "vad",
        "scheduler",
        "telegram",
        "desktop_notifier",
    ):
        assert forbidden not in source


def test_ui_package_lazy_export_for_dashboard_demo_is_safe() -> None:
    code = textwrap.dedent(
        """
        import importlib
        import json
        import sys

        package = importlib.import_module("async_scholar.ui")
        assert "build_local_alpha_dashboard_demo_dry_run" in package.__all__
        assert "build_local_alpha_dashboard_inspection_summary" in package.__all__
        assert "build_local_alpha_dashboard_static_demo_html" in package.__all__
        before = set(sys.modules)
        build = package.build_local_alpha_dashboard_demo_dry_run
        inspect_summary = package.build_local_alpha_dashboard_inspection_summary
        build_static = package.build_local_alpha_dashboard_static_demo_html
        loaded = set(sys.modules) - before
        prefixes = ("fastapi", "nicegui", "async_scholar.demo", "async_scholar.audio")
        forbidden = sorted(
            name
            for name in loaded
            if any(
                name == prefix or name.startswith(f"{prefix}.")
                for prefix in prefixes
            )
        )
        print(
            json.dumps(
                {
                    "callable": callable(build),
                    "inspection_callable": callable(inspect_summary),
                    "static_callable": callable(build_static),
                    "forbidden": forbidden,
                }
            )
        )
        raise SystemExit(bool(forbidden))
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads(completed.stdout) == {
        "callable": True,
        "inspection_callable": True,
        "static_callable": True,
        "forbidden": [],
    }


def test_build_demo_sources_are_deterministic_and_metadata_only() -> None:
    demo = _demo_module()
    first = demo.build_local_alpha_dashboard_demo_sources()
    second = demo.build_local_alpha_dashboard_demo_sources()

    assert first == second
    assert first.session_status.status()["run_status"] == "completed"
    assert first.session_status.status()["source_kind"] == "fixture_demo"
    assert first.session_status.status()["segment_count"] == 5
    assert first.session_status.status()["event_count"] == 2
    assert first.events()[0]["event_type"] == "attendance_prompt"
    assert first.alerts.alerts()[0]["status"] == "pending"
    assert first.alerts.alerts()[0]["confirmation_required"] is True
    assert first.archive.items()[0]["title"] == "Local archive summary"
    assert (
        first.gate_d["product_judgment_evidence_status"] == "human_recorded_narrow_pass"
    )
    assert first.gate_d["blocking_evidence"] == ["product_judgment_evidence"]
    assert first.gate_d["satisfactory_evidence_count"] == 9
    assert first.gate_d["missing_evidence_count"] == 0
    assert first.gate_d["ready_for_gate_review"] is False
    assert first.gate_d["manual_product_judgment_required"] is False
    assert first.gate_d["manual_product_judgment_recorded"] is True
    assert first.gate_d["gate_d_pass_claimed"] is False
    assert first.gate_d["product_promise_alpha_pass_claimed"] is False

    exposed = repr(first)
    for private_value in PRIVATE_VALUES:
        assert private_value not in exposed


def test_build_inspection_summary_is_deterministic_and_metadata_only() -> None:
    demo = _demo_module()

    first = demo.build_local_alpha_dashboard_inspection_summary()
    second = demo.build_local_alpha_dashboard_inspection_summary()

    assert first == second
    assert first.endswith("\n")
    assert "AsyncScholar local alpha inspection" in first
    assert "Server started: no" in first
    assert "Browser opened: no" in first
    assert "Gate D: narrow local pass recorded" in first
    assert "Approved scope: local fixture-to-reviewer demo only" in first
    assert "Human product judgment: narrow local pass recorded" in first
    assert "Satisfactory evidence: 9" in first
    assert "Missing evidence: 0" in first
    assert "Narrow pass evidence: human-recorded checkpoint note" in first
    assert "Manual judgment completed: narrow local pass" in first
    assert "Manual judgment recorded in checkpoint: yes" in first
    assert "Run status: Completed" in first
    assert "Source kind: Fixture demo" in first
    assert "Attendance prompt - 42s - 94% confidence" in first
    assert "Important event - 185s - 88% confidence" in first
    assert "Urgent alert" in first
    assert "Status: Pending" in first
    assert "Confirmation required" in first
    assert "Local archive summary" in first
    assert "Reviewer available" in first
    assert "Reviewer artifact metadata only." in first
    assert "Human judgment handoff" in first
    for handoff_line in STATIC_DEMO_HUMAN_JUDGMENT_HANDOFF_LINES[:-1]:
        assert handoff_line in first
    assert "Product Promise Alpha: narrow local pass recorded" in first
    assert "Gate D passed" not in first
    assert "Product Promise Alpha passed" not in first
    serialized = json.dumps({"summary": first})
    for private_value in PRIVATE_VALUES:
        assert private_value not in serialized


def test_current_demo_surfaces_record_narrow_gate_d_pass_without_broad_approval() -> (
    None
):
    demo = _demo_module()

    summary = demo.build_local_alpha_dashboard_inspection_summary()
    html = demo.build_local_alpha_dashboard_static_demo_html()
    payload = demo.build_local_alpha_dashboard_demo_dry_run()
    combined = "\n".join((summary, _visible_text(html), json.dumps(payload)))

    for expected in (
        "Gate D: narrow local pass recorded",
        "Product Promise Alpha: narrow local pass recorded",
        "Human product judgment: narrow local pass recorded",
        "Approved scope: local fixture-to-reviewer demo only",
        "Real online monitoring approved: no",
        "Screenshots/traces/videos/downloads approved: no",
        "Audio/hardware/loopback approved: no",
        "Push/merge approved: no",
        "Future broader/live product judgment required: yes",
        "Gate D handoff packet: narrow local pass noted",
    ):
        assert expected in combined

    for stale in (
        "Gate D not passed",
        "Product Promise Alpha not passed",
        "product_judgment_evidence remains blocking",
        "Blocked on product_judgment_evidence",
        "Gate D blocker: product_judgment_evidence",
        "Gate D: blocked on product_judgment_evidence",
        "Human product judgment required: yes",
        "Gate D handoff packet: manual judgment required",
    ):
        assert stale not in combined

    assert payload["gate_d_status"] == "narrow_local_pass_recorded"
    assert payload["product_judgment_evidence_status"] == "human_recorded_narrow_pass"
    assert payload["product_promise_alpha_pass_claimed"] is False


def test_build_static_demo_html_is_deterministic_and_metadata_only() -> None:
    demo = _demo_module()

    first = demo.build_local_alpha_dashboard_static_demo_html()
    second = demo.build_local_alpha_dashboard_static_demo_html()

    assert first == second
    assert first.startswith("<!doctype html>\n")
    assert first.endswith("\n")
    assert '<html lang="en">' in first
    assert "<title>AsyncScholar local alpha static demo</title>" in first
    assert "AsyncScholar local alpha static demo" in first
    assert "Safety boundary" in first
    assert "Gate D: narrow local pass recorded" in first
    assert "Product judgment: narrow local pass recorded" in first
    assert "Session: completed" in first
    assert "Detected events: 2" in first
    assert "Alert: pending confirmation" in first
    assert "Live delivery: no" in first
    assert "Server started: no" in first
    assert "Browser opened: no" in first
    assert "Demo source status" in first
    assert "Session source: fixed fixture metadata" in first
    assert "Event source: fixed fixture metadata" in first
    assert "Alert source: fixed fixture metadata" in first
    assert "Archive source: fixed fixture metadata" in first
    assert "Gate D source: local handoff metadata" in first
    assert "Transcript source: not displayed" in first
    assert "Recording source: not displayed" in first
    assert "Private source data read: no" in first
    assert "Source refresh required: no" in first
    assert "Local demo launch" in first
    assert (
        "Static demo entrypoint: scripts/run_local_alpha_dashboard_static_demo.ps1"
        in first
    )
    assert "CLI export command: local-alpha-dashboard-static-demo --output" in first
    assert "Private data read: no" in first
    assert "Gate D: narrow local pass recorded" in first
    assert "Approved scope: local fixture-to-reviewer demo only" in first
    assert "Human product judgment: narrow local pass recorded" in first
    assert "Satisfactory evidence: 9" in first
    assert "Missing evidence: 0" in first
    assert "Manual judgment completed: narrow local pass" in first
    assert "Manual judgment recorded in checkpoint: yes" in first
    assert "Run status: Completed" in first
    assert "Source kind: Fixture demo" in first
    assert "Attendance prompt - 42s - 94% confidence" in first
    assert "Important event - 185s - 88% confidence" in first
    assert "Urgent alert" in first
    assert "Status: Pending" in first
    assert "Confirmation required" in first
    assert "Archive review status" in first
    assert "Archive artifacts: metadata only" in first
    assert "Reviewer summary: metadata only" in first
    assert "Detected events archived: 2" in first
    assert "Alert previews archived: pending confirmation" in first
    assert "Transcript text displayed: no" in first
    assert "Recording displayed: no" in first
    assert "Private paths displayed: no" in first
    assert "Delete/export execution: no" in first
    assert "Demo review checklist" in first
    assert "Session status visible: yes" in first
    assert "Detected event summary visible: yes" in first
    assert "Alert preview requires confirmation: yes" in first
    assert "Archive/reviewer metadata visible: yes" in first
    assert "Gate D human note visible: narrow local pass recorded" in first
    assert "Future broader/live product judgment required: yes" in first
    assert "Action execution allowed: no" in first
    assert "Human judgment next step" in first
    assert "Manual inspection completed: narrow local pass" in first
    assert "Product judgment recorded in checkpoint: yes" in first
    assert "AI can complete product judgment: no" in first
    assert "AI can record product judgment: no" in first
    assert "Human-recorded narrow local pass: yes" in first
    assert "Backend evidence trail" in first
    assert "Fixture/local demo evidence: existing CLI surfaces" in first
    assert "Inspection summary: local-alpha-dashboard-inspection" in first
    assert (
        "Static export: local-alpha-dashboard-static-demo --output local-html-file"
        in first
    )
    assert "Gate D evidence bundle: gate-d-local-evidence-bundle" in first
    assert "Gate D handoff packet: gate-d-handoff-packet-local" in first
    assert "Artifact access performed: no" in first
    assert "Command execution performed by page: no" in first
    assert "Private data required: no" in first
    assert "Local alpha demo runbook" in first
    for runbook_line in STATIC_DEMO_RUNBOOK_LINES:
        assert runbook_line in first
    assert "Local alpha artifact summary" in first
    for artifact_summary_line in STATIC_DEMO_ARTIFACT_SUMMARY_LINES:
        assert artifact_summary_line in first
    assert "One-command fixture demo handoff" in first
    for fixture_handoff_line in STATIC_DEMO_FIXTURE_HANDOFF_LINES:
        assert fixture_handoff_line in first
    assert "Fixture demo summary export" in first
    unescaped_first = unescape(first)
    for summary_export_line in STATIC_DEMO_FIXTURE_SUMMARY_EXPORT_LINES:
        assert summary_export_line in unescaped_first
    assert "Gate D safety status" in first
    visible_first = _visible_text(first)
    for gate_d_safety_status_line in STATIC_DEMO_GATE_D_SAFETY_STATUS_LINES:
        assert gate_d_safety_status_line in visible_first
    assert "Local alpha demo readiness checklist" in first
    for readiness_line in STATIC_DEMO_READINESS_CHECKLIST_LINES:
        assert readiness_line in visible_first
    assert "Human judgment handoff" in first
    for handoff_line in STATIC_DEMO_HUMAN_JUDGMENT_HANDOFF_LINES:
        assert handoff_line in visible_first
    assert "Product Promise Alpha: narrow local pass recorded" in first
    assert "Local alpha product loop summary" in first
    for product_loop_line in STATIC_DEMO_PRODUCT_LOOP_SUMMARY_LINES:
        assert product_loop_line in visible_first
    assert "Live delivery perform&#101;d: no" in first
    assert "Local alpha demo review snapshot" in first
    for review_snapshot_line in STATIC_DEMO_REVIEW_SNAPSHOT_LINES:
        assert review_snapshot_line in visible_first
    assert "Human decision boundary" in first
    for decision_boundary_line in STATIC_DEMO_HUMAN_DECISION_BOUNDARY_LINES:
        assert decision_boundary_line in visible_first
    assert "Product review cue" in first
    for product_review_cue_line in STATIC_DEMO_PRODUCT_REVIEW_CUE_LINES:
        assert product_review_cue_line in visible_first
    assert "Local archive summary" in first
    assert "Reviewer available" in first
    assert "Reviewer artifact metadata only." in first
    assert "Gate D passed" not in first
    assert "Product Promise Alpha passed" not in first
    lowered = first.casefold()
    for forbidden in (
        "<script",
        "<link",
        "<img",
        "<iframe",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "src=",
        "href=",
        "action=",
        "method=",
        "formaction=",
        "value=",
    ):
        assert forbidden not in lowered
    _assert_no_event_handler_attributes(first)
    serialized = json.dumps({"html": first})
    for private_value in PRIVATE_VALUES:
        assert private_value not in serialized


def test_static_demo_html_sections_are_human_facing_and_ordered() -> None:
    demo = _demo_module()

    html = demo.build_local_alpha_dashboard_static_demo_html()

    assert html.count("<section") == 29
    strip_text = _summary_status_strip_text(html)
    assert "Gate D: narrow local pass recorded" in strip_text
    assert "Product judgment: narrow local pass recorded" in strip_text
    assert "Session: completed" in strip_text
    assert "Detected events: 2" in strip_text
    assert "Alert: pending confirmation" in strip_text
    assert "Live delivery: no" in strip_text
    assert html.index('class="summary-status-strip"') < html.index("<section")
    assert "Metadata unavailable." not in strip_text
    strip_html = _summary_status_strip_html(html)
    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "c:/",
        "d:\\",
        "d:/",
        "\\\\",
        "meet.example",
        ".env",
        "cookie-value",
        "token=private",
        "auth-state",
        "browser profile",
        "secret",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript",
        "gate d: passed",
        "product promise alpha: passed",
        "gate d passed",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in strip_html.casefold()
    _assert_no_event_handler_attributes(strip_html)

    expected_headings = (
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
    positions = []
    for heading in expected_headings:
        marker = f"<h2>{heading}</h2>"
        assert marker in html
        positions.append(html.index(marker))
    assert positions == sorted(positions)
    assert html.index("<h2>One-command fixture demo handoff</h2>") < html.index(
        "<h2>Fixture demo summary export</h2>"
    )
    assert html.index("<h2>Fixture demo summary export</h2>") < html.index(
        "<h2>Gate D safety status</h2>"
    )
    assert html.index("<h2>Gate D safety status</h2>") < html.index(
        "<h2>Local alpha demo readiness checklist</h2>"
    )
    assert html.index("<h2>Local alpha demo readiness checklist</h2>") < html.index(
        "<h2>Human judgment handoff</h2>"
    )
    assert html.index("<h2>Human judgment handoff</h2>") < html.index(
        "<h2>Local alpha product loop summary</h2>"
    )
    assert html.index("<h2>Local alpha product loop summary</h2>") < html.index(
        "<h2>Local alpha demo review snapshot</h2>"
    )
    assert html.index("<h2>Local alpha demo review snapshot</h2>") < html.index(
        "<h2>Human decision boundary</h2>"
    )
    assert html.index("<h2>Human decision boundary</h2>") < html.index(
        "<h2>Product review cue</h2>"
    )
    assert html.index("<h2>Product review cue</h2>") < html.index(
        "<h2>Demo timeline</h2>"
    )

    gate_section = _section_text(html, "Gate D safety")
    assert "Gate D: narrow local pass recorded" in gate_section
    assert "Approved scope: local fixture-to-reviewer demo only" in gate_section
    assert "Human product judgment: narrow local pass recorded" in gate_section
    assert "Manual judgment completed: narrow local pass" in gate_section
    assert "Manual judgment recorded in checkpoint: yes" in gate_section

    digest_section = _section_text(html, "Evidence digest")
    assert "Handoff status: Metadata aid only" in digest_section
    assert (
        "Local bundle status: Narrow local pass recorded in checkpoint"
        in digest_section
    )
    assert "Satisfactory evidence: 9" in digest_section
    assert "Missing evidence: 0" in digest_section
    assert "Narrow pass evidence: human-recorded checkpoint note" in digest_section
    assert "Manual product judgment completed: narrow local pass" in digest_section
    assert "Manual product judgment recorded in checkpoint: yes" in digest_section
    assert "AI can complete product judgment: no" in digest_section

    summary_export_section = _section_text(html, "Fixture demo summary export")
    summary_export_visible = _visible_text(summary_export_section)
    assert "Metadata unavailable." not in summary_export_section
    for expected in STATIC_DEMO_FIXTURE_SUMMARY_EXPORT_LINES:
        assert expected in summary_export_visible
    assert "<button" not in summary_export_section.casefold()
    for forbidden in (
        "<script",
        "<link",
        "<img",
        "<iframe",
        "<embed",
        "<object",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "\\\\",
        "meet.example",
        ".env",
        "cookie-value",
        "token=private",
        "auth-state",
        "browser profile",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript",
        "summary json",
        "raw command output included: yes",
        "private paths included: yes",
        "browser/server launched: yes",
        "live delivery performed: yes",
        "product judgment recorded: yes",
        "gate d evidence bundle: passed",
        "gate d handoff packet: completed",
        "gate d passed",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in summary_export_section.casefold()
    assert re.search(r"[a-z]:\\", summary_export_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(summary_export_section)

    gate_d_safety_status_section = _section_text(html, "Gate D safety status")
    gate_d_safety_status_visible = _visible_text(gate_d_safety_status_section)
    assert "Metadata unavailable." not in gate_d_safety_status_section
    for expected in STATIC_DEMO_GATE_D_SAFETY_STATUS_LINES:
        assert expected in gate_d_safety_status_visible
    for forbidden in (
        "<script",
        "<link",
        "<img",
        "<iframe",
        "<embed",
        "<object",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "\\\\",
        "meet.example",
        ".env",
        "cookie-value",
        "token=private",
        "auth-state",
        "browser profile",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript",
        "gate d status: passed",
        "real online monitoring approved: yes",
        "browser/auth/profile/cookies/tokens approved: yes",
        "audio/hardware/loopback approved: yes",
        "live delivery approved: yes",
        "autonomous participation approved: yes",
        "academic-answer behavior approved: yes",
        "product judgment recorded: yes",
        "gate d passed",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in gate_d_safety_status_section.casefold()
    assert (
        re.search(r"[a-z]:\\", gate_d_safety_status_section, flags=re.IGNORECASE)
        is None
    )
    _assert_no_event_handler_attributes(gate_d_safety_status_section)

    readiness_section = _section_text(html, "Local alpha demo readiness checklist")
    readiness_visible = _visible_text(readiness_section)
    assert "Metadata unavailable." not in readiness_section
    for expected in STATIC_DEMO_READINESS_CHECKLIST_LINES:
        assert expected in readiness_visible
    for forbidden in (
        "<script",
        "<link",
        "<img",
        "<iframe",
        "<embed",
        "<object",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "\\\\",
        "meet.example",
        ".env",
        "cookie-value",
        "token=private",
        "auth-state",
        "browser profile",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript",
        "raw command output",
        "fixture/local demo available: no",
        "static dashboard export available: no",
        "session status visible: no",
        "detected event summary visible: no",
        "alert preview requires confirmation: no",
        "archive/reviewer summary visible: no",
        "gate d safety status visible: no",
        "product judgment required: no",
        "gate d passed",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in readiness_section.casefold()
    assert re.search(r"[a-z]:\\", readiness_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(readiness_section)

    handoff_section = _section_text(html, "Human judgment handoff")
    handoff_visible = _visible_text(handoff_section)
    assert "Metadata unavailable." not in handoff_section
    for expected in STATIC_DEMO_HUMAN_JUDGMENT_HANDOFF_LINES:
        assert expected in handoff_visible
    assert "Product Promise Alpha: narrow local pass recorded" in handoff_section
    for forbidden in (
        "<script",
        "<link",
        "<img",
        "<iframe",
        "<embed",
        "<object",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "\\\\",
        "meet.example",
        ".env",
        "cookie-value",
        "token=private",
        "auth-state",
        "browser profile",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript",
        "raw command output",
        "product judgment: passed",
        "human reviewer required: no",
        "ai can record pass judgment: yes",
        "gate d blocking evidence: none",
        "evidence source: real online monitoring",
        "static dashboard available: no",
        "gate d handoff packet available: no",
        "real online monitoring approved: yes",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in handoff_section.casefold()
    assert re.search(r"[a-z]:\\", handoff_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(handoff_section)

    product_loop_section = _section_text(html, "Local alpha product loop summary")
    product_loop_visible = _visible_text(product_loop_section)
    assert "Metadata unavailable." not in product_loop_section
    for expected in STATIC_DEMO_PRODUCT_LOOP_SUMMARY_LINES:
        assert expected in product_loop_visible
    assert "Live delivery perform&#101;d: no" in product_loop_section
    for forbidden in (
        "<script",
        "<link",
        "<img",
        "<iframe",
        "<embed",
        "<object",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "\\\\",
        "meet.example",
        ".env",
        "cookie-value",
        "token=private",
        "auth-state",
        "browser profile",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript",
        "raw command output",
        "fixture input: private",
        "session status: failed",
        "detected events: 0",
        "alert preview: sent",
        "archive/reviewer: transcript",
        "gate d bundle: passed",
        "product judgment: passed",
        "private content displayed: yes",
        "live delivery performed: yes",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in product_loop_section.casefold()
    assert re.search(r"[a-z]:\\", product_loop_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(product_loop_section)

    manual_review_section = _section_text(html, "Manual review status")
    manual_review_visible = _visible_text(manual_review_section)
    assert "Metadata unavailable." not in manual_review_section
    for expected in (
        "Review packet: local metadata only",
        "Human product judgment: narrow local pass recorded",
        "Product judgment storage written: no",
        "AI can complete product judgment: no",
        "Gate D human note: narrow local pass recorded",
        "Private data needed for review: no",
        "Live services needed for review: no",
        "Action execution allowed: no",
        "Product Promise Alpha: narrow local pass recorded",
    ):
        assert expected in manual_review_visible
    assert "<button" not in manual_review_section.casefold()
    for forbidden in (
        "<script",
        "<link",
        "<img",
        "<iframe",
        "<embed",
        "<object",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "\\\\",
        "meet.example",
        ".env",
        "cookie",
        "token",
        "auth",
        "profile",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript",
        "recording",
        "final product judgment recorded: yes",
        "ai can complete product judgment: yes",
        "private data needed for review: yes",
        "live services needed for review: yes",
        "action execution allowed: yes",
        "gate d passed",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in manual_review_section.casefold()
    assert re.search(r"[a-z]:\\", manual_review_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(manual_review_section)
    assert html.index("<h2>Evidence digest</h2>") < html.index(
        "<h2>Manual review status</h2>"
    )
    assert html.index("<h2>Manual review status</h2>") < html.index(
        "<h2>Demo review checklist</h2>"
    )

    checklist_section = _section_text(html, "Demo review checklist")
    checklist_visible = _visible_text(checklist_section)
    assert "Metadata unavailable." not in checklist_section
    for expected in (
        "Session status visible: yes",
        "Detected event summary visible: yes",
        "Alert preview requires confirmation: yes",
        "Archive/reviewer metadata visible: yes",
        "Gate D human note visible: narrow local pass recorded",
        "Future broader/live product judgment required: yes",
        "Action execution allowed: no",
        "Product Promise Alpha: narrow local pass recorded",
    ):
        assert expected in checklist_visible
    assert "<button" not in checklist_section.casefold()
    for forbidden in (
        "<script",
        "<link",
        "<img",
        "<iframe",
        "<embed",
        "<object",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "\\\\",
        "meet.example",
        ".env",
        "cookie",
        "token",
        "auth",
        "profile",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript",
        "recording",
        "session status visible: no",
        "detected event summary visible: no",
        "alert preview requires confirmation: no",
        "archive/reviewer metadata visible: no",
        "gate d blocker visible: none",
        "human product judgment required: no",
        "action execution allowed: yes",
        "gate d passed",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in checklist_section.casefold()
    assert re.search(r"[a-z]:\\", checklist_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(checklist_section)
    assert html.index("<h2>Demo review checklist</h2>") < html.index(
        "<h2>Human judgment next step</h2>"
    )

    human_judgment_section = _section_text(html, "Human judgment next step")
    human_judgment_visible = _visible_text(human_judgment_section)
    assert "Metadata unavailable." not in human_judgment_section
    for expected in (
        "Manual inspection completed: narrow local pass",
        "Product judgment recorded in checkpoint: yes",
        "AI can complete product judgment: no",
        "AI can record product judgment: no",
        "Human-recorded narrow local pass: yes",
        "Action execution allowed: no",
        "Product Promise Alpha: narrow local pass recorded",
    ):
        assert expected in human_judgment_visible
    assert "<button" not in human_judgment_section.casefold()
    for forbidden in (
        "<script",
        "<link",
        "<img",
        "<iframe",
        "<embed",
        "<object",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "\\\\",
        "meet.example",
        ".env",
        "cookie",
        "token",
        "auth",
        "profile",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript",
        "recording",
        "manual inspection required: no",
        "product judgment recorded: yes",
        "ai can complete product judgment: yes",
        "ai can record product judgment: yes",
        "product_judgment_evidence_status: satisfactory",
        "action execution allowed: yes",
        "gate d passed",
        "product promise alpha passed",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in human_judgment_section.casefold()
    assert re.search(r"[a-z]:\\", human_judgment_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(human_judgment_section)
    assert html.index("<h2>Human judgment next step</h2>") < html.index(
        "<h2>Session status</h2>"
    )

    session_section = _section_text(html, "Session status")
    assert "Server started: no" in session_section
    assert "Browser opened: no" in session_section
    assert "Run status: Completed" in session_section
    assert "Source kind: Fixture demo" in session_section
    assert "Segments: 5" in session_section
    assert "Events: 2" in session_section

    source_section = _section_text(html, "Demo source status")
    source_visible = _visible_text(source_section)
    assert "Metadata unavailable." not in source_section
    for expected in (
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
    ):
        assert expected in source_visible
    assert "<button" not in source_section.casefold()
    for forbidden in (
        "<script",
        "<link",
        "<img",
        "<iframe",
        "<embed",
        "<object",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "\\\\",
        "meet.example",
        ".env",
        "cookie",
        "token",
        "auth",
        "profile",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript source: displayed",
        "recording source: displayed",
        "private source data read: yes",
        "source refresh required: yes",
        "gate d source: passed",
        "product promise alpha passed",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in source_section.casefold()
    assert re.search(r"[a-z]:\\", source_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(source_section)
    assert html.index("<h2>Session status</h2>") < html.index(
        "<h2>Demo source status</h2>"
    )
    assert html.index("<h2>Demo source status</h2>") < html.index(
        "<h2>Local demo launch</h2>"
    )

    launch_section = _section_text(html, "Local demo launch")
    launch_visible = _visible_text(launch_section)
    assert "Metadata unavailable." not in launch_section
    assert (
        "Static demo entrypoint: scripts/run_local_alpha_dashboard_static_demo.ps1"
        in launch_visible
    )
    assert (
        "CLI export command: local-alpha-dashboard-static-demo --output "
        "local-html-file" in launch_visible
    )
    assert "Server started: no" in launch_visible
    assert "Browser opened: no" in launch_visible
    assert "Live delivery: no" in launch_visible
    assert "Private data read: no" in launch_visible
    assert "Gate D: narrow local pass recorded" in launch_visible
    assert "Product Promise Alpha: narrow local pass recorded" in launch_visible
    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "\\\\",
        "meet.example",
        ".env",
        "cookie",
        "token",
        "auth",
        "profile",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript",
        "gate d passed",
        "product promise alpha passed",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in launch_section.casefold()
    assert re.search(r"[a-z]:\\", launch_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(launch_section)

    verification_section = _section_text(html, "Demo verification status")
    verification_visible = _visible_text(verification_section)
    assert "Metadata unavailable." not in verification_section
    for expected in (
        "Static artifact: generated locally",
        "Source mode: fixed fixture metadata",
        "Server required: no",
        "Browser required: no",
        "Inspection command: local-alpha-dashboard-inspection",
        "Static export command: local-alpha-dashboard-static-demo --output "
        "local-html-file",
        "Gate D checkpoint: narrow local pass recorded",
        "Narrow pass evidence: human-recorded checkpoint note",
        "Manual product judgment completed: narrow local pass",
        "Product Promise Alpha: narrow local pass recorded",
    ):
        assert expected in verification_visible
    assert "<button" not in verification_section.casefold()
    for forbidden in (
        "<script",
        "<link",
        "<img",
        "<iframe",
        "<embed",
        "<object",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "\\\\",
        "meet.example",
        ".env",
        "cookie",
        "token",
        "auth",
        "profile",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript",
        "server required: yes",
        "browser required: yes",
        "gate d evidence bundle: passed",
        "gate d passed",
        "product promise alpha passed",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in verification_section.casefold()
    assert re.search(r"[a-z]:\\", verification_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(verification_section)
    assert html.index("<h2>Local demo launch</h2>") < html.index(
        "<h2>Demo verification status</h2>"
    )
    assert html.index("<h2>Demo verification status</h2>") < html.index(
        "<h2>Backend evidence trail</h2>"
    )

    backend_evidence_section = _section_text(html, "Backend evidence trail")
    backend_evidence_visible = _visible_text(backend_evidence_section)
    assert "Metadata unavailable." not in backend_evidence_section
    for expected in (
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
    ):
        assert expected in backend_evidence_visible
    assert "<button" not in backend_evidence_section.casefold()
    for forbidden in (
        "<script",
        "<link",
        "<img",
        "<iframe",
        "<embed",
        "<object",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "\\\\",
        "meet.example",
        ".env",
        "cookie",
        "token",
        "auth",
        "profile",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript",
        "recording",
        "artifact access performed: yes",
        "command execution performed by page: yes",
        "private data required: yes",
        "gate d evidence bundle: passed",
        "product_judgment_evidence_status: satisfactory",
        "gate d passed",
        "product promise alpha passed",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in backend_evidence_section.casefold()
    assert re.search(r"[a-z]:\\", backend_evidence_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(backend_evidence_section)
    assert html.index("<h2>Backend evidence trail</h2>") < html.index(
        "<h2>Local alpha demo runbook</h2>"
    )

    runbook_section = _section_text(html, "Local alpha demo runbook")
    runbook_visible = _visible_text(runbook_section)
    assert "Metadata unavailable." not in runbook_section
    for expected in STATIC_DEMO_RUNBOOK_LINES:
        assert expected in runbook_visible
    assert "<button" not in runbook_section.casefold()
    for forbidden in (
        "<script",
        "<link",
        "<img",
        "<iframe",
        "<embed",
        "<object",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "\\\\",
        "meet.example",
        ".env",
        "cookie",
        "token",
        "auth",
        "profile",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript",
        "recording",
        "page executes commands",
        "artifacts are opened by the page",
        "private data required: yes",
        "product_judgment_evidence_status: satisfactory",
        "gate d passed",
        "product promise alpha passed",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in runbook_section.casefold()
    assert re.search(r"[a-z]:\\", runbook_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(runbook_section)
    assert html.index("<h2>Local alpha demo runbook</h2>") < html.index(
        "<h2>Local alpha artifact summary</h2>"
    )

    artifact_summary_section = _section_text(html, "Local alpha artifact summary")
    artifact_summary_visible = _visible_text(artifact_summary_section)
    assert "Metadata unavailable." not in artifact_summary_section
    for expected in STATIC_DEMO_ARTIFACT_SUMMARY_LINES:
        assert expected in artifact_summary_visible
    assert artifact_summary_section.count("events.jsonl") == 1
    assert artifact_summary_section.count("alerts.log") == 1
    assert artifact_summary_section.count("reviewer.md") == 1
    assert "<button" not in artifact_summary_section.casefold()
    for forbidden in (
        "<script",
        "<link",
        "<img",
        "<iframe",
        "<embed",
        "<object",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "c:/",
        "\\\\",
        "/tmp/",
        "meet.example",
        ".env",
        "cookie",
        "token",
        "auth",
        "profile",
        "private.jsonl",
        "session.jsonl",
        "private-alerts.log",
        "private-reviewer.md",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript",
        "recording",
        "archive/reviewer contents displayed: yes",
        "private paths displayed: yes",
        "artifact opening performed: yes",
        "generated artifacts committed: yes",
        "product_judgment_evidence_status: satisfactory",
        "gate d passed",
        "product promise alpha passed",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in artifact_summary_section.casefold()
    assert re.search(r"[a-z]:\\", artifact_summary_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(artifact_summary_section)
    assert html.index("<h2>Local alpha artifact summary</h2>") < html.index(
        "<h2>One-command fixture demo handoff</h2>"
    )

    fixture_handoff_section = _section_text(html, "One-command fixture demo handoff")
    fixture_handoff_visible = _visible_text(fixture_handoff_section)
    assert "Metadata unavailable." not in fixture_handoff_section
    for expected in STATIC_DEMO_FIXTURE_HANDOFF_LINES:
        assert expected in fixture_handoff_visible
    assert "<button" not in fixture_handoff_section.casefold()
    for forbidden in (
        "<script",
        "<link",
        "<img",
        "<iframe",
        "<embed",
        "<object",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "c:/",
        "\\\\",
        "/tmp/",
        "meet.example",
        ".env",
        "cookie",
        "token",
        "auth",
        "profile",
        "private.jsonl",
        "session.jsonl",
        "private-alerts.log",
        "private-reviewer.md",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript",
        "recording",
        "raw command output displayed: yes",
        "user paths displayed: yes",
        "browser/server launched by page: yes",
        "product judgment recorded: yes",
        "product_judgment_evidence_status: satisfactory",
        "gate d passed",
        "product promise alpha passed",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in fixture_handoff_section.casefold()
    assert re.search(r"[a-z]:\\", fixture_handoff_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(fixture_handoff_section)
    assert html.index("<h2>One-command fixture demo handoff</h2>") < html.index(
        "<h2>Demo timeline</h2>"
    )

    timeline_section = _section_text(html, "Demo timeline")
    assert "Fixture source prepared" in timeline_section
    assert "Session completed" in timeline_section
    assert "Event detected" in timeline_section
    assert "Alert awaiting confirmation" in timeline_section
    assert "Archive/reviewer metadata ready" in timeline_section
    assert "Gate D narrow local pass recorded" in timeline_section

    events_section = _section_text(html, "Detected events")
    assert "Attendance prompt - 42s - 94% confidence" in events_section
    assert "Important event - 185s - 88% confidence" in events_section

    alert_section = _section_text(html, "Alert preview")
    assert "Urgent alert" in alert_section
    assert "Status: Pending" in alert_section
    assert "Confirmation required" in alert_section
    assert "Review confirmation before acting." in alert_section

    confirmation_section = _section_text(html, "Confirmation queue")
    confirmation_visible = _visible_text(confirmation_section)
    assert "User confirmation required" in confirmation_visible
    assert "Alert status: pending" in confirmation_visible
    assert "Participation action sent: no" in confirmation_visible
    assert "Autonomous participation: no" in confirmation_visible
    assert "Live delivery: no" in confirmation_visible
    assert "Academic answer behavior: no" in confirmation_visible

    action_section = _section_text(html, "Action controls")
    action_visible = _visible_text(action_section)
    assert "Metadata unavailable." not in action_section
    assert "Review alert confirmation" in action_visible
    assert "Send participation action" in action_visible
    assert "Open archive reviewer" in action_visible
    assert "Record product judgment" in action_visible
    assert "User confirmation required" in action_visible
    assert "Alert delivery live: no" in action_visible
    assert "Participation action sent: no" in action_visible
    assert "Autonomous participation: no" in action_visible
    assert "Academic answer behavior: no" in action_visible
    assert "Gate D: narrow local pass recorded" in action_visible
    assert "Product Promise Alpha: narrow local pass recorded" in action_visible
    assert action_section.count("<button ") == 4
    assert action_section.count('type="button"') == 4
    assert action_section.count(" disabled ") == 4
    assert action_section.count('aria-disabled="true"') == 4
    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
    ):
        assert forbidden not in action_section.casefold()
    _assert_no_event_handler_attributes(action_section)

    archive_review_section = _section_text(html, "Archive review status")
    archive_review_visible = _visible_text(archive_review_section)
    assert "Metadata unavailable." not in archive_review_section
    for expected in (
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
    ):
        assert expected in archive_review_visible
    assert "<button" not in archive_review_section.casefold()
    for forbidden in (
        "<script",
        "<link",
        "<img",
        "<iframe",
        "<embed",
        "<object",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "\\\\",
        "meet.example",
        ".env",
        "cookie",
        "token",
        "auth",
        "profile",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript text: private",
        "recording displayed: yes",
        "private paths displayed: yes",
        "delete/export execution: yes",
        "gate d passed",
        "product promise alpha passed",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in archive_review_section.casefold()
    assert re.search(r"[a-z]:\\", archive_review_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(archive_review_section)
    assert html.index("<h2>Action controls</h2>") < html.index(
        "<h2>Archive review status</h2>"
    )
    assert html.index("<h2>Archive review status</h2>") < html.index(
        "<h2>Archive and reviewer</h2>"
    )

    archive_section = _section_text(html, "Archive and reviewer")
    assert "Local archive summary" in archive_section
    assert "Reviewer available" in archive_section
    assert "Reviewer artifact metadata only." in archive_section

    safety_section = _section_text(html, "Safety boundary")
    assert "Local fixture-to-reviewer demo only" in safety_section
    assert "no real external meetings" in safety_section
    assert "private meeting/class data" in safety_section
    assert "audio/hardware/loopback" in safety_section
    assert "live delivery" in safety_section
    assert "participation" in safety_section
    assert "academic-answer behavior" in safety_section


def test_static_demo_timeline_fails_closed_for_private_values(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_timeline() -> tuple[str, ...]:
        return (
            "Fixture source prepared",
            "C:\\Users\\student\\secret-token-auth-profile",
            "Gate D passed",
            "https://meet.example.edu/class-room?token=private",
        )

    monkeypatch.setattr(demo, "_build_static_demo_timeline_lines", fake_timeline)

    html = demo.build_local_alpha_dashboard_static_demo_html()

    timeline_section = _section_text(html, "Demo timeline")
    for expected in (
        "Fixture source prepared",
        "Session completed",
        "Event detected",
        "Alert awaiting confirmation",
        "Archive/reviewer metadata ready",
        "Gate D narrow local pass recorded",
    ):
        assert expected in timeline_section

    lowered = timeline_section.casefold()
    for forbidden in (
        "secret",
        "token",
        "auth",
        "profile",
        "meet.example",
        "c:\\",
        "gate d passed",
        "product promise alpha passed",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered


@pytest.mark.parametrize(
    "unsafe_queue",
    [
        (
            "User confirmation required",
            "Alert status: sent",
            "Participation action sent: yes",
            "Autonomous participation: yes",
            "Live delivery: yes",
            "Academic answer behavior: yes",
        ),
        (
            "User confirmation required",
            "C:\\Users\\student\\secret-token-auth-profile",
            "Gate D passed",
            "Product Promise Alpha passed",
            "https://meet.example.edu/class-room?token=private",
            "Good morning, everyone. I am going to take attendance",
        ),
        ("User confirmation required",),
        (),
    ],
)
def test_static_demo_confirmation_queue_fails_closed_for_unsafe_values(
    monkeypatch,
    unsafe_queue: tuple[str, ...],
) -> None:
    demo = _demo_module()

    def fake_queue() -> tuple[str, ...]:
        return unsafe_queue

    monkeypatch.setattr(demo, "_build_static_demo_confirmation_queue_lines", fake_queue)

    html = demo.build_local_alpha_dashboard_static_demo_html()

    confirmation_section = _section_text(html, "Confirmation queue")
    confirmation_visible = _visible_text(confirmation_section)
    for expected in (
        "User confirmation required",
        "Alert status: pending",
        "Participation action sent: no",
        "Autonomous participation: no",
        "Live delivery: no",
        "Academic answer behavior: no",
    ):
        assert expected in confirmation_visible

    lowered = confirmation_section.casefold()
    for forbidden in (
        "sent: yes",
        "autonomous participation: yes",
        "live delivery: yes",
        "academic answer behavior: yes",
        "good morning",
        "secret",
        "token",
        "auth",
        "profile",
        "meet.example",
        "c:\\",
        "gate d passed",
        "product promise alpha passed",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered


def test_static_demo_confirmation_queue_fails_closed_for_helper_exception(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_queue() -> tuple[str, ...]:
        raise RuntimeError("C:\\Users\\student\\.env token traceback")

    monkeypatch.setattr(demo, "_build_static_demo_confirmation_queue_lines", fake_queue)

    html = demo.build_local_alpha_dashboard_static_demo_html()

    confirmation_section = _section_text(html, "Confirmation queue")
    confirmation_visible = _visible_text(confirmation_section)
    assert "User confirmation required" in confirmation_visible
    assert "Alert status: pending" in confirmation_visible
    assert "Participation action sent: no" in confirmation_visible
    assert "Autonomous participation: no" in confirmation_visible
    assert "Live delivery: no" in confirmation_visible
    assert "Academic answer behavior: no" in confirmation_visible
    assert "traceback" not in confirmation_section.casefold()
    assert ".env" not in confirmation_section.casefold()
    assert "token" not in confirmation_section.casefold()


@pytest.mark.parametrize(
    "unsafe_controls",
    [
        (
            "Action: Review alert confirmation",
            "Action: <script>alert('unsafe')</script>",
            "Participation action sent: yes",
            "Autonomous participation: yes",
            "Live delivery: yes",
            "Academic answer behavior: yes",
            "Gate D passed",
            "Product Promise Alpha passed",
        ),
        (
            "Action: C:\\Users\\student\\secret-token-auth-profile",
            "Action: https://meet.example.edu/class-room?token=private",
            "User confirmation required",
        ),
        ("Action: Review alert confirmation",),
        (),
    ],
)
def test_static_demo_action_controls_fail_closed_for_unsafe_values(
    monkeypatch,
    unsafe_controls: tuple[str, ...],
) -> None:
    demo = _demo_module()

    def fake_controls() -> tuple[str, ...]:
        return unsafe_controls

    monkeypatch.setattr(demo, "_build_static_demo_action_control_lines", fake_controls)

    html = demo.build_local_alpha_dashboard_static_demo_html()

    action_section = _section_text(html, "Action controls")
    action_visible = _visible_text(action_section)
    for expected in (
        "Review alert confirmation",
        "Send participation action",
        "Open archive reviewer",
        "Record product judgment",
        "User confirmation required",
        "Alert delivery live: no",
        "Participation action sent: no",
        "Autonomous participation: no",
        "Academic answer behavior: no",
        "Gate D: narrow local pass recorded",
        "Product Promise Alpha: narrow local pass recorded",
    ):
        assert expected in action_visible
    assert action_section.count("<button ") == 4
    assert action_section.count('type="button"') == 4
    assert action_section.count(" disabled ") == 4
    assert action_section.count('aria-disabled="true"') == 4

    lowered = action_section.casefold()
    for forbidden in (
        "<script",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "secret",
        "token",
        "auth",
        "profile",
        "meet.example",
        "c:\\",
        "participation action sent: yes",
        "autonomous participation: yes",
        "live delivery: yes",
        "academic answer behavior: yes",
        "gate d passed",
        "product promise alpha passed",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered
    _assert_no_event_handler_attributes(action_section)


def test_static_demo_action_controls_fail_closed_for_helper_exception(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_controls() -> tuple[str, ...]:
        raise RuntimeError("C:\\Users\\student\\.env token traceback")

    monkeypatch.setattr(demo, "_build_static_demo_action_control_lines", fake_controls)

    html = demo.build_local_alpha_dashboard_static_demo_html()

    action_section = _section_text(html, "Action controls")
    action_visible = _visible_text(action_section)
    assert "Review alert confirmation" in action_visible
    assert "Send participation action" in action_visible
    assert "Open archive reviewer" in action_visible
    assert "Record product judgment" in action_visible
    assert "User confirmation required" in action_visible
    assert "Alert delivery live: no" in action_visible
    assert "Participation action sent: no" in action_visible
    assert "Autonomous participation: no" in action_visible
    assert "Academic answer behavior: no" in action_visible
    assert "Gate D: narrow local pass recorded" in action_visible
    assert "Product Promise Alpha: narrow local pass recorded" in action_visible
    assert "traceback" not in action_section.casefold()
    assert ".env" not in action_section.casefold()
    assert "token" not in action_section.casefold()


@pytest.mark.parametrize(
    "unsafe_archive_review",
    [
        (
            "Archive artifacts: metadata only",
            "Reviewer summary: metadata only",
            "Detected events archived: 2",
            "Alert previews archived: pending confirmation",
            "Transcript text: private class content",
            "Recording displayed: yes",
            "Private paths displayed: yes",
            "Delete/export execution: yes",
            "Gate D passed",
            "Product Promise Alpha passed",
        ),
        (
            "Archive artifacts: C:\\Users\\student\\secret-token-auth-profile",
            "Reviewer summary: https://meet.example.edu/class-room?token=private",
            "Detected events archived: 2",
            "Alert previews archived: pending confirmation",
            "transcript artifact: data\\sessions\\events.jsonl",
            "recording artifact: lecture.wav lecture.mp4 clip.png",
            "product judgment evidence satisfied",
        ),
        ("Archive artifacts: metadata only",),
        (),
    ],
)
def test_static_demo_archive_review_status_fails_closed_for_unsafe_values(
    monkeypatch,
    unsafe_archive_review: tuple[str, ...],
) -> None:
    demo = _demo_module()

    def fake_archive_review() -> tuple[str, ...]:
        return unsafe_archive_review

    monkeypatch.setattr(
        demo,
        "_build_static_demo_archive_review_status_lines",
        fake_archive_review,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    archive_review_section = _section_text(html, "Archive review status")
    archive_review_visible = _visible_text(archive_review_section)
    for expected in (
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
    ):
        assert expected in archive_review_visible

    lowered = archive_review_section.casefold()
    for forbidden in (
        "<script",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "secret",
        "token",
        "auth",
        "profile",
        "meet.example",
        "c:\\",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "transcript text: private",
        "recording displayed: yes",
        "private paths displayed: yes",
        "delete/export execution: yes",
        "gate d passed",
        "product promise alpha passed",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered
    assert "<button" not in lowered
    _assert_no_event_handler_attributes(archive_review_section)


def test_static_demo_archive_review_status_fails_closed_for_helper_exception(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_archive_review() -> tuple[str, ...]:
        raise RuntimeError("C:\\Users\\student\\.env token traceback")

    monkeypatch.setattr(
        demo,
        "_build_static_demo_archive_review_status_lines",
        fake_archive_review,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    archive_review_section = _section_text(html, "Archive review status")
    archive_review_visible = _visible_text(archive_review_section)
    assert "Archive artifacts: metadata only" in archive_review_visible
    assert "Reviewer summary: metadata only" in archive_review_visible
    assert "Detected events archived: 2" in archive_review_visible
    assert "Alert previews archived: pending confirmation" in archive_review_visible
    assert "Transcript text displayed: no" in archive_review_visible
    assert "Recording displayed: no" in archive_review_visible
    assert "Private paths displayed: no" in archive_review_visible
    assert "Delete/export execution: no" in archive_review_visible
    assert "Gate D: narrow local pass recorded" in archive_review_visible
    assert "Product Promise Alpha: narrow local pass recorded" in archive_review_visible
    assert "traceback" not in archive_review_section.casefold()
    assert ".env" not in archive_review_section.casefold()
    assert "token" not in archive_review_section.casefold()


@pytest.mark.parametrize(
    "unsafe_verification",
    [
        (
            "Static artifact: generated locally",
            "Source mode: fixed fixture metadata",
            "Server required: yes",
            "Browser required: yes",
            "Inspection command: https://meet.example.edu/class-room?token=private",
            "Static export command: file:///tmp/private-demo.html",
            "Gate D evidence bundle: passed",
            "Blocking evidence: none",
            "Manual product judgment required: no",
            "Product Promise Alpha passed",
        ),
        (
            "Static artifact: C:\\Users\\student\\secret-token-auth-profile",
            "Source mode: transcript text: private class content",
            "Server required: no",
            "Browser required: no",
            "Inspection command: local-alpha-dashboard-inspection",
            "Static export command: local-alpha-dashboard-static-demo --output "
            "data\\sessions\\private.jsonl",
            "Gate D checkpoint: narrow local pass recorded",
            "Narrow pass evidence: human-recorded checkpoint note",
            "Manual product judgment completed: narrow local pass",
            "product judgment evidence satisfied",
        ),
        ("Static artifact: generated locally",),
        (),
    ],
)
def test_static_demo_verification_status_fails_closed_for_unsafe_values(
    monkeypatch,
    unsafe_verification: tuple[str, ...],
) -> None:
    demo = _demo_module()

    def fake_verification() -> tuple[str, ...]:
        return unsafe_verification

    monkeypatch.setattr(
        demo,
        "_build_static_demo_verification_status_lines",
        fake_verification,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    verification_section = _section_text(html, "Demo verification status")
    verification_visible = _visible_text(verification_section)
    for expected in (
        "Static artifact: generated locally",
        "Source mode: fixed fixture metadata",
        "Server required: no",
        "Browser required: no",
        "Inspection command: local-alpha-dashboard-inspection",
        "Static export command: local-alpha-dashboard-static-demo --output "
        "local-html-file",
        "Gate D checkpoint: narrow local pass recorded",
        "Narrow pass evidence: human-recorded checkpoint note",
        "Manual product judgment completed: narrow local pass",
        "Product Promise Alpha: narrow local pass recorded",
    ):
        assert expected in verification_visible

    lowered = verification_section.casefold()
    for forbidden in (
        "<script",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "secret",
        "token",
        "auth",
        "profile",
        "meet.example",
        "http:",
        "https:",
        "file:",
        "c:\\",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "transcript",
        "server required: yes",
        "browser required: yes",
        "gate d evidence bundle: passed",
        "blocking evidence: none",
        "manual product judgment required: no",
        "product promise alpha passed",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered
    assert "<button" not in lowered
    _assert_no_event_handler_attributes(verification_section)


def test_static_demo_verification_status_fails_closed_for_helper_exception(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_verification() -> tuple[str, ...]:
        raise RuntimeError("C:\\Users\\student\\.env token traceback")

    monkeypatch.setattr(
        demo,
        "_build_static_demo_verification_status_lines",
        fake_verification,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    verification_section = _section_text(html, "Demo verification status")
    verification_visible = _visible_text(verification_section)
    assert "Static artifact: generated locally" in verification_visible
    assert "Source mode: fixed fixture metadata" in verification_visible
    assert "Server required: no" in verification_visible
    assert "Browser required: no" in verification_visible
    assert (
        "Inspection command: local-alpha-dashboard-inspection" in verification_visible
    )
    assert (
        "Static export command: local-alpha-dashboard-static-demo --output "
        "local-html-file" in verification_visible
    )
    assert "Gate D checkpoint: narrow local pass recorded" in verification_visible
    assert (
        "Narrow pass evidence: human-recorded checkpoint note" in verification_visible
    )
    assert (
        "Manual product judgment completed: narrow local pass" in verification_visible
    )
    assert "Product Promise Alpha: narrow local pass recorded" in verification_visible
    assert "traceback" not in verification_section.casefold()
    assert ".env" not in verification_section.casefold()
    assert "token" not in verification_section.casefold()


@pytest.mark.parametrize(
    "unsafe_backend_evidence",
    [
        (
            "Fixture/local demo evidence: live meeting data",
            "Inspection summary: https://meet.example.edu/class-room?token=private",
            "Static export: file:///tmp/private-dashboard.html",
            "Gate D evidence bundle: passed",
            "Gate D handoff packet: C:\\Users\\student\\auth-profile.json",
            "Artifact access performed: yes",
            "Command execution performed by page: yes",
            "Private data required: yes",
            "product_judgment_evidence_status: satisfactory",
            "Product Promise Alpha passed",
        ),
        (
            "Fixture/local demo evidence: existing CLI surfaces",
            "Inspection summary: local-alpha-dashboard-inspection",
            "Static export: data\\sessions\\private.jsonl",
            "Gate D evidence bundle: gate-d-local-evidence-bundle",
            "Gate D handoff packet: gate-d-handoff-packet-local",
            "Artifact access performed: no",
            "Command execution performed by page: no",
            "Private data required: no",
            "transcript text: Good morning, everyone",
            "product judgment evidence satisfied",
        ),
        ("Fixture/local demo evidence: existing CLI surfaces",),
        (),
    ],
)
def test_static_demo_backend_evidence_trail_fails_closed_for_unsafe_values(
    monkeypatch,
    unsafe_backend_evidence: tuple[str, ...],
) -> None:
    demo = _demo_module()

    def fake_backend_evidence() -> tuple[str, ...]:
        return unsafe_backend_evidence

    monkeypatch.setattr(
        demo,
        "_build_static_demo_backend_evidence_trail_lines",
        fake_backend_evidence,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    backend_evidence_section = _section_text(html, "Backend evidence trail")
    backend_evidence_visible = _visible_text(backend_evidence_section)
    for expected in (
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
    ):
        assert expected in backend_evidence_visible

    lowered = backend_evidence_section.casefold()
    for forbidden in (
        "<script",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "meet.example",
        "http:",
        "https:",
        "file:",
        "c:\\",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript",
        "auth",
        "profile",
        "token",
        "artifact access performed: yes",
        "command execution performed by page: yes",
        "private data required: yes",
        "gate d evidence bundle: passed",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered
    assert "<button" not in lowered
    _assert_no_event_handler_attributes(backend_evidence_section)


def test_static_demo_backend_evidence_trail_fails_closed_for_helper_exception(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_backend_evidence() -> tuple[str, ...]:
        raise RuntimeError("C:\\Users\\student\\.env token traceback")

    monkeypatch.setattr(
        demo,
        "_build_static_demo_backend_evidence_trail_lines",
        fake_backend_evidence,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    backend_evidence_section = _section_text(html, "Backend evidence trail")
    backend_evidence_visible = _visible_text(backend_evidence_section)
    assert (
        "Fixture/local demo evidence: existing CLI surfaces" in backend_evidence_visible
    )
    assert "Inspection summary: local-alpha-dashboard-inspection" in (
        backend_evidence_visible
    )
    assert (
        "Static export: local-alpha-dashboard-static-demo --output local-html-file"
        in backend_evidence_visible
    )
    assert (
        "Gate D evidence bundle: gate-d-local-evidence-bundle"
        in backend_evidence_visible
    )
    assert "Gate D handoff packet: gate-d-handoff-packet-local" in (
        backend_evidence_visible
    )
    assert "Artifact access performed: no" in backend_evidence_visible
    assert "Command execution performed by page: no" in backend_evidence_visible
    assert "Private data required: no" in backend_evidence_visible
    assert "Human-recorded narrow local pass: yes" in backend_evidence_visible
    assert (
        "Product Promise Alpha: narrow local pass recorded" in backend_evidence_visible
    )
    assert "traceback" not in backend_evidence_section.casefold()
    assert ".env" not in backend_evidence_section.casefold()
    assert "token" not in backend_evidence_section.casefold()


@pytest.mark.parametrize(
    "unsafe_source_status",
    [
        (
            "Session source: fixed fixture metadata",
            "Event source: fixed fixture metadata",
            "Alert source: fixed fixture metadata",
            "Archive source: fixed fixture metadata",
            "Gate D source: passed",
            "Transcript source: displayed",
            "Recording source: displayed",
            "Private source data read: yes",
            "Source refresh required: yes",
            "Product Promise Alpha passed",
        ),
        (
            "Session source: C:\\Users\\student\\secret-token-auth-profile",
            "Event source: https://meet.example.edu/class-room?token=private",
            "Alert source: file:///tmp/private-alerts.jsonl",
            "\\\\server\\share\\cookie-profile.json",
            "Good morning, everyone. I am going to take attendance",
            "transcript text: private class content",
            "generated-media: lecture.wav lecture.mp4 clip.png",
            "product judgment evidence satisfied",
        ),
        ("Session source: fixed fixture metadata",),
        (),
    ],
)
def test_static_demo_source_status_fails_closed_for_unsafe_values(
    monkeypatch,
    unsafe_source_status: tuple[str, ...],
) -> None:
    demo = _demo_module()

    def fake_source_status() -> tuple[str, ...]:
        return unsafe_source_status

    monkeypatch.setattr(
        demo,
        "_build_static_demo_source_status_lines",
        fake_source_status,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    source_section = _section_text(html, "Demo source status")
    source_visible = _visible_text(source_section)
    for expected in (
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
    ):
        assert expected in source_visible

    lowered = source_section.casefold()
    for forbidden in (
        "<script",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "secret",
        "token",
        "auth",
        "profile",
        "cookie",
        "meet.example",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "\\\\",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript text",
        "transcript source: displayed",
        "recording source: displayed",
        "private source data read: yes",
        "source refresh required: yes",
        "gate d source: passed",
        "product promise alpha passed",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered
    assert "<button" not in lowered
    _assert_no_event_handler_attributes(source_section)


def test_static_demo_source_status_fails_closed_for_helper_exception(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_source_status() -> tuple[str, ...]:
        raise RuntimeError("C:\\Users\\student\\.env token traceback")

    monkeypatch.setattr(
        demo,
        "_build_static_demo_source_status_lines",
        fake_source_status,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    source_section = _section_text(html, "Demo source status")
    source_visible = _visible_text(source_section)
    assert "Session source: fixed fixture metadata" in source_visible
    assert "Event source: fixed fixture metadata" in source_visible
    assert "Alert source: fixed fixture metadata" in source_visible
    assert "Archive source: fixed fixture metadata" in source_visible
    assert "Gate D source: local handoff metadata" in source_visible
    assert "Transcript source: not displayed" in source_visible
    assert "Recording source: not displayed" in source_visible
    assert "Private source data read: no" in source_visible
    assert "Source refresh required: no" in source_visible
    assert "Product Promise Alpha: narrow local pass recorded" in source_visible
    assert "traceback" not in source_section.casefold()
    assert ".env" not in source_section.casefold()
    assert "token" not in source_section.casefold()


@pytest.mark.parametrize(
    "unsafe_manual_review",
    [
        (
            "Review packet: public transcript",
            "Human product judgment: completed",
            "Final product judgment recorded: yes",
            "AI can complete product judgment: yes",
            "Gate D blocker: none",
            "Private data needed for review: yes",
            "Live services needed for review: yes",
            "Action execution allowed: yes",
            "Product Promise Alpha passed",
        ),
        (
            "Review packet: C:\\Users\\student\\secret-token-auth-profile",
            "https://meet.example.edu/class-room?token=private",
            "file:///tmp/private-review.jsonl",
            "\\\\server\\share\\cookie-profile.json",
            "Good morning, everyone. I am going to take attendance",
            "transcript text: private class content",
            "recording path: lecture.wav lecture.mp4 clip.png",
            "product judgment evidence satisfied",
        ),
        ("Review packet: local metadata only",),
        (),
    ],
)
def test_static_demo_manual_review_status_fails_closed_for_unsafe_values(
    monkeypatch,
    unsafe_manual_review: tuple[str, ...],
) -> None:
    demo = _demo_module()

    def fake_manual_review() -> tuple[str, ...]:
        return unsafe_manual_review

    monkeypatch.setattr(
        demo,
        "_build_static_demo_manual_review_status_lines",
        fake_manual_review,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    manual_review_section = _section_text(html, "Manual review status")
    manual_review_visible = _visible_text(manual_review_section)
    for expected in (
        "Review packet: local metadata only",
        "Human product judgment: narrow local pass recorded",
        "Product judgment storage written: no",
        "AI can complete product judgment: no",
        "Gate D human note: narrow local pass recorded",
        "Private data needed for review: no",
        "Live services needed for review: no",
        "Action execution allowed: no",
        "Product Promise Alpha: narrow local pass recorded",
    ):
        assert expected in manual_review_visible

    lowered = manual_review_section.casefold()
    for forbidden in (
        "<script",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "secret",
        "token",
        "auth",
        "profile",
        "cookie",
        "meet.example",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "\\\\",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript text",
        "recording path",
        "public transcript",
        "final product judgment recorded: yes",
        "ai can complete product judgment: yes",
        "private data needed for review: yes",
        "live services needed for review: yes",
        "action execution allowed: yes",
        "gate d blocker: none",
        "product promise alpha passed",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered
    assert "<button" not in lowered
    _assert_no_event_handler_attributes(manual_review_section)


def test_static_demo_manual_review_status_fails_closed_for_helper_exception(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_manual_review() -> tuple[str, ...]:
        raise RuntimeError("C:\\Users\\student\\.env token traceback")

    monkeypatch.setattr(
        demo,
        "_build_static_demo_manual_review_status_lines",
        fake_manual_review,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    manual_review_section = _section_text(html, "Manual review status")
    manual_review_visible = _visible_text(manual_review_section)
    assert "Review packet: local metadata only" in manual_review_visible
    assert "Human product judgment: narrow local pass recorded" in manual_review_visible
    assert "Product judgment storage written: no" in manual_review_visible
    assert "AI can complete product judgment: no" in manual_review_visible
    assert "Gate D human note: narrow local pass recorded" in manual_review_visible
    assert "Private data needed for review: no" in manual_review_visible
    assert "Live services needed for review: no" in manual_review_visible
    assert "Action execution allowed: no" in manual_review_visible
    assert "Product Promise Alpha: narrow local pass recorded" in manual_review_visible
    assert "traceback" not in manual_review_section.casefold()
    assert ".env" not in manual_review_section.casefold()
    assert "token" not in manual_review_section.casefold()


@pytest.mark.parametrize(
    "unsafe_checklist",
    [
        (
            "Session status visible: no",
            "Detected event summary visible: no",
            "Alert preview requires confirmation: no",
            "Archive/reviewer metadata visible: no",
            "Gate D blocker visible: none",
            "Human product judgment required: no",
            "Action execution allowed: yes",
            "Product Promise Alpha passed",
        ),
        (
            "Session status visible: C:\\Users\\student\\secret-token-auth-profile",
            "https://meet.example.edu/class-room?token=private",
            "file:///tmp/private-checklist.jsonl",
            "\\\\server\\share\\cookie-profile.json",
            "Good morning, everyone. I am going to take attendance",
            "transcript text: private class content",
            "recording path: lecture.wav lecture.mp4 clip.png",
            "product judgment evidence satisfied",
        ),
        ("Session status visible: yes",),
        (),
    ],
)
def test_static_demo_review_checklist_fails_closed_for_unsafe_values(
    monkeypatch,
    unsafe_checklist: tuple[str, ...],
) -> None:
    demo = _demo_module()

    def fake_checklist() -> tuple[str, ...]:
        return unsafe_checklist

    monkeypatch.setattr(
        demo,
        "_build_static_demo_review_checklist_lines",
        fake_checklist,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    checklist_section = _section_text(html, "Demo review checklist")
    checklist_visible = _visible_text(checklist_section)
    for expected in (
        "Session status visible: yes",
        "Detected event summary visible: yes",
        "Alert preview requires confirmation: yes",
        "Archive/reviewer metadata visible: yes",
        "Gate D human note visible: narrow local pass recorded",
        "Future broader/live product judgment required: yes",
        "Action execution allowed: no",
        "Product Promise Alpha: narrow local pass recorded",
    ):
        assert expected in checklist_visible

    lowered = checklist_section.casefold()
    for forbidden in (
        "<script",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "secret",
        "token",
        "auth",
        "profile",
        "cookie",
        "meet.example",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "\\\\",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript text",
        "recording path",
        "session status visible: no",
        "detected event summary visible: no",
        "alert preview requires confirmation: no",
        "archive/reviewer metadata visible: no",
        "gate d blocker visible: none",
        "human product judgment required: no",
        "action execution allowed: yes",
        "product promise alpha passed",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered
    assert "<button" not in lowered
    _assert_no_event_handler_attributes(checklist_section)


def test_static_demo_review_checklist_fails_closed_for_helper_exception(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_checklist() -> tuple[str, ...]:
        raise RuntimeError("C:\\Users\\student\\.env token traceback")

    monkeypatch.setattr(
        demo,
        "_build_static_demo_review_checklist_lines",
        fake_checklist,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    checklist_section = _section_text(html, "Demo review checklist")
    checklist_visible = _visible_text(checklist_section)
    assert "Session status visible: yes" in checklist_visible
    assert "Detected event summary visible: yes" in checklist_visible
    assert "Alert preview requires confirmation: yes" in checklist_visible
    assert "Archive/reviewer metadata visible: yes" in checklist_visible
    assert "Gate D human note visible: narrow local pass recorded" in checklist_visible
    assert "Future broader/live product judgment required: yes" in checklist_visible
    assert "Action execution allowed: no" in checklist_visible
    assert "Product Promise Alpha: narrow local pass recorded" in checklist_visible
    assert "traceback" not in checklist_section.casefold()
    assert ".env" not in checklist_section.casefold()
    assert "token" not in checklist_section.casefold()


@pytest.mark.parametrize(
    "unsafe_next_step",
    [
        (
            "Manual inspection required: no",
            "Product judgment recorded: yes",
            "AI can complete product judgment: yes",
            "AI can record product judgment: yes",
            "product_judgment_evidence_status: satisfactory",
            "Action execution allowed: yes",
            "Product Promise Alpha passed",
        ),
        (
            "Manual inspection required: C:\\Users\\student\\secret-token-auth-profile",
            "https://meet.example.edu/class-room?token=private",
            "file:///tmp/private-judgment.jsonl",
            "\\\\server\\share\\cookie-profile.json",
            "Good morning, everyone. I am going to take attendance",
            "transcript text: private class content",
            "recording path: lecture.wav lecture.mp4 clip.png",
            "product judgment evidence satisfied",
        ),
        ("Manual inspection completed: narrow local pass",),
        (),
    ],
)
def test_static_demo_human_judgment_next_step_fails_closed_for_unsafe_values(
    monkeypatch,
    unsafe_next_step: tuple[str, ...],
) -> None:
    demo = _demo_module()

    def fake_next_step() -> tuple[str, ...]:
        return unsafe_next_step

    monkeypatch.setattr(
        demo,
        "_build_static_demo_human_judgment_next_step_lines",
        fake_next_step,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    next_step_section = _section_text(html, "Human judgment next step")
    next_step_visible = _visible_text(next_step_section)
    for expected in (
        "Manual inspection completed: narrow local pass",
        "Product judgment recorded in checkpoint: yes",
        "AI can complete product judgment: no",
        "AI can record product judgment: no",
        "Human-recorded narrow local pass: yes",
        "Action execution allowed: no",
        "Product Promise Alpha: narrow local pass recorded",
    ):
        assert expected in next_step_visible

    lowered = next_step_section.casefold()
    for forbidden in (
        "<script",
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "action=",
        "method=",
        "formaction=",
        "name=",
        "value=",
        "secret",
        "token",
        "auth",
        "profile",
        "cookie",
        "meet.example",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "\\\\",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "good morning",
        "transcript text",
        "recording path",
        "manual inspection required: no",
        "product judgment recorded: yes",
        "ai can complete product judgment: yes",
        "ai can record product judgment: yes",
        "product_judgment_evidence_status: satisfactory",
        "action execution allowed: yes",
        "product promise alpha passed",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered
    assert "<button" not in lowered
    _assert_no_event_handler_attributes(next_step_section)


def test_static_demo_human_judgment_next_step_fails_closed_for_helper_exception(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_next_step() -> tuple[str, ...]:
        raise RuntimeError("C:\\Users\\student\\.env token traceback")

    monkeypatch.setattr(
        demo,
        "_build_static_demo_human_judgment_next_step_lines",
        fake_next_step,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    next_step_section = _section_text(html, "Human judgment next step")
    next_step_visible = _visible_text(next_step_section)
    assert "Manual inspection completed: narrow local pass" in next_step_visible
    assert "Product judgment recorded in checkpoint: yes" in next_step_visible
    assert "AI can complete product judgment: no" in next_step_visible
    assert "AI can record product judgment: no" in next_step_visible
    assert "Human-recorded narrow local pass: yes" in next_step_visible
    assert "Action execution allowed: no" in next_step_visible
    assert "Product Promise Alpha: narrow local pass recorded" in next_step_visible
    assert "traceback" not in next_step_section.casefold()
    assert ".env" not in next_step_section.casefold()
    assert "token" not in next_step_section.casefold()


@pytest.mark.parametrize(
    "unsafe_launch",
    [
        (
            "Static demo entrypoint: scripts/run_local_alpha_dashboard_static_demo.ps1",
            "CLI export command: local-alpha-dashboard-static-demo --output "
            "local-html-file",
            "Server started: yes",
            "Browser opened: yes",
            "Live delivery: yes",
            "Private data read: yes",
            "Gate D passed",
            "Product Promise Alpha passed",
        ),
        (
            "Static demo entrypoint: C:\\Users\\student\\secret-token-auth-profile",
            "CLI export command: https://meet.example.edu/class-room?token=private",
            "file:///tmp/async-scholar-local-alpha-dashboard.html",
            "\\\\server\\share\\cookie-profile.json",
            "Good morning, everyone. I am going to take attendance",
            "transcript text: private class content",
            "generated-media: lecture.wav lecture.mp4 clip.png",
            "product judgment evidence satisfied",
        ),
        ("Static demo entrypoint: scripts/run_local_alpha_dashboard_static_demo.ps1",),
        (),
    ],
)
def test_static_demo_local_launch_fails_closed_for_unsafe_values(
    monkeypatch,
    unsafe_launch: tuple[str, ...],
) -> None:
    demo = _demo_module()

    def fake_launch() -> tuple[str, ...]:
        return unsafe_launch

    monkeypatch.setattr(demo, "_build_static_demo_local_launch_lines", fake_launch)

    html = demo.build_local_alpha_dashboard_static_demo_html()

    launch_section = _section_text(html, "Local demo launch")
    launch_visible = _visible_text(launch_section)
    for expected in (
        "Static demo entrypoint: scripts/run_local_alpha_dashboard_static_demo.ps1",
        "CLI export command: local-alpha-dashboard-static-demo --output "
        "local-html-file",
        "Server started: no",
        "Browser opened: no",
        "Live delivery: no",
        "Private data read: no",
        "Gate D: narrow local pass recorded",
        "Product Promise Alpha: narrow local pass recorded",
    ):
        assert expected in launch_visible

    lowered = launch_section.casefold()
    for forbidden in (
        "server started: yes",
        "browser opened: yes",
        "live delivery: yes",
        "private data read: yes",
        "good morning",
        "transcript",
        "secret",
        "token",
        "auth",
        "profile",
        "cookie",
        "meet.example",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "\\\\",
        ".wav",
        ".mp4",
        ".png",
        "gate d passed",
        "product promise alpha passed",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered


def test_static_demo_local_launch_fails_closed_for_helper_exception(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_launch() -> tuple[str, ...]:
        raise RuntimeError("C:\\Users\\student\\.env token traceback")

    monkeypatch.setattr(demo, "_build_static_demo_local_launch_lines", fake_launch)

    html = demo.build_local_alpha_dashboard_static_demo_html()

    launch_section = _section_text(html, "Local demo launch")
    launch_visible = _visible_text(launch_section)
    assert (
        "Static demo entrypoint: scripts/run_local_alpha_dashboard_static_demo.ps1"
        in launch_visible
    )
    assert (
        "CLI export command: local-alpha-dashboard-static-demo --output "
        "local-html-file" in launch_visible
    )
    assert "Server started: no" in launch_visible
    assert "Browser opened: no" in launch_visible
    assert "Live delivery: no" in launch_visible
    assert "Private data read: no" in launch_visible
    assert "Gate D: narrow local pass recorded" in launch_visible
    assert "Product Promise Alpha: narrow local pass recorded" in launch_visible
    assert "traceback" not in launch_section.casefold()
    assert ".env" not in launch_section.casefold()
    assert "token" not in launch_section.casefold()


@pytest.mark.parametrize(
    "unsafe_strip",
    [
        (
            "Gate D: passed",
            "Product judgment: satisfied",
            "Session: completed",
            "Detected events: 2",
            "Alert: pending confirmation",
            "Live delivery: yes",
        ),
        (
            "Gate D: narrow local pass recorded",
            "Product Promise Alpha: passed",
            "product_judgment_evidence_status: satisfactory",
            "https://meet.example.edu/class-room?token=private",
            "D:\\private\\lecture.wav",
            "transcript text: Good morning, everyone",
        ),
        (
            "Gate D: narrow local pass recorded",
            "file:///tmp/async-scholar-local-alpha-dashboard.html",
            "\\\\server\\share\\cookie-profile.json",
            "C:/Users/student/private/events.jsonl",
            "generated-media: lecture.mp4 clip.png",
            "product judgment evidence satisfied",
        ),
        ("Gate D: narrow local pass recorded",),
        (),
    ],
)
def test_static_demo_summary_status_strip_fails_closed_for_unsafe_values(
    monkeypatch,
    unsafe_strip: tuple[str, ...],
) -> None:
    demo = _demo_module()

    def fake_strip() -> tuple[str, ...]:
        return unsafe_strip

    monkeypatch.setattr(
        demo, "_build_static_demo_summary_status_strip_lines", fake_strip
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    strip_html = _summary_status_strip_html(html)
    strip_text = _summary_status_strip_text(html)
    for expected in (
        "Gate D: narrow local pass recorded",
        "Product judgment: narrow local pass recorded",
        "Session: completed",
        "Detected events: 2",
        "Alert: pending confirmation",
        "Live delivery: no",
    ):
        assert expected in strip_text

    lowered = strip_html.casefold()
    for forbidden in (
        "gate d: passed",
        "product judgment: satisfied",
        "product promise alpha: passed",
        "product_judgment_evidence_status: satisfactory",
        "live delivery: yes",
        "good morning",
        "transcript",
        "secret",
        "token",
        "auth",
        "profile",
        "cookie",
        "meet.example",
        "http:",
        "https:",
        "file:",
        "c:\\",
        "c:/",
        "d:\\",
        "d:/",
        "\\\\",
        ".jsonl",
        ".wav",
        ".mp4",
        ".png",
        "gate d passed",
        "product promise alpha passed",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered


def test_static_demo_summary_status_strip_fails_closed_for_helper_exception(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_strip() -> tuple[str, ...]:
        raise RuntimeError("C:\\Users\\student\\.env token traceback")

    monkeypatch.setattr(
        demo, "_build_static_demo_summary_status_strip_lines", fake_strip
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    strip_html = _summary_status_strip_html(html)
    strip_text = _summary_status_strip_text(html)
    assert "Gate D: narrow local pass recorded" in strip_text
    assert "Product judgment: narrow local pass recorded" in strip_text
    assert "Session: completed" in strip_text
    assert "Detected events: 2" in strip_text
    assert "Alert: pending confirmation" in strip_text
    assert "Live delivery: no" in strip_text
    assert "traceback" not in strip_html.casefold()
    assert ".env" not in strip_html.casefold()
    assert "token" not in strip_html.casefold()


def test_static_demo_evidence_digest_fails_closed_for_pass_like_helper(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_packet() -> dict[str, object]:
        return {
            "handoff_packet_status": "passed C:\\Users\\student\\.env token",
            "local_gate_d_bundle_status": "passed",
            "satisfactory_evidence_count": True,
            "missing_evidence_count": "C:\\Users\\student\\secret.txt",
            "blocking_evidence": ["product_judgment_evidence", "auth-token"],
            "manual_product_judgment_required": False,
            "manual_product_judgment_recorded": True,
            "review_can_be_completed_by_ai": True,
            "gate_d_pass_claimed": True,
            "product_promise_alpha_pass_claimed": True,
        }

    monkeypatch.setattr(demo, "_build_local_gate_d_handoff_packet", fake_packet)

    html = demo.build_local_alpha_dashboard_static_demo_html()

    digest_section = _section_text(html, "Evidence digest")
    assert "Handoff status: Metadata aid only" in digest_section
    assert (
        "Local bundle status: Narrow local pass recorded in checkpoint"
        in digest_section
    )
    assert "Satisfactory evidence: 0" in digest_section
    assert "Missing evidence: 0" in digest_section
    assert "Narrow pass evidence: human-recorded checkpoint note" in digest_section
    assert "Manual product judgment completed: narrow local pass" in digest_section
    assert "Manual product judgment recorded in checkpoint: yes" in digest_section
    assert "AI can complete product judgment: no" in digest_section

    lowered = digest_section.casefold()
    for forbidden in (
        "passed",
        "secret",
        "token",
        "auth",
        ".env",
        "c:\\",
        "gate d passed",
        "product promise alpha passed",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered


def test_static_demo_html_helper_does_not_use_live_runner() -> None:
    demo = _demo_module()
    source = inspect.getsource(
        demo.build_local_alpha_dashboard_static_demo_html
    ).casefold()

    for forbidden in (
        "run_local_alpha_dashboard_demo",
        "render_local_alpha_dashboard_demo_page",
        "nicegui",
        "ui.run",
        "webbrowser",
        "subprocess",
    ):
        assert forbidden not in source


def test_static_demo_action_control_helper_preserves_static_scope() -> None:
    demo = _demo_module()
    source = (
        inspect.getsource(demo._safe_static_demo_action_control_lines)
        + inspect.getsource(demo._build_static_demo_action_control_lines)
        + inspect.getsource(demo._render_static_demo_action_control_item)
    ).casefold()

    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "onclick",
        "onchange",
        "onsubmit",
        "formaction",
        "ui.run",
        "webbrowser",
        "startfile",
        "subprocess.run",
        "dispatch_alert",
        "telegram",
        "desktop_notifier",
        "scheduler",
        "delete",
    ):
        assert forbidden not in source


def test_static_demo_archive_review_status_helper_preserves_static_scope() -> None:
    demo = _demo_module()
    source = (
        inspect.getsource(demo._safe_static_demo_archive_review_status_lines)
        + inspect.getsource(demo._build_static_demo_archive_review_status_lines)
    ).casefold()

    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "onclick",
        "onchange",
        "onsubmit",
        "formaction",
        "ui.run",
        "webbrowser",
        "startfile",
        "subprocess.run",
        "run_local_alpha_dashboard_demo",
        "dispatch_alert",
        "telegram",
        "desktop_notifier",
        "scheduler",
        "delete/export execution: yes",
    ):
        assert forbidden not in source


def test_static_demo_review_checklist_helper_preserves_static_scope() -> None:
    demo = _demo_module()
    source = (
        inspect.getsource(demo._safe_static_demo_review_checklist_lines)
        + inspect.getsource(demo._build_static_demo_review_checklist_lines)
    ).casefold()

    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "onclick",
        "onchange",
        "onsubmit",
        "formaction",
        "ui.run",
        "webbrowser",
        "startfile",
        "subprocess.run",
        "run_local_alpha_dashboard_demo",
        "dispatch_alert",
        "telegram",
        "desktop_notifier",
        "scheduler",
        "delete",
        "session status visible: no",
        "detected event summary visible: no",
        "alert preview requires confirmation: no",
        "archive/reviewer metadata visible: no",
        "gate d blocker visible: none",
        "human product judgment required: no",
        "action execution allowed: yes",
    ):
        assert forbidden not in source


def test_static_demo_human_judgment_next_step_helper_preserves_static_scope() -> None:
    demo = _demo_module()
    source = (
        inspect.getsource(demo._safe_static_demo_human_judgment_next_step_lines)
        + inspect.getsource(demo._build_static_demo_human_judgment_next_step_lines)
    ).casefold()

    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "onclick",
        "onchange",
        "onsubmit",
        "formaction",
        "ui.run",
        "webbrowser",
        "startfile",
        "subprocess.run",
        "run_local_alpha_dashboard_demo",
        "dispatch_alert",
        "telegram",
        "desktop_notifier",
        "scheduler",
        "delete",
        "manual inspection required: no",
        "product judgment recorded: yes",
        "ai can complete product judgment: yes",
        "ai can record product judgment: yes",
        "action execution allowed: yes",
    ):
        assert forbidden not in source


def test_static_demo_source_status_helper_preserves_static_scope() -> None:
    demo = _demo_module()
    source = (
        inspect.getsource(demo._safe_static_demo_source_status_lines)
        + inspect.getsource(demo._build_static_demo_source_status_lines)
    ).casefold()

    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "onclick",
        "onchange",
        "onsubmit",
        "formaction",
        "ui.run",
        "webbrowser",
        "startfile",
        "subprocess.run",
        "run_local_alpha_dashboard_demo",
        "dispatch_alert",
        "telegram",
        "desktop_notifier",
        "scheduler",
        "delete",
        "transcript source: displayed",
        "recording source: displayed",
        "private source data read: yes",
        "source refresh required: yes",
    ):
        assert forbidden not in source


def test_static_demo_local_launch_helper_preserves_static_scope() -> None:
    demo = _demo_module()
    source = (
        inspect.getsource(demo._safe_static_demo_local_launch_lines)
        + inspect.getsource(demo._build_static_demo_local_launch_lines)
    ).casefold()

    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "href=",
        "src=",
        "onclick",
        "onchange",
        "onsubmit",
        "formaction",
        "ui.run",
        "webbrowser",
        "startfile",
        "subprocess.run",
        "run_local_alpha_dashboard_demo",
        "dispatch_alert",
        "telegram",
        "desktop_notifier",
        "scheduler",
        "delete",
    ):
        assert forbidden not in source


def test_static_demo_backend_evidence_trail_helper_preserves_static_scope() -> None:
    demo = _demo_module()
    source = (
        inspect.getsource(demo._safe_static_demo_backend_evidence_trail_lines)
        + inspect.getsource(demo._build_static_demo_backend_evidence_trail_lines)
    ).casefold()

    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "onclick",
        "onchange",
        "onsubmit",
        "formaction",
        "ui.run",
        "webbrowser",
        "startfile",
        "subprocess.run",
        "run_local_alpha_dashboard_demo",
        "dispatch_alert",
        "telegram",
        "desktop_notifier",
        "scheduler",
        "delete",
        "open(",
        "read_text",
        "write_text",
        "artifact access performed: yes",
        "command execution performed by page: yes",
        "private data required: yes",
        "gate d evidence bundle: passed",
        "product_judgment_evidence_status: satisfactory",
    ):
        assert forbidden not in source


@pytest.mark.parametrize(
    "unsafe_runbook",
    [
        (
            "1. Run fixture/local demo evidence",
            "2. Inspect dashboard safety status",
            "3. Export static local alpha dashboard",
            "4. Review Gate D evidence bundle",
            "5. Review Gate D handoff packet",
            "Commands are copied manually; the page executes commands",
            "Artifacts are opened by the page",
            "Private data required: yes",
            "Gate D passed",
            "Product Promise Alpha passed",
        ),
        (
            "Traceback C:\\Users\\student\\.env token",
            "https://meet.example.edu/class-room?token=private",
            "cookie-value",
            "auth-state",
            "browser profile",
            "Good morning, everyone. I am going to take attendance",
            r"C:\private\lecture.wav",
            r"C:\private\lecture.mp4",
            "product_judgment_evidence_status: satisfactory",
            "product judgment evidence satisfied",
        ),
        (),
    ],
)
def test_static_demo_runbook_fails_closed_for_unsafe_values(
    monkeypatch,
    unsafe_runbook: tuple[str, ...],
) -> None:
    demo = _demo_module()

    def fake_runbook() -> tuple[str, ...]:
        return unsafe_runbook

    monkeypatch.setattr(demo, "_build_static_demo_runbook_lines", fake_runbook)

    html = demo.build_local_alpha_dashboard_static_demo_html()

    runbook_section = _section_text(html, "Local alpha demo runbook")
    runbook_visible = _visible_text(runbook_section)
    for expected in STATIC_DEMO_RUNBOOK_LINES:
        assert expected in runbook_visible
    assert "Metadata unavailable." not in runbook_section
    lowered = runbook_section.casefold()
    for forbidden in (
        "<script",
        "<a ",
        "<button",
        "<form",
        "<input",
        "href=",
        "src=",
        "action=",
        "method=",
        "page executes commands",
        "artifacts are opened by the page",
        "private data required: yes",
        "meet.example",
        ".env",
        "cookie-value",
        "token=private",
        "auth-state",
        "browser profile",
        "good morning",
        "traceback",
        ".wav",
        ".mp4",
        "gate d passed",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered
    assert re.search(r"[a-z]:\\", runbook_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(runbook_section)


def test_static_demo_runbook_fails_closed_for_helper_exception(monkeypatch) -> None:
    demo = _demo_module()

    def fake_runbook() -> tuple[str, ...]:
        raise RuntimeError("Traceback C:\\Users\\student\\.env token")

    monkeypatch.setattr(demo, "_build_static_demo_runbook_lines", fake_runbook)

    html = demo.build_local_alpha_dashboard_static_demo_html()

    runbook_section = _section_text(html, "Local alpha demo runbook")
    runbook_visible = _visible_text(runbook_section)
    for expected in STATIC_DEMO_RUNBOOK_LINES:
        assert expected in runbook_visible
    assert "Traceback" not in runbook_section
    assert ".env" not in runbook_section
    assert "token" not in runbook_section.casefold()


def test_static_demo_runbook_helper_preserves_static_scope() -> None:
    demo = _demo_module()
    source = (
        inspect.getsource(demo._safe_static_demo_runbook_lines)
        + inspect.getsource(demo._build_static_demo_runbook_lines)
    ).casefold()

    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "onclick",
        "onchange",
        "onsubmit",
        "formaction",
        "ui.run",
        "webbrowser",
        "startfile",
        "subprocess.run",
        "run_local_alpha_dashboard_demo",
        "dispatch_alert",
        "telegram",
        "desktop_notifier",
        "scheduler",
        "delete",
        "open(",
        "read_text",
        "write_text",
        "page executes commands",
        "artifacts are opened by the page",
        "private data required: yes",
        "gate d passed",
        "product_judgment_evidence_status: satisfactory",
    ):
        assert forbidden not in source


def test_static_demo_artifact_summary_allows_only_exact_fixture_metadata_line() -> None:
    demo = _demo_module()

    assert demo._safe_static_demo_artifact_summary_lines() == (
        STATIC_DEMO_ARTIFACT_SUMMARY_LINES
    )
    assert demo._static_demo_text_is_unsafe(
        "Fixture artifacts: events.jsonl, alerts.log, reviewer.md"
    )


@pytest.mark.parametrize(
    "unsafe_artifact_summary",
    [
        (
            "Fixture artifacts: private.jsonl, alerts.log, reviewer.md",
            "Static dashboard artifact: C:\\Users\\student\\dashboard.html",
            "Gate D evidence bundle: stdout metadata only",
            "Gate D handoff packet: stdout metadata only",
            "Archive/reviewer contents displayed: yes",
            "Private paths displayed: yes",
            "Artifact opening performed: yes",
            "Generated artifacts committed: yes",
            "Gate D passed",
            "Product Promise Alpha passed",
        ),
        (
            "Traceback C:\\Users\\student\\.env token",
            "https://meet.example.edu/class-room?token=private",
            "cookie-value",
            "auth-state",
            "browser profile",
            "Good morning, everyone. I am going to take attendance",
            r"C:\private\lecture.wav",
            r"C:\private\lecture.mp4",
            "product_judgment_evidence_status: satisfactory",
            "product judgment evidence satisfied",
        ),
        (),
    ],
)
def test_static_demo_artifact_summary_fails_closed_for_unsafe_values(
    monkeypatch,
    unsafe_artifact_summary: tuple[str, ...],
) -> None:
    demo = _demo_module()

    def fake_artifact_summary() -> tuple[str, ...]:
        return unsafe_artifact_summary

    monkeypatch.setattr(
        demo,
        "_build_static_demo_artifact_summary_lines",
        fake_artifact_summary,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    artifact_summary_section = _section_text(html, "Local alpha artifact summary")
    artifact_summary_visible = _visible_text(artifact_summary_section)
    for expected in STATIC_DEMO_ARTIFACT_SUMMARY_LINES:
        assert expected in artifact_summary_visible
    assert "Metadata unavailable." not in artifact_summary_section
    lowered = artifact_summary_section.casefold()
    for forbidden in (
        "<script",
        "<a ",
        "<button",
        "<form",
        "<input",
        "href=",
        "src=",
        "action=",
        "method=",
        "private.jsonl",
        "c:\\",
        "https:",
        "meet.example",
        ".env",
        "cookie",
        "token",
        "auth",
        "profile",
        "good morning",
        "traceback",
        ".wav",
        ".mp4",
        "archive/reviewer contents displayed: yes",
        "private paths displayed: yes",
        "artifact opening performed: yes",
        "generated artifacts committed: yes",
        "gate d passed",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered
    assert re.search(r"[a-z]:\\", artifact_summary_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(artifact_summary_section)


def test_static_demo_artifact_summary_fails_closed_for_helper_exception(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_artifact_summary() -> tuple[str, ...]:
        raise RuntimeError("Traceback C:\\Users\\student\\.env token")

    monkeypatch.setattr(
        demo,
        "_build_static_demo_artifact_summary_lines",
        fake_artifact_summary,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    artifact_summary_section = _section_text(html, "Local alpha artifact summary")
    artifact_summary_visible = _visible_text(artifact_summary_section)
    for expected in STATIC_DEMO_ARTIFACT_SUMMARY_LINES:
        assert expected in artifact_summary_visible
    assert "Traceback" not in artifact_summary_section
    assert ".env" not in artifact_summary_section
    assert "token" not in artifact_summary_section.casefold()


def test_static_demo_artifact_summary_helper_preserves_static_scope() -> None:
    demo = _demo_module()
    source = (
        inspect.getsource(demo._safe_static_demo_artifact_summary_lines)
        + inspect.getsource(demo._build_static_demo_artifact_summary_lines)
    ).casefold()

    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "onclick",
        "onchange",
        "onsubmit",
        "formaction",
        "ui.run",
        "webbrowser",
        "startfile",
        "subprocess.run",
        "run_local_alpha_dashboard_demo",
        "dispatch_alert",
        "telegram",
        "desktop_notifier",
        "scheduler",
        "delete",
        "open(",
        "read_text",
        "write_text",
        "archive/reviewer contents displayed: yes",
        "private paths displayed: yes",
        "artifact opening performed: yes",
        "generated artifacts committed: yes",
        "gate d passed",
        "product_judgment_evidence_status: satisfactory",
    ):
        assert forbidden not in source


@pytest.mark.parametrize(
    "unsafe_fixture_handoff",
    [
        (
            "Wrapper: C:\\Users\\student\\secret-token-auth-profile.ps1",
            "Fixture evidence: private transcript command",
            "Dashboard export: https://meet.example.edu/class-room",
            "Gate D bundle check: gate-d-local-evidence-bundle",
            "Gate D handoff packet check: gate-d-handoff-packet-local",
            "Raw command output displayed: yes",
            "User paths displayed: yes",
            "Browser/server launched by page: yes",
            "Product judgment recorded: yes",
            "Gate D passed",
            "Product Promise Alpha passed",
        ),
        (
            "Traceback C:\\Users\\student\\.env token",
            "https://meet.example.edu/class-room?token=private",
            "cookie-value",
            "auth-state",
            "browser profile",
            "Good morning, everyone. I am going to take attendance",
            r"C:\private\lecture.wav",
            r"C:\private\lecture.mp4",
            "product_judgment_evidence_status: satisfactory",
            "product judgment evidence satisfied",
            "Product Promise Alpha passed",
        ),
        (),
    ],
)
def test_static_demo_fixture_handoff_fails_closed_for_unsafe_values(
    monkeypatch,
    unsafe_fixture_handoff: tuple[str, ...],
) -> None:
    demo = _demo_module()

    def fake_fixture_handoff() -> tuple[str, ...]:
        return unsafe_fixture_handoff

    monkeypatch.setattr(
        demo,
        "_build_static_demo_fixture_handoff_lines",
        fake_fixture_handoff,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    fixture_handoff_section = _section_text(html, "One-command fixture demo handoff")
    fixture_handoff_visible = _visible_text(fixture_handoff_section)
    for expected in STATIC_DEMO_FIXTURE_HANDOFF_LINES:
        assert expected in fixture_handoff_visible
    assert "Metadata unavailable." not in fixture_handoff_section
    lowered = fixture_handoff_section.casefold()
    for forbidden in (
        "<script",
        "<a ",
        "<button",
        "<form",
        "<input",
        "href=",
        "src=",
        "action=",
        "method=",
        "private_summary",
        "c:\\",
        "https:",
        "meet.example",
        ".env",
        "cookie",
        "token",
        "auth",
        "profile",
        "good morning",
        "traceback",
        ".wav",
        ".mp4",
        "raw command output displayed: yes",
        "user paths displayed: yes",
        "browser/server launched by page: yes",
        "product judgment recorded: yes",
        "gate d passed",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered
    assert re.search(r"[a-z]:\\", fixture_handoff_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(fixture_handoff_section)


def test_static_demo_fixture_handoff_fails_closed_for_helper_exception(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_fixture_handoff() -> tuple[str, ...]:
        raise RuntimeError("Traceback C:\\Users\\student\\.env token")

    monkeypatch.setattr(
        demo,
        "_build_static_demo_fixture_handoff_lines",
        fake_fixture_handoff,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    fixture_handoff_section = _section_text(html, "One-command fixture demo handoff")
    fixture_handoff_visible = _visible_text(fixture_handoff_section)
    for expected in STATIC_DEMO_FIXTURE_HANDOFF_LINES:
        assert expected in fixture_handoff_visible
    assert "Traceback" not in fixture_handoff_section
    assert ".env" not in fixture_handoff_section
    assert "token" not in fixture_handoff_section.casefold()


def test_static_demo_fixture_handoff_helper_preserves_static_scope() -> None:
    demo = _demo_module()
    source = (
        inspect.getsource(demo._safe_static_demo_fixture_handoff_lines)
        + inspect.getsource(demo._build_static_demo_fixture_handoff_lines)
    ).casefold()

    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "onclick",
        "onchange",
        "onsubmit",
        "formaction",
        "ui.run",
        "webbrowser",
        "startfile",
        "subprocess.run",
        "dispatch_alert",
        "telegram",
        "desktop_notifier",
        "scheduler",
        "delete",
        "open(",
        "read_text",
        "write_text",
        "raw command output displayed: yes",
        "user paths displayed: yes",
        "browser/server launched by page: yes",
        "product judgment recorded: yes",
        "gate d passed",
        "product_judgment_evidence_status: satisfactory",
    ):
        assert forbidden not in source


@pytest.mark.parametrize(
    "unsafe_summary_export",
    [
        (
            "Summary export: C:\\Users\\student\\secret-token-auth-profile.json",
            "Summary kind: private_summary",
            "Fixture artifacts generated: yes",
            "Static dashboard generated: yes",
            "Raw command output included: yes",
            "Private paths included: yes",
            "Browser/server launched: yes",
            "Live delivery performed: yes",
            "Product judgment recorded: yes",
            "Gate D evidence bundle: passed",
            "Gate D handoff packet: completed",
            "Gate D passed",
            "Product Promise Alpha passed",
        ),
        (
            "Traceback C:\\Users\\student\\.env token",
            "https://meet.example.edu/class-room?token=private",
            "cookie-value",
            "auth-state",
            "browser profile",
            "Good morning, everyone. I am going to take attendance",
            r"C:\private\lecture.wav",
            r"C:\private\lecture.mp4",
            "product_judgment_evidence_status: satisfactory",
            "product judgment evidence satisfied",
            "Product Promise Alpha passed",
        ),
        (),
    ],
)
def test_static_demo_fixture_summary_export_fails_closed_for_unsafe_values(
    monkeypatch,
    unsafe_summary_export: tuple[str, ...],
) -> None:
    demo = _demo_module()

    def fake_summary_export() -> tuple[str, ...]:
        return unsafe_summary_export

    monkeypatch.setattr(
        demo,
        "_build_static_demo_fixture_summary_export_lines",
        fake_summary_export,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    summary_export_section = _section_text(html, "Fixture demo summary export")
    summary_export_visible = _visible_text(summary_export_section)
    for expected in STATIC_DEMO_FIXTURE_SUMMARY_EXPORT_LINES:
        assert expected in summary_export_visible
    assert "Metadata unavailable." not in summary_export_section
    lowered = summary_export_section.casefold()
    for forbidden in (
        "<script",
        "<a ",
        "<button",
        "<form",
        "<input",
        "href=",
        "src=",
        "action=",
        "method=",
        "private_summary",
        "c:\\",
        "https:",
        "meet.example",
        ".env",
        "cookie",
        "token",
        "auth",
        "profile",
        "good morning",
        "traceback",
        ".wav",
        ".mp4",
        "raw command output included: yes",
        "private paths included: yes",
        "browser/server launched: yes",
        "live delivery performed: yes",
        "product judgment recorded: yes",
        "gate d evidence bundle: passed",
        "gate d handoff packet: completed",
        "gate d passed",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered
    assert re.search(r"[a-z]:\\", summary_export_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(summary_export_section)


def test_static_demo_fixture_summary_export_fails_closed_for_helper_exception(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_summary_export() -> tuple[str, ...]:
        raise RuntimeError("Traceback C:\\Users\\student\\.env token")

    monkeypatch.setattr(
        demo,
        "_build_static_demo_fixture_summary_export_lines",
        fake_summary_export,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    summary_export_section = _section_text(html, "Fixture demo summary export")
    summary_export_visible = _visible_text(summary_export_section)
    for expected in STATIC_DEMO_FIXTURE_SUMMARY_EXPORT_LINES:
        assert expected in summary_export_visible
    assert "Traceback" not in summary_export_section
    assert ".env" not in summary_export_section
    assert "token" not in summary_export_section.casefold()


def test_static_demo_fixture_summary_export_helper_preserves_static_scope() -> None:
    demo = _demo_module()
    source = (
        inspect.getsource(demo._safe_static_demo_fixture_summary_export_lines)
        + inspect.getsource(demo._build_static_demo_fixture_summary_export_lines)
    ).casefold()

    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "onclick",
        "onchange",
        "onsubmit",
        "formaction",
        "ui.run",
        "webbrowser",
        "startfile",
        "subprocess.run",
        "dispatch_alert",
        "telegram",
        "desktop_notifier",
        "scheduler",
        "delete",
        "open(",
        "json.load",
        "read_text",
        "write_text",
        "raw command output included: yes",
        "private paths included: yes",
        "browser/server launched: yes",
        "live delivery performed: yes",
        "product judgment recorded: yes",
        "gate d passed",
        "product_judgment_evidence_status: satisfactory",
    ):
        assert forbidden not in source


@pytest.mark.parametrize(
    "unsafe_gate_d_safety_status",
    [
        (
            "Gate D status: passed",
            "Blocking evidence: none",
            "Manual product judgment required: no",
            "Product judgment recorded: yes",
            "AI can complete product judgment: yes",
            "Real online monitoring approved: yes",
            "Browser/auth/profile access: yes",
            "Loopback/system audio access: yes",
            "Live delivery performed: yes",
            "Autonomous participation: yes",
            "Academic answers: yes",
            "Product Promise Alpha: passed",
        ),
        (
            "Traceback C:\\Users\\student\\.env token",
            "https://meet.example.edu/class-room?token=private",
            "cookie-value",
            "auth-state",
            "browser profile",
            "Good morning, everyone. I am going to take attendance",
            r"C:\private\lecture.wav",
            r"C:\private\lecture.mp4",
            "product_judgment_evidence_status: satisfactory",
            "product judgment evidence satisfied",
            "Product Promise Alpha passed",
        ),
        (),
    ],
)
def test_static_demo_gate_d_safety_status_fails_closed_for_unsafe_values(
    monkeypatch,
    unsafe_gate_d_safety_status: tuple[str, ...],
) -> None:
    demo = _demo_module()

    def fake_gate_d_safety_status() -> tuple[str, ...]:
        return unsafe_gate_d_safety_status

    monkeypatch.setattr(
        demo,
        "_build_static_demo_gate_d_safety_status_lines",
        fake_gate_d_safety_status,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    gate_d_safety_status_section = _section_text(html, "Gate D safety status")
    gate_d_safety_status_visible = _visible_text(gate_d_safety_status_section)
    for expected in STATIC_DEMO_GATE_D_SAFETY_STATUS_LINES:
        assert expected in gate_d_safety_status_visible
    assert "Metadata unavailable." not in gate_d_safety_status_section
    lowered = gate_d_safety_status_section.casefold()
    for forbidden in (
        "<script",
        "<a ",
        "<button",
        "<form",
        "<input",
        "href=",
        "src=",
        "action=",
        "method=",
        "c:\\",
        "https:",
        "meet.example",
        ".env",
        "cookie-value",
        "token=private",
        "auth-state",
        "browser profile",
        "good morning",
        "traceback",
        ".wav",
        ".mp4",
        "gate d status: passed",
        "manual product judgment required: no",
        "product judgment recorded: yes",
        "ai can complete product judgment: yes",
        "real online monitoring approved: yes",
        "browser/auth/profile/cookies/tokens approved: yes",
        "audio/hardware/loopback approved: yes",
        "live delivery approved: yes",
        "autonomous participation approved: yes",
        "academic-answer behavior approved: yes",
        "product promise alpha: passed",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered
    assert (
        re.search(r"[a-z]:\\", gate_d_safety_status_section, flags=re.IGNORECASE)
        is None
    )
    _assert_no_event_handler_attributes(gate_d_safety_status_section)


def test_static_demo_gate_d_safety_status_fails_closed_for_helper_exception(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_gate_d_safety_status() -> tuple[str, ...]:
        raise RuntimeError("Traceback C:\\Users\\student\\.env token")

    monkeypatch.setattr(
        demo,
        "_build_static_demo_gate_d_safety_status_lines",
        fake_gate_d_safety_status,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    gate_d_safety_status_section = _section_text(html, "Gate D safety status")
    gate_d_safety_status_visible = _visible_text(gate_d_safety_status_section)
    for expected in STATIC_DEMO_GATE_D_SAFETY_STATUS_LINES:
        assert expected in gate_d_safety_status_visible
    assert "Traceback" not in gate_d_safety_status_section
    assert ".env" not in gate_d_safety_status_section
    assert "token=private" not in gate_d_safety_status_section.casefold()
    assert "cookie-value" not in gate_d_safety_status_section.casefold()


def test_static_demo_gate_d_safety_status_helper_preserves_static_scope() -> None:
    demo = _demo_module()
    source = (
        inspect.getsource(demo._safe_static_demo_gate_d_safety_status_lines)
        + inspect.getsource(demo._build_static_demo_gate_d_safety_status_lines)
    ).casefold()

    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "onclick",
        "onchange",
        "onsubmit",
        "formaction",
        "ui.run",
        "webbrowser",
        "startfile",
        "subprocess",
        "dispatch_alert",
        "telegram",
        "desktop_notifier",
        "scheduler",
        "delete",
        "export",
        "open(",
        "json.load",
        "read_text",
        "write_text",
        "gate d status: passed",
        "manual product judgment required: no",
        "product judgment recorded: yes",
        "real online monitoring approved: yes",
        "live delivery performed: yes",
        "autonomous participation: yes",
        "academic answers: yes",
        "product promise alpha: passed",
        "product_judgment_evidence_status: satisfactory",
    ):
        assert forbidden not in source


@pytest.mark.parametrize(
    "unsafe_readiness_checklist",
    [
        (
            "Fixture/local demo available: no",
            "Static dashboard export available: no",
            "Session status visible: no",
            "Detected event summary visible: no",
            "Alert preview requires confirmation: no",
            "Archive/reviewer summary visible: no",
            "Gate D safety status visible: no",
            "Product judgment required: no",
            "Product Promise Alpha passed",
        ),
        (
            "Traceback C:\\Users\\student\\.env token",
            "https://meet.example.edu/class-room?token=private",
            "cookie-value",
            "auth-state",
            "browser profile",
            "Good morning, everyone. I am going to take attendance",
            r"C:\private\lecture.wav",
            r"C:\private\lecture.mp4",
            "raw command output included: yes",
            "product_judgment_evidence_status: satisfactory",
            "product judgment evidence satisfied",
        ),
        (),
    ],
)
def test_static_demo_readiness_checklist_fails_closed_for_unsafe_values(
    monkeypatch,
    unsafe_readiness_checklist: tuple[str, ...],
) -> None:
    demo = _demo_module()

    def fake_readiness_checklist() -> tuple[str, ...]:
        return unsafe_readiness_checklist

    monkeypatch.setattr(
        demo,
        "_build_static_demo_readiness_checklist_lines",
        fake_readiness_checklist,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    readiness_section = _section_text(html, "Local alpha demo readiness checklist")
    readiness_visible = _visible_text(readiness_section)
    for expected in STATIC_DEMO_READINESS_CHECKLIST_LINES:
        assert expected in readiness_visible
    assert "Metadata unavailable." not in readiness_section
    lowered = readiness_section.casefold()
    for forbidden in (
        "<script",
        "<a ",
        "<button",
        "<form",
        "<input",
        "href=",
        "src=",
        "action=",
        "method=",
        "c:\\",
        "https:",
        "meet.example",
        ".env",
        "cookie",
        "token",
        "auth",
        "profile",
        "good morning",
        "traceback",
        ".wav",
        ".mp4",
        "raw command output included: yes",
        "fixture/local demo available: no",
        "static dashboard export available: no",
        "session status visible: no",
        "detected event summary visible: no",
        "alert preview requires confirmation: no",
        "archive/reviewer summary visible: no",
        "gate d safety status visible: no",
        "product judgment required: no",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered
    assert re.search(r"[a-z]:\\", readiness_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(readiness_section)


def test_static_demo_readiness_checklist_fails_closed_for_helper_exception(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_readiness_checklist() -> tuple[str, ...]:
        raise RuntimeError("Traceback C:\\Users\\student\\.env token")

    monkeypatch.setattr(
        demo,
        "_build_static_demo_readiness_checklist_lines",
        fake_readiness_checklist,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    readiness_section = _section_text(html, "Local alpha demo readiness checklist")
    readiness_visible = _visible_text(readiness_section)
    for expected in STATIC_DEMO_READINESS_CHECKLIST_LINES:
        assert expected in readiness_visible
    assert "Traceback" not in readiness_section
    assert ".env" not in readiness_section
    assert "token" not in readiness_section.casefold()


def test_static_demo_readiness_checklist_helper_preserves_static_scope() -> None:
    demo = _demo_module()
    source = (
        inspect.getsource(demo._safe_static_demo_readiness_checklist_lines)
        + inspect.getsource(demo._build_static_demo_readiness_checklist_lines)
    ).casefold()

    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "onclick",
        "onchange",
        "onsubmit",
        "formaction",
        "ui.run",
        "webbrowser",
        "startfile",
        "subprocess.run",
        "run_local_alpha_dashboard_demo",
        "dispatch_alert",
        "telegram",
        "desktop_notifier",
        "scheduler",
        "delete/export execution: yes",
        "fixture/local demo available: no",
        "static dashboard export available: no",
        "session status visible: no",
        "detected event summary visible: no",
        "alert preview requires confirmation: no",
        "archive/reviewer summary visible: no",
        "gate d safety status visible: no",
        "product judgment required: no",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
    ):
        assert forbidden not in source


@pytest.mark.parametrize(
    "unsafe_handoff_lines",
    [
        (
            "Product judgment: passed",
            "Human reviewer required: no",
            "AI can record pass judgment: yes",
            "Gate D blocking evidence: none",
            "Evidence source: real online monitoring",
            "Static dashboard available: no",
            "Gate D handoff packet available: no",
            "Real online monitoring approved: yes",
            "Product Promise Alpha passed: yes",
        ),
        (
            "Traceback C:\\Users\\student\\.env token",
            "https://meet.example.edu/class-room?token=private",
            "cookie-value",
            "auth-state",
            "browser profile",
            "Good morning, everyone. I am going to take attendance",
            r"C:\private\lecture.wav",
            r"C:\private\lecture.mp4",
            "raw command output included: yes",
            "product_judgment_evidence_status: satisfactory",
            "product judgment evidence satisfied",
        ),
        (),
    ],
)
def test_static_demo_human_judgment_handoff_fails_closed_for_unsafe_values(
    monkeypatch,
    unsafe_handoff_lines: tuple[str, ...],
) -> None:
    demo = _demo_module()

    def fake_handoff_lines() -> tuple[str, ...]:
        return unsafe_handoff_lines

    monkeypatch.setattr(
        demo,
        "_build_static_demo_human_judgment_handoff_lines",
        fake_handoff_lines,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    handoff_section = _section_text(html, "Human judgment handoff")
    handoff_visible = _visible_text(handoff_section)
    for expected in STATIC_DEMO_HUMAN_JUDGMENT_HANDOFF_LINES:
        assert expected in handoff_visible
    assert "Metadata unavailable." not in handoff_section
    assert "Product Promise Alpha: narrow local pass recorded" in handoff_section
    lowered = handoff_section.casefold()
    for forbidden in (
        "<script",
        "<a ",
        "<button",
        "<form",
        "<input",
        "href=",
        "src=",
        "action=",
        "method=",
        "c:\\",
        "https:",
        "meet.example",
        ".env",
        "cookie",
        "token",
        "auth",
        "profile",
        "good morning",
        "traceback",
        ".wav",
        ".mp4",
        "raw command output included: yes",
        "product judgment: passed",
        "human reviewer required: no",
        "ai can record pass judgment: yes",
        "gate d blocking evidence: none",
        "evidence source: real online monitoring",
        "static dashboard available: no",
        "gate d handoff packet available: no",
        "real online monitoring approved: yes",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered
    assert re.search(r"[a-z]:\\", handoff_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(handoff_section)


def test_static_demo_human_judgment_handoff_fails_closed_for_helper_exception(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_handoff_lines() -> tuple[str, ...]:
        raise RuntimeError("Traceback C:\\Users\\student\\.env token")

    monkeypatch.setattr(
        demo,
        "_build_static_demo_human_judgment_handoff_lines",
        fake_handoff_lines,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    handoff_section = _section_text(html, "Human judgment handoff")
    handoff_visible = _visible_text(handoff_section)
    for expected in STATIC_DEMO_HUMAN_JUDGMENT_HANDOFF_LINES:
        assert expected in handoff_visible
    assert "Traceback" not in handoff_section
    assert ".env" not in handoff_section
    assert "token" not in handoff_section.casefold()


def test_static_demo_human_judgment_handoff_helper_preserves_static_scope() -> None:
    demo = _demo_module()
    source = (
        inspect.getsource(demo._safe_static_demo_human_judgment_handoff_lines)
        + inspect.getsource(demo._build_static_demo_human_judgment_handoff_lines)
    ).casefold()

    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "onclick",
        "onchange",
        "onsubmit",
        "formaction",
        "ui.run",
        "webbrowser",
        "startfile",
        "subprocess.run",
        "run_local_alpha_dashboard_demo",
        "dispatch_alert",
        "telegram",
        "desktop_notifier",
        "scheduler",
        "delete/export execution: yes",
        "product judgment: passed",
        "human reviewer required: no",
        "ai can record pass judgment: yes",
        "gate d blocking evidence: none",
        "evidence source: real online monitoring",
        "static dashboard available: no",
        "gate d handoff packet available: no",
        "real online monitoring approved: yes",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
    ):
        assert forbidden not in source


@pytest.mark.parametrize(
    "unsafe_product_loop_lines",
    [
        (
            "Product loop: real meeting to reviewer",
            "Fixture input: private transcript",
            "Session status: failed",
            "Detected events: 0",
            "Alert preview: sent",
            "Archive/reviewer: transcript contents",
            "Gate D bundle: passed",
            "Product judgment: passed",
            "Private content displayed: yes",
            "Live delivery performed: yes",
            "Product Promise Alpha passed",
        ),
        (
            "Traceback C:\\Users\\student\\.env token",
            "https://meet.example.edu/class-room?token=private",
            "cookie-value",
            "auth-state",
            "browser profile",
            "Good morning, everyone. I am going to take attendance",
            r"C:\private\lecture.wav",
            r"C:\private\lecture.mp4",
            "raw command output included: yes",
            "product_judgment_evidence_status: satisfactory",
            "product judgment evidence satisfied",
        ),
        (),
    ],
)
def test_static_demo_product_loop_summary_fails_closed_for_unsafe_values(
    monkeypatch,
    unsafe_product_loop_lines: tuple[str, ...],
) -> None:
    demo = _demo_module()

    def fake_product_loop_lines() -> tuple[str, ...]:
        return unsafe_product_loop_lines

    monkeypatch.setattr(
        demo,
        "_build_static_demo_product_loop_summary_lines",
        fake_product_loop_lines,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    product_loop_section = _section_text(html, "Local alpha product loop summary")
    product_loop_visible = _visible_text(product_loop_section)
    for expected in STATIC_DEMO_PRODUCT_LOOP_SUMMARY_LINES:
        assert expected in product_loop_visible
    assert "Metadata unavailable." not in product_loop_section
    assert "Live delivery perform&#101;d: no" in product_loop_section
    lowered = product_loop_section.casefold()
    for forbidden in (
        "<script",
        "<a ",
        "<button",
        "<form",
        "<input",
        "href=",
        "src=",
        "action=",
        "method=",
        "c:\\",
        "https:",
        "meet.example",
        ".env",
        "cookie",
        "token",
        "auth",
        "profile",
        "good morning",
        "traceback",
        ".wav",
        ".mp4",
        "raw command output included: yes",
        "product loop: real meeting to reviewer",
        "fixture input: private transcript",
        "session status: failed",
        "detected events: 0",
        "alert preview: sent",
        "archive/reviewer: transcript contents",
        "gate d bundle: passed",
        "product judgment: passed",
        "private content displayed: yes",
        "live delivery performed: yes",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered
    assert re.search(r"[a-z]:\\", product_loop_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(product_loop_section)


def test_static_demo_product_loop_summary_fails_closed_for_helper_exception(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_product_loop_lines() -> tuple[str, ...]:
        raise RuntimeError("Traceback C:\\Users\\student\\.env token")

    monkeypatch.setattr(
        demo,
        "_build_static_demo_product_loop_summary_lines",
        fake_product_loop_lines,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    product_loop_section = _section_text(html, "Local alpha product loop summary")
    product_loop_visible = _visible_text(product_loop_section)
    for expected in STATIC_DEMO_PRODUCT_LOOP_SUMMARY_LINES:
        assert expected in product_loop_visible
    assert "Traceback" not in product_loop_section
    assert ".env" not in product_loop_section
    assert "token" not in product_loop_section.casefold()


def test_static_demo_product_loop_summary_helper_preserves_static_scope() -> None:
    demo = _demo_module()
    source = (
        inspect.getsource(demo._safe_static_demo_product_loop_summary_lines)
        + inspect.getsource(demo._build_static_demo_product_loop_summary_lines)
    ).casefold()

    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "onclick",
        "onchange",
        "onsubmit",
        "formaction",
        "ui.run",
        "webbrowser",
        "startfile",
        "subprocess.run",
        "run_local_alpha_dashboard_demo",
        "dispatch_alert",
        "telegram",
        "desktop_notifier",
        "scheduler",
        "gate d bundle: passed",
        "product judgment: passed",
        "private content displayed: yes",
        "live delivery performed: yes",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
    ):
        assert forbidden not in source


@pytest.mark.parametrize(
    "unsafe_review_snapshot_lines",
    [
        (
            "Review scope: real online monitoring",
            "Input mode: private transcript",
            "Session status: hidden",
            "Detected event summary: missing",
            "Alert confirmation: optional",
            "Archive/reviewer summary: transcript contents",
            "Live services: used",
            "Private content: displayed",
            "Gate D: passed",
            "Product judgment: passed",
            "Product Promise Alpha passed",
        ),
        (
            "Traceback C:\\Users\\student\\.env token",
            "https://meet.example.edu/class-room?token=private",
            "cookie-value",
            "auth-state",
            "browser profile",
            "Good morning, everyone. I am going to take attendance",
            r"C:\private\lecture.wav",
            r"C:\private\lecture.mp4",
            "raw command output included: yes",
            "product_judgment_evidence_status: satisfactory",
            "product judgment evidence satisfied",
        ),
        (),
    ],
)
def test_static_demo_review_snapshot_fails_closed_for_unsafe_values(
    monkeypatch,
    unsafe_review_snapshot_lines: tuple[str, ...],
) -> None:
    demo = _demo_module()

    def fake_review_snapshot_lines() -> tuple[str, ...]:
        return unsafe_review_snapshot_lines

    monkeypatch.setattr(
        demo,
        "_build_static_demo_review_snapshot_lines",
        fake_review_snapshot_lines,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    review_snapshot_section = _section_text(html, "Local alpha demo review snapshot")
    review_snapshot_visible = _visible_text(review_snapshot_section)
    for expected in STATIC_DEMO_REVIEW_SNAPSHOT_LINES:
        assert expected in review_snapshot_visible
    assert "Metadata unavailable." not in review_snapshot_section
    lowered = review_snapshot_section.casefold()
    for forbidden in (
        "<script",
        "<a ",
        "<button",
        "<form",
        "<input",
        "href=",
        "src=",
        "action=",
        "method=",
        "c:\\",
        "https:",
        "meet.example",
        ".env",
        "cookie",
        "token",
        "auth",
        "profile",
        "good morning",
        "traceback",
        ".wav",
        ".mp4",
        "raw command output included: yes",
        "review scope: real online monitoring",
        "input mode: private transcript",
        "session status: hidden",
        "detected event summary: missing",
        "alert confirmation: optional",
        "archive/reviewer summary: transcript contents",
        "live services: used",
        "private content: displayed",
        "gate d: passed",
        "product judgment: passed",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered
    assert re.search(r"[a-z]:\\", review_snapshot_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(review_snapshot_section)


def test_static_demo_review_snapshot_fails_closed_for_helper_exception(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_review_snapshot_lines() -> tuple[str, ...]:
        raise RuntimeError("Traceback C:\\Users\\student\\.env token")

    monkeypatch.setattr(
        demo,
        "_build_static_demo_review_snapshot_lines",
        fake_review_snapshot_lines,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    review_snapshot_section = _section_text(html, "Local alpha demo review snapshot")
    review_snapshot_visible = _visible_text(review_snapshot_section)
    for expected in STATIC_DEMO_REVIEW_SNAPSHOT_LINES:
        assert expected in review_snapshot_visible
    assert "Traceback" not in review_snapshot_section
    assert ".env" not in review_snapshot_section
    assert "token" not in review_snapshot_section.casefold()


def test_static_demo_review_snapshot_helper_preserves_static_scope() -> None:
    demo = _demo_module()
    source = (
        inspect.getsource(demo._safe_static_demo_review_snapshot_lines)
        + inspect.getsource(demo._build_static_demo_review_snapshot_lines)
    ).casefold()

    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "onclick",
        "onchange",
        "onsubmit",
        "formaction",
        "ui.run",
        "webbrowser",
        "startfile",
        "subprocess.run",
        "run_local_alpha_dashboard_demo",
        "dispatch_alert",
        "telegram",
        "desktop_notifier",
        "scheduler",
        "review scope: real online monitoring",
        "input mode: private transcript",
        "alert confirmation: optional",
        "archive/reviewer summary: transcript contents",
        "live services: used",
        "private content: displayed",
        "gate d: passed",
        "product judgment: passed",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
    ):
        assert forbidden not in source


def test_static_demo_human_decision_boundary_section_is_fixed_and_safe() -> None:
    demo = _demo_module()

    html = demo.build_local_alpha_dashboard_static_demo_html()

    decision_section = _section_text(html, "Human decision boundary")
    decision_visible = _visible_text(decision_section)
    for expected in STATIC_DEMO_HUMAN_DECISION_BOUNDARY_LINES:
        assert expected in decision_visible
    assert "Metadata unavailable." not in decision_section
    lowered = decision_section.casefold()
    for forbidden in (
        "<script",
        "<a ",
        "<button",
        "<form",
        "<input",
        "href=",
        "src=",
        "action=",
        "method=",
        "c:\\",
        "https:",
        "meet.example",
        ".env",
        "cookie",
        "token",
        "auth",
        "profile",
        "good morning",
        "traceback",
        ".wav",
        ".mp4",
        "raw command output included: yes",
        "current product judgment: passed",
        "human decision required: no",
        "demo evidence scope: real online monitoring",
        "ai can complete product judgment: yes",
        "ai can record product judgment: yes",
        "gate d blocker: none",
        "gate d: passed",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered
    assert re.search(r"[a-z]:\\", decision_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(decision_section)


def test_static_demo_human_decision_boundary_fails_closed_for_helper_exception(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_decision_boundary_lines() -> tuple[str, ...]:
        raise RuntimeError("Traceback C:\\Users\\student\\.env token")

    monkeypatch.setattr(
        demo,
        "_build_static_demo_human_decision_boundary_lines",
        fake_decision_boundary_lines,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    decision_section = _section_text(html, "Human decision boundary")
    decision_visible = _visible_text(decision_section)
    for expected in STATIC_DEMO_HUMAN_DECISION_BOUNDARY_LINES:
        assert expected in decision_visible
    assert "Traceback" not in decision_section
    assert ".env" not in decision_section
    assert "token" not in decision_section.casefold()


def test_static_demo_human_decision_boundary_helper_preserves_static_scope() -> None:
    demo = _demo_module()
    source = (
        inspect.getsource(demo._safe_static_demo_human_decision_boundary_lines)
        + inspect.getsource(demo._build_static_demo_human_decision_boundary_lines)
    ).casefold()

    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "onclick",
        "onchange",
        "onsubmit",
        "formaction",
        "ui.run",
        "webbrowser",
        "startfile",
        "subprocess.run",
        "run_local_alpha_dashboard_demo",
        "dispatch_alert",
        "telegram",
        "desktop_notifier",
        "scheduler",
        "current product judgment: passed",
        "human decision required: no",
        "demo evidence scope: real online monitoring",
        "ai can complete product judgment: yes",
        "ai can record product judgment: yes",
        "gate d blocker: none",
        "gate d: passed",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
    ):
        assert forbidden not in source


def test_static_demo_product_review_cue_section_is_fixed_and_safe() -> None:
    demo = _demo_module()

    html = demo.build_local_alpha_dashboard_static_demo_html()

    cue_section = _section_text(html, "Product review cue")
    cue_visible = _visible_text(cue_section)
    for expected in STATIC_DEMO_PRODUCT_REVIEW_CUE_LINES:
        assert expected in cue_visible
    assert "Metadata unavailable." not in cue_section
    lowered = cue_section.casefold()
    for forbidden in (
        "<script",
        "<a ",
        "<button",
        "<form",
        "<input",
        "href=",
        "src=",
        "action=",
        "method=",
        "c:\\",
        "https:",
        "meet.example",
        ".env",
        "cookie",
        "token",
        "auth",
        "profile",
        "good morning",
        "traceback",
        ".wav",
        ".mp4",
        "raw command output included: yes",
        "review target: real online monitoring",
        "what to judge: private meeting behavior",
        "evidence basis: private transcript",
        "ai action: record judgment",
        "product judgment recorded: yes",
        "gate d blocker: none",
        "gate d: passed",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
        "product judgment evidence satisfied",
    ):
        assert forbidden not in lowered
    assert re.search(r"[a-z]:\\", cue_section, flags=re.IGNORECASE) is None
    _assert_no_event_handler_attributes(cue_section)


def test_static_demo_product_review_cue_fails_closed_for_helper_exception(
    monkeypatch,
) -> None:
    demo = _demo_module()

    def fake_product_review_cue_lines() -> tuple[str, ...]:
        raise RuntimeError("Traceback C:\\Users\\student\\.env token")

    monkeypatch.setattr(
        demo,
        "_build_static_demo_product_review_cue_lines",
        fake_product_review_cue_lines,
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    cue_section = _section_text(html, "Product review cue")
    cue_visible = _visible_text(cue_section)
    for expected in STATIC_DEMO_PRODUCT_REVIEW_CUE_LINES:
        assert expected in cue_visible
    assert "Traceback" not in cue_section
    assert ".env" not in cue_section
    assert "token" not in cue_section.casefold()


def test_static_demo_product_review_cue_helper_preserves_static_scope() -> None:
    demo = _demo_module()
    source = (
        inspect.getsource(demo._safe_static_demo_product_review_cue_lines)
        + inspect.getsource(demo._build_static_demo_product_review_cue_lines)
    ).casefold()

    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "onclick",
        "onchange",
        "onsubmit",
        "formaction",
        "ui.run",
        "webbrowser",
        "startfile",
        "subprocess.run",
        "run_local_alpha_dashboard_demo",
        "dispatch_alert",
        "telegram",
        "desktop_notifier",
        "scheduler",
        "review target: real online monitoring",
        "what to judge: private meeting behavior",
        "evidence basis: private transcript",
        "ai action: record judgment",
        "product judgment recorded: yes",
        "gate d blocker: none",
        "gate d: passed",
        "product promise alpha passed",
        "product_judgment_evidence_status: satisfactory",
    ):
        assert forbidden not in source


def test_static_demo_summary_status_strip_helper_preserves_static_scope() -> None:
    demo = _demo_module()
    source = (
        inspect.getsource(demo._safe_static_demo_summary_status_strip_lines)
        + inspect.getsource(demo._build_static_demo_summary_status_strip_lines)
        + inspect.getsource(demo._render_static_demo_summary_status_strip)
    ).casefold()

    for forbidden in (
        "<form",
        "<input",
        "<textarea",
        "<select",
        "<a ",
        "<button",
        "href=",
        "src=",
        "onclick",
        "onchange",
        "onsubmit",
        "formaction",
        "ui.run",
        "webbrowser",
        "startfile",
        "subprocess.run",
        "run_local_alpha_dashboard_demo",
        "dispatch_alert",
        "telegram",
        "desktop_notifier",
        "scheduler",
        "delete",
    ):
        assert forbidden not in source


def test_build_static_demo_html_escapes_summary_text(monkeypatch) -> None:
    demo = _demo_module()

    def fake_summary() -> str:
        return (
            "AsyncScholar local alpha inspection\n"
            "Server started: no\n"
            "Browser opened: no\n"
            "<script>alert('unsafe')</script>\n"
        )

    monkeypatch.setattr(
        demo, "build_local_alpha_dashboard_inspection_summary", fake_summary
    )

    html = demo.build_local_alpha_dashboard_static_demo_html()

    assert "<script>" not in html
    assert "&lt;script&gt;alert(&#x27;unsafe&#x27;)&lt;/script&gt;" in html


def test_dry_run_payload_is_safe_and_loopback_only() -> None:
    demo = _demo_module()

    payload = demo.build_local_alpha_dashboard_demo_dry_run(
        host="127.0.0.1",
        port=8086,
    )

    assert tuple(payload) == demo.LOCAL_ALPHA_DASHBOARD_DEMO_DRY_RUN_KEYS
    assert payload["demo_kind"] == "local_alpha_dashboard_demo"
    assert payload["url"] == "http://127.0.0.1:8086"
    assert payload["host"] == "127.0.0.1"
    assert payload["port"] == 8086
    assert payload["dry_run"] is True
    assert payload["server_started"] is False
    assert payload["browser_opened"] is False
    assert payload["gate_d_status"] == "narrow_local_pass_recorded"
    assert payload["product_judgment_evidence_status"] == "human_recorded_narrow_pass"
    assert payload["manual_product_judgment_required"] is False
    assert payload["product_promise_alpha_pass_claimed"] is False
    assert payload["metadata_only_demo_sources"] is True
    assert payload["private_data_read"] is False
    assert payload["audio_capture_performed"] is False
    assert payload["browser_automation_performed"] is False
    assert payload["live_delivery_performed"] is False
    assert payload["scheduler_loop_performed"] is False
    assert payload["deletion_or_export_performed"] is False
    assert payload["real_online_monitoring_performed"] is False
    assert payload["autonomous_participation_performed"] is False
    assert payload["academic_answer_behavior_performed"] is False
    assert payload["safety_summary"] == demo.LOCAL_ALPHA_DASHBOARD_DEMO_SAFETY_SUMMARY

    serialized = json.dumps(payload, sort_keys=True)
    for private_value in PRIVATE_VALUES:
        assert private_value not in serialized


@pytest.mark.parametrize(
    "host",
    [
        "0.0.0.0",
        "192.168.1.22",
        "example.com",
        r"C:\Users\student\token-secret-auth-profile",
        "",
    ],
)
def test_dry_run_rejects_non_loopback_hosts_without_echo(host: str) -> None:
    demo = _demo_module()

    with pytest.raises(
        ValueError, match="local alpha dashboard demo could not be built"
    ):
        demo.build_local_alpha_dashboard_demo_dry_run(host=host, port=8086)


@pytest.mark.parametrize("port", [0, -1, 65536, "8086", True])
def test_dry_run_rejects_invalid_ports(port: object) -> None:
    demo = _demo_module()

    with pytest.raises(
        ValueError, match="local alpha dashboard demo could not be built"
    ):
        demo.build_local_alpha_dashboard_demo_dry_run(host="127.0.0.1", port=port)


def _demo_module():
    return importlib.import_module("async_scholar.ui.local_alpha_dashboard_demo")


def _section_text(html: str, heading: str) -> str:
    start = html.index(f"<h2>{heading}</h2>")
    end = html.index("</section>", start)
    return html[start:end]


def _visible_text(html: str) -> str:
    return unescape(re.sub(r"<[^>]+>", "", html))


def _summary_status_strip_html(html: str) -> str:
    start = html.index('class="summary-status-strip"')
    start = html.rfind("<div", 0, start)
    end = html.index("</div>", start)
    return html[start:end]


def _summary_status_strip_text(html: str) -> str:
    return _visible_text(_summary_status_strip_html(html))


def _assert_no_event_handler_attributes(html: str) -> None:
    assert re.search(r"\son[a-z]+\s*=", html, flags=re.IGNORECASE) is None
