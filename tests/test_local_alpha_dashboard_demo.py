from __future__ import annotations

import importlib
import inspect
import json
import re
import subprocess
import sys
import textwrap

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
    "product_judgment_evidence remains blocking",
    "Product Promise Alpha not passed",
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
    assert first.gate_d["product_judgment_evidence_status"] == "blocking"
    assert first.gate_d["blocking_evidence"] == ["product_judgment_evidence"]
    assert first.gate_d["satisfactory_evidence_count"] == 9
    assert first.gate_d["missing_evidence_count"] == 0
    assert first.gate_d["ready_for_gate_review"] is False
    assert first.gate_d["manual_product_judgment_required"] is True
    assert first.gate_d["manual_product_judgment_recorded"] is False
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
    assert "Gate D not passed" in first
    assert "Blocked on product_judgment_evidence" in first
    assert "Human product judgment: deferred" in first
    assert "Satisfactory evidence: 9" in first
    assert "Missing evidence: 0" in first
    assert "Blocking evidence: product_judgment_evidence" in first
    assert "Manual judgment required: yes" in first
    assert "Manual judgment recorded: no" in first
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
    assert "Gate D passed" not in first
    assert "Product Promise Alpha passed" not in first
    serialized = json.dumps({"summary": first})
    for private_value in PRIVATE_VALUES:
        assert private_value not in serialized


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
    assert "Gate D: blocked" in first
    assert "Product judgment: deferred" in first
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
    assert "Gate D not passed" in first
    assert "Blocked on product_judgment_evidence" in first
    assert "Human product judgment: deferred" in first
    assert "Satisfactory evidence: 9" in first
    assert "Missing evidence: 0" in first
    assert "Manual judgment required: yes" in first
    assert "Manual judgment recorded: no" in first
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
    assert "Gate D blocker visible: product_judgment_evidence" in first
    assert "Human product judgment required: yes" in first
    assert "Action execution allowed: no" in first
    assert "Human judgment next step" in first
    assert "Manual inspection required: yes" in first
    assert "Product judgment recorded: no" in first
    assert "AI can complete product judgment: no" in first
    assert "AI can record product judgment: no" in first
    assert "product_judgment_evidence remains blocking" in first
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

    assert html.count("<section") == 19
    strip_text = _summary_status_strip_text(html)
    assert "Gate D: blocked" in strip_text
    assert "Product judgment: deferred" in strip_text
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
        "cookie",
        "token",
        "auth",
        "profile",
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

    gate_section = _section_text(html, "Gate D safety")
    assert "Gate D not passed" in gate_section
    assert "Blocked on product_judgment_evidence" in gate_section
    assert "Human product judgment: deferred" in gate_section
    assert "Manual judgment required: yes" in gate_section
    assert "Manual judgment recorded: no" in gate_section

    digest_section = _section_text(html, "Evidence digest")
    assert "Handoff status: Ready for manual review" in digest_section
    assert "Local bundle status: Blocked" in digest_section
    assert "Satisfactory evidence: 9" in digest_section
    assert "Missing evidence: 0" in digest_section
    assert "Blocking evidence: product_judgment_evidence" in digest_section
    assert "Manual product judgment required: yes" in digest_section
    assert "Manual product judgment recorded: no" in digest_section
    assert "AI can complete product judgment: no" in digest_section

    manual_review_section = _section_text(html, "Manual review status")
    manual_review_visible = _visible_text(manual_review_section)
    assert "Metadata unavailable." not in manual_review_section
    for expected in (
        "Review packet: local metadata only",
        "Human product judgment: required",
        "Final product judgment recorded: no",
        "AI can complete product judgment: no",
        "Gate D blocker: product_judgment_evidence",
        "Private data needed for review: no",
        "Live services needed for review: no",
        "Action execution allowed: no",
        "Product Promise Alpha not passed",
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
        "Gate D blocker visible: product_judgment_evidence",
        "Human product judgment required: yes",
        "Action execution allowed: no",
        "Product Promise Alpha not passed",
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
        "Manual inspection required: yes",
        "Product judgment recorded: no",
        "AI can complete product judgment: no",
        "AI can record product judgment: no",
        "product_judgment_evidence remains blocking",
        "Action execution allowed: no",
        "Product Promise Alpha not passed",
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
        "Product Promise Alpha not passed",
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
    assert "Gate D not passed" in launch_visible
    assert "Product Promise Alpha not passed" in launch_visible
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
        "Gate D evidence bundle: blocked",
        "Blocking evidence: product_judgment_evidence",
        "Manual product judgment required: yes",
        "Product Promise Alpha not passed",
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
        "product_judgment_evidence remains blocking",
        "Product Promise Alpha not passed",
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
        "<h2>Demo timeline</h2>"
    )

    timeline_section = _section_text(html, "Demo timeline")
    assert "Fixture source prepared" in timeline_section
    assert "Session completed" in timeline_section
    assert "Event detected" in timeline_section
    assert "Alert awaiting confirmation" in timeline_section
    assert "Archive/reviewer metadata ready" in timeline_section
    assert "Gate D blocked" in timeline_section

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
    assert "Gate D not passed" in action_visible
    assert "Product Promise Alpha not passed" in action_visible
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
        "Gate D not passed",
        "Product Promise Alpha not passed",
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
    assert "Local alpha demo only" in safety_section
    assert "no real meeting" in safety_section
    assert "private meeting data" in safety_section
    assert "audio capture" in safety_section
    assert "live delivery" in safety_section
    assert "participation" in safety_section
    assert "academic answers" in safety_section


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
        "Gate D blocked",
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
        "Gate D not passed",
        "Product Promise Alpha not passed",
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
    assert "Gate D not passed" in action_visible
    assert "Product Promise Alpha not passed" in action_visible
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
        "Gate D not passed",
        "Product Promise Alpha not passed",
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
    assert "Gate D not passed" in archive_review_visible
    assert "Product Promise Alpha not passed" in archive_review_visible
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
            "Gate D evidence bundle: blocked",
            "Blocking evidence: product_judgment_evidence",
            "Manual product judgment required: yes",
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
        "Gate D evidence bundle: blocked",
        "Blocking evidence: product_judgment_evidence",
        "Manual product judgment required: yes",
        "Product Promise Alpha not passed",
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
    assert "Gate D evidence bundle: blocked" in verification_visible
    assert "Blocking evidence: product_judgment_evidence" in verification_visible
    assert "Manual product judgment required: yes" in verification_visible
    assert "Product Promise Alpha not passed" in verification_visible
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
        "product_judgment_evidence remains blocking",
        "Product Promise Alpha not passed",
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
    assert "product_judgment_evidence remains blocking" in backend_evidence_visible
    assert "Product Promise Alpha not passed" in backend_evidence_visible
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
        "Product Promise Alpha not passed",
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
    assert "Product Promise Alpha not passed" in source_visible
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
        "Human product judgment: required",
        "Final product judgment recorded: no",
        "AI can complete product judgment: no",
        "Gate D blocker: product_judgment_evidence",
        "Private data needed for review: no",
        "Live services needed for review: no",
        "Action execution allowed: no",
        "Product Promise Alpha not passed",
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
    assert "Human product judgment: required" in manual_review_visible
    assert "Final product judgment recorded: no" in manual_review_visible
    assert "AI can complete product judgment: no" in manual_review_visible
    assert "Gate D blocker: product_judgment_evidence" in manual_review_visible
    assert "Private data needed for review: no" in manual_review_visible
    assert "Live services needed for review: no" in manual_review_visible
    assert "Action execution allowed: no" in manual_review_visible
    assert "Product Promise Alpha not passed" in manual_review_visible
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
        "Gate D blocker visible: product_judgment_evidence",
        "Human product judgment required: yes",
        "Action execution allowed: no",
        "Product Promise Alpha not passed",
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
    assert "Gate D blocker visible: product_judgment_evidence" in checklist_visible
    assert "Human product judgment required: yes" in checklist_visible
    assert "Action execution allowed: no" in checklist_visible
    assert "Product Promise Alpha not passed" in checklist_visible
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
        ("Manual inspection required: yes",),
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
        "Manual inspection required: yes",
        "Product judgment recorded: no",
        "AI can complete product judgment: no",
        "AI can record product judgment: no",
        "product_judgment_evidence remains blocking",
        "Action execution allowed: no",
        "Product Promise Alpha not passed",
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
    assert "Manual inspection required: yes" in next_step_visible
    assert "Product judgment recorded: no" in next_step_visible
    assert "AI can complete product judgment: no" in next_step_visible
    assert "AI can record product judgment: no" in next_step_visible
    assert "product_judgment_evidence remains blocking" in next_step_visible
    assert "Action execution allowed: no" in next_step_visible
    assert "Product Promise Alpha not passed" in next_step_visible
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
        "Gate D not passed",
        "Product Promise Alpha not passed",
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
    assert "Gate D not passed" in launch_visible
    assert "Product Promise Alpha not passed" in launch_visible
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
            "Gate D: blocked",
            "Product Promise Alpha: passed",
            "product_judgment_evidence_status: satisfactory",
            "https://meet.example.edu/class-room?token=private",
            "D:\\private\\lecture.wav",
            "transcript text: Good morning, everyone",
        ),
        (
            "Gate D: blocked",
            "file:///tmp/async-scholar-local-alpha-dashboard.html",
            "\\\\server\\share\\cookie-profile.json",
            "C:/Users/student/private/events.jsonl",
            "generated-media: lecture.mp4 clip.png",
            "product judgment evidence satisfied",
        ),
        ("Gate D: blocked",),
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
        "Gate D: blocked",
        "Product judgment: deferred",
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
    assert "Gate D: blocked" in strip_text
    assert "Product judgment: deferred" in strip_text
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
    assert "Handoff status: Ready for manual review" in digest_section
    assert "Local bundle status: Blocked" in digest_section
    assert "Satisfactory evidence: 0" in digest_section
    assert "Missing evidence: 0" in digest_section
    assert "Blocking evidence: product_judgment_evidence" in digest_section
    assert "Manual product judgment required: yes" in digest_section
    assert "Manual product judgment recorded: no" in digest_section
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
        "cookie",
        "token",
        "auth",
        "profile",
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
    assert payload["gate_d_status"] == "not_passed"
    assert payload["product_judgment_evidence_status"] == "blocking"
    assert payload["manual_product_judgment_required"] is True
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
    return re.sub(r"<[^>]+>", "", html)


def _summary_status_strip_html(html: str) -> str:
    start = html.index('class="summary-status-strip"')
    start = html.rfind("<div", 0, start)
    end = html.index("</div>", start)
    return html[start:end]


def _summary_status_strip_text(html: str) -> str:
    return _visible_text(_summary_status_strip_html(html))


def _assert_no_event_handler_attributes(html: str) -> None:
    assert re.search(r"\son[a-z]+\s*=", html, flags=re.IGNORECASE) is None
