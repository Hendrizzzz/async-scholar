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
    assert "Server started: no" in first
    assert "Browser opened: no" in first
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

    assert html.count("<section") == 10
    expected_headings = (
        "Gate D safety",
        "Evidence digest",
        "Session status",
        "Demo timeline",
        "Detected events",
        "Alert preview",
        "Confirmation queue",
        "Action controls",
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

    session_section = _section_text(html, "Session status")
    assert "Server started: no" in session_section
    assert "Browser opened: no" in session_section
    assert "Run status: Completed" in session_section
    assert "Source kind: Fixture demo" in session_section
    assert "Segments: 5" in session_section
    assert "Events: 2" in session_section

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


def _assert_no_event_handler_attributes(html: str) -> None:
    assert re.search(r"\son[a-z]+\s*=", html, flags=re.IGNORECASE) is None
