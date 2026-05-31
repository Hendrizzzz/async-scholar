from __future__ import annotations

import importlib
import inspect
import json
import subprocess
import sys
import textwrap

FORBIDDEN_IMPORT_PREFIXES = (
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
FORBIDDEN_SOURCE_REFERENCES = (
    "async_scholar.demo",
    "async_scholar.scheduler",
    "async_scholar.browser",
    "run_fixture_demo",
    "transcript_stream",
    "alert_dispatch",
    "desktop_notifier",
    "telegram_notifier",
    "fastapi",
    "uvicorn",
)
PRIVATE_RENDER_VALUES = (
    "Good morning, everyone. I am going to take attendance",
    "event-123",
    "segment-123",
    "alert-123",
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


def test_local_alpha_dashboard_module_import_is_safe() -> None:
    code = textwrap.dedent(
        """
        import importlib
        import json
        import sys

        before = set(sys.modules)
        importlib.import_module("async_scholar.ui.local_alpha_dashboard")
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

    module = importlib.import_module("async_scholar.ui.local_alpha_dashboard")
    source = inspect.getsource(module).casefold()
    for reference in FORBIDDEN_SOURCE_REFERENCES:
        assert reference not in source


def test_ui_package_lazy_export_for_local_alpha_dashboard_is_safe() -> None:
    code = textwrap.dedent(
        """
        import importlib
        import json
        import sys

        package = importlib.import_module("async_scholar.ui")
        assert "render_local_alpha_dashboard" in package.__all__
        before = set(sys.modules)
        render = package.render_local_alpha_dashboard
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
        print(json.dumps({"callable": callable(render), "forbidden": forbidden}))
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
    assert json.loads(completed.stdout) == {"callable": True, "forbidden": []}


def test_dashboard_renders_safe_human_facing_sections() -> None:
    dashboard = _dashboard_module()
    ui = FakeUI()
    sources = dashboard.LocalAlphaDashboardSources(
        session_status=StaticStatusSource(
            [
                {
                    "run_status": "completed",
                    "source_kind": "fixture_demo",
                    "segment_count": 5,
                    "event_count": 2,
                    "artifact_paths": PRIVATE_RENDER_VALUES[3],
                    "transcript_text": PRIVATE_RENDER_VALUES[0],
                    "cookie": PRIVATE_RENDER_VALUES[8],
                }
            ]
        ),
        events=StaticEventSource(
            [
                [
                    {
                        "event_type": "attendance_prompt",
                        "detected_at": 12,
                        "confidence": 0.88,
                        "message": PRIVATE_RENDER_VALUES[0],
                        "event_id": PRIVATE_RENDER_VALUES[1],
                        "source_segment_id": PRIVATE_RENDER_VALUES[2],
                    }
                ]
            ]
        ),
        alerts=StaticAlertSource(
            [
                [
                    {
                        "severity": "urgent",
                        "status": "delivered",
                        "confirmation_required": False,
                        "message": PRIVATE_RENDER_VALUES[0],
                        "alert_id": PRIVATE_RENDER_VALUES[3],
                        "provider_result": "live delivery happened",
                    }
                ]
            ]
        ),
        archive=StaticArchiveSource(
            [
                [
                    {
                        "title": PRIVATE_RENDER_VALUES[1],
                        "reviewer_excerpt": PRIVATE_RENDER_VALUES[0],
                        "reviewer_status": "available",
                        "event_count": 2,
                        "alert_count": 1,
                        "updated_time_label": "Updated May 30, 2026",
                        "events_path": PRIVATE_RENDER_VALUES[3],
                        "audio_file": PRIVATE_RENDER_VALUES[4],
                        "reviewer_path": r"C:\private\reviewer.md",
                    }
                ]
            ]
        ),
        gate_d={
            "status": "passed",
            "product_judgment_evidence": "approved",
            "product_judgment_evidence_status": "blocking",
            "blocking_evidence": [
                "product_judgment_evidence",
                r"C:\private\lecture.wav",
            ],
            "satisfactory_evidence_count": 9,
            "missing_evidence_count": 0,
            "ready_for_gate_review": True,
            "manual_product_judgment_required": False,
            "manual_product_judgment_recorded": True,
            "raw_note": "ready for release",
        },
    )

    view = dashboard.render_local_alpha_dashboard(sources, ui=ui)
    rendered = "\n".join(ui.texts)

    assert view.gate_d_status.status_label == "Gate D not passed"
    assert "AsyncScholar local alpha" in rendered
    assert "Gate D safety" in rendered
    assert "Gate D not passed" in rendered
    assert "Blocked on product_judgment_evidence" in rendered
    assert "Human product judgment: deferred" in rendered
    assert "Gate D: blocked" in rendered
    assert "Product judgment: deferred" in rendered
    assert "Evidence digest" in rendered
    assert "Local evidence bundle: metadata only" in rendered
    assert "Product judgment evidence: blocking" in rendered
    assert "Session: completed" in rendered
    assert "Detected events: 2" in rendered
    assert "Alert: pending confirmation" in rendered
    assert "Live delivery: no" in rendered
    assert "Satisfactory evidence: 9" in rendered
    assert "Missing evidence: 0" in rendered
    assert "Blocking evidence: product_judgment_evidence" in rendered
    assert "Ready for gate review: no" in rendered
    assert "Manual judgment required: yes" in rendered
    assert "Manual judgment recorded: no" in rendered
    assert "Manual review status" in rendered
    assert "Review packet: local metadata only" in rendered
    assert "Human product judgment: required" in rendered
    assert "Final product judgment recorded: no" in rendered
    assert "AI can complete product judgment: no" in rendered
    assert "Gate D blocker: product_judgment_evidence" in rendered
    assert "Private data needed for review: no" in rendered
    assert "Live services needed for review: no" in rendered
    assert "Action execution allowed: no" in rendered
    assert "Demo review checklist" in rendered
    assert "Session status visible: yes" in rendered
    assert "Detected event summary visible: yes" in rendered
    assert "Alert preview requires confirmation: yes" in rendered
    assert "Archive/reviewer metadata visible: yes" in rendered
    assert "Gate D blocker visible: product_judgment_evidence" in rendered
    assert "Human product judgment required: yes" in rendered
    assert "Session status" in rendered
    assert "Completed" in rendered
    assert "Fixture demo" in rendered
    assert "Demo source status" in rendered
    assert "Session source: injected fixture metadata" in rendered
    assert "Event source: injected fixture metadata" in rendered
    assert "Alert source: injected fixture metadata" in rendered
    assert "Archive source: injected fixture metadata" in rendered
    assert "Gate D source: injected local handoff metadata" in rendered
    assert "Transcript source: not displayed" in rendered
    assert "Recording source: not displayed" in rendered
    assert "Private source data read: no" in rendered
    assert "Source refresh required: no" in rendered
    assert "Local demo launch" in rendered
    assert "Demo mode: local fixture/static only" in rendered
    assert (
        "Launch command: python -m async_scholar "
        "local-alpha-dashboard-static-demo --output TEMP_HTML"
    ) in rendered
    assert (
        "Inspection command: python -m async_scholar local-alpha-dashboard-inspection"
    ) in rendered
    assert "Server started: no" in rendered
    assert "Browser opened: no" in rendered
    assert "Private data read: no" in rendered
    assert "Product Promise Alpha not passed" in rendered
    assert "Demo verification status" in rendered
    assert "Dashboard surface: local injected UI" in rendered
    assert "Source mode: injected fixture metadata" in rendered
    assert (
        "Static export command: python -m async_scholar "
        "local-alpha-dashboard-static-demo --output TEMP_HTML"
    ) in rendered
    assert "Gate D evidence bundle: blocked" in rendered
    assert "Attendance prompt - 12s - 88% confidence" in rendered
    assert "Urgent alert" in rendered
    assert "Status: Pending" in rendered
    assert "Confirmation required" in rendered
    assert "Confirmation queue" in rendered
    assert "User confirmation required" in rendered
    assert "Alert status: pending" in rendered
    assert "Participation action sent: no" in rendered
    assert "Autonomous participation: no" in rendered
    assert "Academic answer behavior: no" in rendered
    assert "Review alert confirmation" in rendered
    assert "Send participation action" in rendered
    assert "Open archive reviewer" in rendered
    assert "Record product judgment" in rendered
    assert "Alert delivery live: no" in rendered
    assert "Archive review status" in rendered
    assert "Archive artifacts: metadata only" in rendered
    assert "Reviewer summary: metadata only" in rendered
    assert "Detected events archived: 2" in rendered
    assert "Alert previews archived: pending confirmation" in rendered
    assert "Transcript text displayed: no" in rendered
    assert "Recording displayed: no" in rendered
    assert "Private paths displayed: no" in rendered
    assert "Delete/export execution: no" in rendered
    assert "Review confirmation before acting." in rendered
    assert "Local archive summary" in rendered
    assert "Reviewer available" in rendered
    assert "Reviewer artifact metadata only." in rendered
    assert "Product Promise Alpha passed" not in rendered
    assert "ready for release" not in rendered
    assert "Status: Delivered" not in rendered
    assert "live delivery happened" not in rendered

    summary = _find_element_by_class(
        ui,
        "async-scholar-local-alpha-dashboard__summary",
    )
    assert summary is not None
    assert [child.text for child in summary.children] == [
        "Gate D: blocked",
        "Product judgment: deferred",
        "Session: completed",
        "Detected events: 2",
        "Alert: pending confirmation",
        "Live delivery: no",
    ]
    assert {child.kind for child in summary.children} == {"label"}
    assert ui.texts.index("Live delivery: no") < ui.texts.index("Gate D safety")
    assert ui.texts.index("Gate D safety") < ui.texts.index("Evidence digest")
    assert ui.texts.index("Evidence digest") < ui.texts.index("Session status")

    evidence_digest = _find_element_by_class(
        ui,
        "async-scholar-local-alpha-dashboard__evidence",
    )
    assert evidence_digest is not None
    assert [child.text for child in evidence_digest.children] == [
        "Evidence digest",
        "Local evidence bundle: metadata only",
        "Product judgment evidence: blocking",
        "Satisfactory evidence: 9",
        "Missing evidence: 0",
        "Blocking evidence: product_judgment_evidence",
        "Ready for gate review: no",
        "Manual judgment required: yes",
        "Manual judgment recorded: no",
        "Gate D not passed",
        "Product Promise Alpha not passed",
    ]
    assert {child.kind for child in evidence_digest.children} == {"label"}
    assert all(child.on_click is None for child in evidence_digest.children)

    manual_review = _find_element_by_class(
        ui,
        "async-scholar-local-alpha-dashboard__manual-review",
    )
    assert manual_review is not None
    assert [child.text for child in manual_review.children] == [
        "Manual review status",
        "Review packet: local metadata only",
        "Human product judgment: required",
        "Final product judgment recorded: no",
        "AI can complete product judgment: no",
        "Gate D blocker: product_judgment_evidence",
        "Private data needed for review: no",
        "Live services needed for review: no",
        "Action execution allowed: no",
        "Product Promise Alpha not passed",
    ]
    assert {child.kind for child in manual_review.children} == {"label"}
    assert all(child.on_click is None for child in manual_review.children)
    assert ui.texts.index("Evidence digest") < ui.texts.index("Manual review status")
    assert ui.texts.index("Manual review status") < ui.texts.index("Session status")

    review_checklist = _find_element_by_class(
        ui,
        "async-scholar-local-alpha-dashboard__review-checklist",
    )
    assert review_checklist is not None
    assert [child.text for child in review_checklist.children] == [
        "Demo review checklist",
        "Session status visible: yes",
        "Detected event summary visible: yes",
        "Alert preview requires confirmation: yes",
        "Archive/reviewer metadata visible: yes",
        "Gate D blocker visible: product_judgment_evidence",
        "Human product judgment required: yes",
        "Action execution allowed: no",
        "Product Promise Alpha not passed",
    ]
    assert {child.kind for child in review_checklist.children} == {"label"}
    assert all(child.on_click is None for child in review_checklist.children)
    assert ui.texts.index("Manual review status") < ui.texts.index(
        "Demo review checklist"
    )
    assert ui.texts.index("Demo review checklist") < ui.texts.index("Session status")

    source_status = _find_element_by_class(
        ui,
        "async-scholar-local-alpha-dashboard__source-status",
    )
    assert source_status is not None
    assert [child.text for child in source_status.children] == [
        "Demo source status",
        "Session source: injected fixture metadata",
        "Event source: injected fixture metadata",
        "Alert source: injected fixture metadata",
        "Archive source: injected fixture metadata",
        "Gate D source: injected local handoff metadata",
        "Transcript source: not displayed",
        "Recording source: not displayed",
        "Private source data read: no",
        "Source refresh required: no",
        "Product Promise Alpha not passed",
    ]
    assert {child.kind for child in source_status.children} == {"label"}
    assert all(child.on_click is None for child in source_status.children)
    assert ui.texts.index("Session status") < ui.texts.index("Demo source status")
    assert ui.texts.index("Demo source status") < ui.texts.index("Local demo launch")

    launch = _find_element_by_class(
        ui,
        "async-scholar-local-alpha-dashboard__launch",
    )
    assert launch is not None
    assert [child.text for child in launch.children] == [
        "Local demo launch",
        "Demo mode: local fixture/static only",
        "Launch command: python -m async_scholar "
        "local-alpha-dashboard-static-demo --output TEMP_HTML",
        "Inspection command: python -m async_scholar local-alpha-dashboard-inspection",
        "Server started: no",
        "Browser opened: no",
        "Live delivery: no",
        "Private data read: no",
        "Gate D not passed",
        "Product Promise Alpha not passed",
    ]
    assert {child.kind for child in launch.children} == {"label"}
    assert ui.texts.index("Events: 2") < ui.texts.index("Local demo launch")
    assert ui.texts.index("Local demo launch") < ui.texts.index(
        "Attendance prompt - 12s - 88% confidence"
    )

    verification = _find_element_by_class(
        ui,
        "async-scholar-local-alpha-dashboard__verification",
    )
    assert verification is not None
    assert [child.text for child in verification.children] == [
        "Demo verification status",
        "Dashboard surface: local injected UI",
        "Source mode: injected fixture metadata",
        "Server started: no",
        "Browser opened: no",
        "Inspection command: python -m async_scholar local-alpha-dashboard-inspection",
        "Static export command: python -m async_scholar "
        "local-alpha-dashboard-static-demo --output TEMP_HTML",
        "Gate D evidence bundle: blocked",
        "Blocking evidence: product_judgment_evidence",
        "Manual product judgment required: yes",
        "Product Promise Alpha not passed",
    ]
    assert {child.kind for child in verification.children} == {"label"}
    assert all(child.on_click is None for child in verification.children)
    assert ui.texts.index("Local demo launch") < ui.texts.index(
        "Demo verification status"
    )
    assert ui.texts.index("Demo verification status") < ui.texts.index(
        "Attendance prompt - 12s - 88% confidence"
    )

    confirmation_queue = _find_element_by_class(
        ui,
        "async-scholar-local-alpha-dashboard__confirmation",
    )
    assert confirmation_queue is not None
    assert [child.text for child in confirmation_queue.children] == [
        "Confirmation queue",
        "User confirmation required",
        "Alert status: pending",
        "Participation action sent: no",
        "Autonomous participation: no",
        "Live delivery: no",
        "Academic answer behavior: no",
    ]
    assert {child.kind for child in confirmation_queue.children} == {"label"}
    assert ui.texts.index("Review confirmation before acting.") < ui.texts.index(
        "Confirmation queue"
    )
    assert ui.texts.index("Confirmation queue") < ui.texts.index(
        "Local archive summary"
    )

    action_controls = _find_element_by_class(
        ui,
        "async-scholar-local-alpha-dashboard__actions",
    )
    assert action_controls is not None
    assert [child.text for child in action_controls.children] == [
        "Action controls",
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
    ]
    assert {child.kind for child in action_controls.children} == {"label"}
    assert all(child.on_click is None for child in action_controls.children)
    assert ui.texts.index("Confirmation queue") < ui.texts.index("Action controls")
    assert ui.texts.index("Action controls") < ui.texts.index("Archive review status")

    archive_review_status = _find_element_by_class(
        ui,
        "async-scholar-local-alpha-dashboard__archive-review-status",
    )
    assert archive_review_status is not None
    assert [child.text for child in archive_review_status.children] == [
        "Archive review status",
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
    ]
    assert {child.kind for child in archive_review_status.children} == {"label"}
    assert all(child.on_click is None for child in archive_review_status.children)
    assert ui.texts.index("Archive review status") < ui.texts.index(
        "Local archive summary"
    )

    for private_value in PRIVATE_RENDER_VALUES:
        assert private_value not in rendered


def test_dashboard_inspection_summary_is_metadata_only_and_no_server() -> None:
    dashboard = _dashboard_module()
    sources = dashboard.LocalAlphaDashboardSources(
        session_status=StaticStatusSource(
            [
                {
                    "run_status": "completed",
                    "source_kind": "fixture_demo",
                    "segment_count": 5,
                    "event_count": 2,
                    "transcript_text": PRIVATE_RENDER_VALUES[0],
                }
            ]
        ),
        events=StaticEventSource(
            [
                [
                    {
                        "event_type": "attendance_prompt",
                        "detected_at": 42,
                        "confidence": 0.94,
                        "message": PRIVATE_RENDER_VALUES[0],
                    },
                    {
                        "event_type": "important_event",
                        "detected_at": 185,
                        "confidence": 0.88,
                        "path": PRIVATE_RENDER_VALUES[4],
                    },
                ]
            ]
        ),
        alerts=StaticAlertSource(
            [
                [
                    {
                        "severity": "urgent",
                        "status": "delivered",
                        "confirmation_required": False,
                        "message": PRIVATE_RENDER_VALUES[0],
                    }
                ]
            ]
        ),
        archive=StaticArchiveSource(
            [
                [
                    {
                        "title": PRIVATE_RENDER_VALUES[5],
                        "reviewer_excerpt": PRIVATE_RENDER_VALUES[0],
                        "reviewer_status": "available",
                        "event_count": 2,
                        "alert_count": 1,
                        "events_path": PRIVATE_RENDER_VALUES[4],
                    }
                ]
            ]
        ),
        gate_d={
            "product_judgment_evidence_status": "blocking",
            "blocking_evidence": ["product_judgment_evidence"],
            "satisfactory_evidence_count": 9,
            "missing_evidence_count": 0,
            "ready_for_gate_review": True,
            "manual_product_judgment_required": False,
            "manual_product_judgment_recorded": True,
            "raw_note": "Product Promise Alpha passed",
        },
    )

    summary = dashboard.format_local_alpha_dashboard_inspection(sources)

    assert "AsyncScholar local alpha inspection" in summary
    assert "Server started: no" in summary
    assert "Browser opened: no" in summary
    assert "Gate D not passed" in summary
    assert "Blocked on product_judgment_evidence" in summary
    assert "Human product judgment: deferred" in summary
    assert "Satisfactory evidence: 9" in summary
    assert "Missing evidence: 0" in summary
    assert "Manual judgment required: yes" in summary
    assert "Manual judgment recorded: no" in summary
    assert "Session status" in summary
    assert "Run status: Completed" in summary
    assert "Source kind: Fixture demo" in summary
    assert "Segments: 5" in summary
    assert "Events: 2" in summary
    assert "Detected events" in summary
    assert "Attendance prompt - 42s - 94% confidence" in summary
    assert "Important event - 185s - 88% confidence" in summary
    assert "Alert preview" in summary
    assert "Urgent alert" in summary
    assert "Status: Pending" in summary
    assert "Confirmation required" in summary
    assert "Archive and reviewer" in summary
    assert "Local archive summary" in summary
    assert "Reviewer available" in summary
    assert "Reviewer artifact metadata only." in summary
    assert "Product Promise Alpha passed" not in summary
    assert "Status: Delivered" not in summary
    for private_value in PRIVATE_RENDER_VALUES:
        assert private_value not in summary


def test_archive_display_fields_are_reduced_to_metadata_only() -> None:
    dashboard = _dashboard_module()
    ui = FakeUI()

    dashboard.render_local_alpha_dashboard(
        dashboard.LocalAlphaDashboardSources(
            session_status=StaticStatusSource([{}]),
            events=StaticEventSource([[]]),
            alerts=StaticAlertSource([[]]),
            archive=StaticArchiveSource(
                [
                    [
                        {
                            "title": PRIVATE_RENDER_VALUES[4],
                            "reviewer_excerpt": PRIVATE_RENDER_VALUES[0],
                            "summary": "segment-123 transcript summary",
                            "excerpt": "token-value private excerpt",
                            "reviewer_status": "available",
                            "event_count": 2,
                            "alert_count": 1,
                        }
                    ]
                ]
            ),
            gate_d={},
        ),
        ui=ui,
    )

    rendered = "\n".join(ui.texts)

    assert "Local archive summary" in rendered
    assert "Reviewer available" in rendered
    assert "Events: 2" in rendered
    assert "Alerts: 1" in rendered
    assert "Reviewer artifact metadata only." in rendered
    for private_value in PRIVATE_RENDER_VALUES:
        assert private_value not in rendered
    assert "segment-123 transcript summary" not in rendered
    assert "token-value private excerpt" not in rendered


def test_dashboard_refresh_uses_only_injected_sources() -> None:
    dashboard = _dashboard_module()
    ui = FakeUI()
    session_source = StaticStatusSource(
        [
            {"run_status": "running", "source_kind": "fixture_demo"},
            {
                "run_status": "completed",
                "source_kind": "fixture_demo",
                "segment_count": 5,
                "event_count": 2,
            },
        ]
    )
    event_source = StaticEventSource(
        [
            [{"event_type": "attendance_prompt", "detected_at": 1, "confidence": 0.25}],
            [{"event_type": "quiz", "detected_at": 2, "confidence": 0.5}],
        ]
    )
    alert_source = StaticAlertSource(
        [
            [{"severity": "info", "status": "sent", "confirmation_required": False}],
            [
                {
                    "severity": "urgent",
                    "status": "delivered",
                    "confirmation_required": False,
                }
            ],
        ]
    )
    archive_source = StaticArchiveSource(
        [
            [{"title": "First review", "reviewer_status": "pending"}],
            [
                {
                    "title": "Second review",
                    "reviewer_status": "available",
                    "event_count": 4,
                }
            ],
        ]
    )

    dashboard.render_local_alpha_dashboard(
        dashboard.LocalAlphaDashboardSources(
            session_status=session_source,
            events=event_source,
            alerts=alert_source,
            archive=archive_source,
            gate_d={},
        ),
        ui=ui,
    )
    first_render = "\n".join(ui.texts)

    assert "Session: running" in first_render
    assert "Detected events: 0" in first_render
    assert "Running" in first_render
    assert "Attendance prompt - 1s - 25% confidence" in first_render
    assert "Local archive summary" in first_render
    assert "Reviewer pending" in first_render
    assert session_source.calls == 1
    assert event_source.calls == 1
    assert alert_source.calls == 1
    assert archive_source.calls == 1

    ui.click("Refresh dashboard")
    second_render = "\n".join(ui.texts)

    assert "Session: completed" in second_render
    assert "Detected events: 2" in second_render
    assert "Session: running" not in second_render
    assert second_render.count("Evidence digest") == 1
    assert second_render.count("Product judgment evidence: blocking") == 1
    assert second_render.count("Local evidence bundle: metadata only") == 1
    assert second_render.count("Manual review status") == 1
    assert second_render.count("Review packet: local metadata only") == 1
    assert second_render.count("Human product judgment: required") == 1
    assert second_render.count("Final product judgment recorded: no") == 1
    assert second_render.count("AI can complete product judgment: no") == 1
    assert second_render.count("Gate D blocker: product_judgment_evidence") == 1
    assert second_render.count("Private data needed for review: no") == 1
    assert second_render.count("Live services needed for review: no") == 1
    assert second_render.count("Action execution allowed: no") == 2
    review_checklist = _find_element_by_class(
        ui,
        "async-scholar-local-alpha-dashboard__review-checklist",
    )
    assert review_checklist is not None
    assert [child.text for child in review_checklist.children] == [
        "Demo review checklist",
        "Session status visible: yes",
        "Detected event summary visible: yes",
        "Alert preview requires confirmation: yes",
        "Archive/reviewer metadata visible: yes",
        "Gate D blocker visible: product_judgment_evidence",
        "Human product judgment required: yes",
        "Action execution allowed: no",
        "Product Promise Alpha not passed",
    ]
    assert {child.kind for child in review_checklist.children} == {"label"}
    assert all(child.on_click is None for child in review_checklist.children)
    assert second_render.count("Demo review checklist") == 1
    assert second_render.count("Session status visible: yes") == 1
    assert second_render.count("Detected event summary visible: yes") == 1
    assert second_render.count("Alert preview requires confirmation: yes") == 1
    assert second_render.count("Archive/reviewer metadata visible: yes") == 1
    assert second_render.count("Gate D blocker visible: product_judgment_evidence") == 1
    assert second_render.count("Human product judgment required: yes") == 1
    assert second_render.count("Local demo launch") == 1
    assert second_render.count("Launch command:") == 1
    assert second_render.count("Private data read: no") == 1
    assert second_render.count("Demo verification status") == 1
    assert second_render.count("Dashboard surface: local injected UI") == 1
    assert second_render.count("Source mode: injected fixture metadata") == 1
    assert second_render.count("Gate D evidence bundle: blocked") == 1
    assert second_render.count("Demo source status") == 1
    assert second_render.count("Session source: injected fixture metadata") == 1
    assert second_render.count("Event source: injected fixture metadata") == 1
    assert second_render.count("Alert source: injected fixture metadata") == 1
    assert second_render.count("Archive source: injected fixture metadata") == 1
    assert second_render.count("Gate D source: injected local handoff metadata") == 1
    assert second_render.count("Transcript source: not displayed") == 1
    assert second_render.count("Recording source: not displayed") == 1
    assert second_render.count("Private source data read: no") == 1
    assert second_render.count("Source refresh required: no") == 1
    assert second_render.count("Confirmation queue") == 1
    assert second_render.count("Alert status: pending") == 1
    assert second_render.count("Participation action sent: no") == 2
    assert second_render.count("Action controls") == 1
    assert second_render.count("Review alert confirmation") == 1
    assert second_render.count("Alert delivery live: no") == 1
    assert second_render.count("Archive review status") == 1
    assert second_render.count("Detected events archived: 2") == 1
    assert second_render.count("Delete/export execution: no") == 1
    assert "Completed" in second_render
    assert "Quiz - 2s - 50% confidence" in second_render
    assert "Severity: Urgent" in second_render
    assert "Status: Pending" in second_render
    assert "Reviewer available" in second_render
    assert "Reviewer pending" not in second_render
    assert session_source.calls == 2
    assert event_source.calls == 2
    assert alert_source.calls == 2
    assert archive_source.calls == 2


def test_gate_d_status_fails_closed_on_pass_like_source() -> None:
    dashboard = _dashboard_module()

    model = dashboard.normalize_gate_d_status(
        {
            "gate_d_status": "passed",
            "product_promise_alpha": "approved",
            "product_judgment_evidence": "satisfied",
            "product_judgment_evidence_status": "satisfied",
            "blocking_evidence": ["private-blocker", "product_judgment_evidence"],
            "satisfactory_evidence_count": 999999,
            "missing_evidence_count": -4,
            "ready_for_gate_review": True,
            "manual_product_judgment_required": False,
            "manual_product_judgment_recorded": True,
            "manual_judgment": "pass",
        }
    )

    rendered = dashboard.format_gate_d_status(model)
    assert model.status_label == "Gate D not passed"
    assert model.blocker_label == "Blocked on product_judgment_evidence"
    assert "Blocking evidence: product_judgment_evidence" in rendered
    assert "Ready for gate review: no" in rendered
    assert "Manual judgment required: yes" in rendered
    assert "Manual judgment recorded: no" in rendered
    assert "approved" not in rendered.casefold()
    assert "satisfied" not in rendered.casefold()
    assert "private-blocker" not in rendered
    assert "pass judgment recorded" not in rendered.casefold()


def test_gate_d_status_renders_allowlisted_metadata_only() -> None:
    dashboard = _dashboard_module()

    model = dashboard.normalize_gate_d_status(
        {
            "product_judgment_evidence_status": "blocking",
            "blocking_evidence": ["product_judgment_evidence"],
            "satisfactory_evidence_count": 9,
            "missing_evidence_count": 0,
            "ready_for_gate_review": False,
            "manual_product_judgment_required": True,
            "manual_product_judgment_recorded": False,
            "raw_note": PRIVATE_RENDER_VALUES[0],
            "private_url": "https://meet.example.edu/class-room?token=private",
            "traceback": PRIVATE_RENDER_VALUES[10],
        }
    )

    rendered = dashboard.format_gate_d_status(model)

    assert "Gate D not passed" in rendered
    assert "Blocked on product_judgment_evidence" in rendered
    assert "Human product judgment: deferred" in rendered
    assert "Satisfactory evidence: 9" in rendered
    assert "Missing evidence: 0" in rendered
    assert "Blocking evidence: product_judgment_evidence" in rendered
    assert "Ready for gate review: no" in rendered
    assert "Manual judgment required: yes" in rendered
    assert "Manual judgment recorded: no" in rendered
    assert "raw_note" not in rendered
    assert "meet.example" not in rendered
    for private_value in PRIVATE_RENDER_VALUES:
        assert private_value not in rendered


def test_gate_d_status_fails_closed_for_unavailable_or_hostile_source() -> None:
    dashboard = _dashboard_module()

    class RaisingGateDSource:
        def __call__(self) -> object:
            raise RuntimeError(r"Traceback C:\Users\student\.env token-value")

    hostile_sources = (
        RaisingGateDSource(),
        r"Traceback C:\Users\student\.env token-value",
        {
            "product_judgment_evidence_status": "blocking",
            "blocking_evidence": [
                "product_judgment_evidence",
                r"C:\private\lecture.wav",
                "token-value",
            ],
            "satisfactory_evidence_count": "not-a-count",
            "missing_evidence_count": "also-not-a-count",
            "ready_for_gate_review": True,
            "manual_product_judgment_required": False,
            "manual_product_judgment_recorded": True,
            "auth_profile": "browser profile",
            "raw_exception": "Traceback (most recent call last)",
        },
    )

    for source in hostile_sources:
        rendered = dashboard.format_gate_d_status(
            dashboard.normalize_gate_d_status(source)
        )
        assert "Gate D not passed" in rendered
        assert "Blocked on product_judgment_evidence" in rendered
        assert "Blocking evidence: product_judgment_evidence" in rendered
        assert "Ready for gate review: no" in rendered
        assert "Manual judgment required: yes" in rendered
        assert "Manual judgment recorded: no" in rendered
        assert "token-value" not in rendered
        assert "Traceback" not in rendered
        assert r"C:\private\lecture.wav" not in rendered
        assert "browser profile" not in rendered


def test_dashboard_summary_strip_fails_closed_for_hostile_sources() -> None:
    dashboard = _dashboard_module()
    ui = FakeUI()

    dashboard.render_local_alpha_dashboard(
        dashboard.LocalAlphaDashboardSources(
            session_status=StaticStatusSource(
                [
                    {
                        "run_status": r"C:\private\lecture.wav",
                        "source_kind": "fixture_demo",
                        "segment_count": "token-value",
                        "event_count": "999999999",
                        "transcript_text": PRIVATE_RENDER_VALUES[0],
                    }
                ]
            ),
            events=StaticEventSource([[]]),
            alerts=StaticAlertSource([[]]),
            archive=StaticArchiveSource([[]]),
            gate_d={
                "status": "passed",
                "product_judgment_evidence": "satisfied",
                "product_judgment_evidence_status": "satisfied",
                "raw_note": "Product Promise Alpha passed",
                "private_path": r"C:\private\lecture.wav",
                "auth_profile": "browser profile",
            },
        ),
        ui=ui,
    )

    summary = _find_element_by_class(
        ui,
        "async-scholar-local-alpha-dashboard__summary",
    )
    assert summary is not None
    assert [child.text for child in summary.children] == [
        "Gate D: blocked",
        "Product judgment: deferred",
        "Session: unknown",
        "Detected events: 9999",
        "Alert: pending confirmation",
        "Live delivery: no",
    ]

    evidence_digest = _find_element_by_class(
        ui,
        "async-scholar-local-alpha-dashboard__evidence",
    )
    assert evidence_digest is not None
    assert [child.text for child in evidence_digest.children] == [
        "Evidence digest",
        "Local evidence bundle: metadata only",
        "Product judgment evidence: blocking",
        "Satisfactory evidence: 0",
        "Missing evidence: 0",
        "Blocking evidence: product_judgment_evidence",
        "Ready for gate review: no",
        "Manual judgment required: yes",
        "Manual judgment recorded: no",
        "Gate D not passed",
        "Product Promise Alpha not passed",
    ]
    assert {child.kind for child in evidence_digest.children} == {"label"}
    assert all(child.on_click is None for child in evidence_digest.children)

    review_checklist = _find_element_by_class(
        ui,
        "async-scholar-local-alpha-dashboard__review-checklist",
    )
    assert review_checklist is not None
    assert [child.text for child in review_checklist.children] == [
        "Demo review checklist",
        "Session status visible: yes",
        "Detected event summary visible: yes",
        "Alert preview requires confirmation: yes",
        "Archive/reviewer metadata visible: yes",
        "Gate D blocker visible: product_judgment_evidence",
        "Human product judgment required: yes",
        "Action execution allowed: no",
        "Product Promise Alpha not passed",
    ]
    assert {child.kind for child in review_checklist.children} == {"label"}
    assert all(child.on_click is None for child in review_checklist.children)

    launch = _find_element_by_class(
        ui,
        "async-scholar-local-alpha-dashboard__launch",
    )
    assert launch is not None
    assert [child.text for child in launch.children] == [
        "Local demo launch",
        "Demo mode: local fixture/static only",
        "Launch command: python -m async_scholar "
        "local-alpha-dashboard-static-demo --output TEMP_HTML",
        "Inspection command: python -m async_scholar local-alpha-dashboard-inspection",
        "Server started: no",
        "Browser opened: no",
        "Live delivery: no",
        "Private data read: no",
        "Gate D not passed",
        "Product Promise Alpha not passed",
    ]
    assert {child.kind for child in launch.children} == {"label"}

    verification = _find_element_by_class(
        ui,
        "async-scholar-local-alpha-dashboard__verification",
    )
    assert verification is not None
    assert [child.text for child in verification.children] == [
        "Demo verification status",
        "Dashboard surface: local injected UI",
        "Source mode: injected fixture metadata",
        "Server started: no",
        "Browser opened: no",
        "Inspection command: python -m async_scholar local-alpha-dashboard-inspection",
        "Static export command: python -m async_scholar "
        "local-alpha-dashboard-static-demo --output TEMP_HTML",
        "Gate D evidence bundle: blocked",
        "Blocking evidence: product_judgment_evidence",
        "Manual product judgment required: yes",
        "Product Promise Alpha not passed",
    ]
    assert {child.kind for child in verification.children} == {"label"}
    assert all(child.on_click is None for child in verification.children)

    source_status = _find_element_by_class(
        ui,
        "async-scholar-local-alpha-dashboard__source-status",
    )
    assert source_status is not None
    assert [child.text for child in source_status.children] == [
        "Demo source status",
        "Session source: injected fixture metadata",
        "Event source: injected fixture metadata",
        "Alert source: injected fixture metadata",
        "Archive source: injected fixture metadata",
        "Gate D source: injected local handoff metadata",
        "Transcript source: not displayed",
        "Recording source: not displayed",
        "Private source data read: no",
        "Source refresh required: no",
        "Product Promise Alpha not passed",
    ]
    assert {child.kind for child in source_status.children} == {"label"}
    assert all(child.on_click is None for child in source_status.children)

    confirmation_queue = _find_element_by_class(
        ui,
        "async-scholar-local-alpha-dashboard__confirmation",
    )
    assert confirmation_queue is not None
    assert [child.text for child in confirmation_queue.children] == [
        "Confirmation queue",
        "User confirmation required",
        "Alert status: pending",
        "Participation action sent: no",
        "Autonomous participation: no",
        "Live delivery: no",
        "Academic answer behavior: no",
    ]
    assert {child.kind for child in confirmation_queue.children} == {"label"}

    action_controls = _find_element_by_class(
        ui,
        "async-scholar-local-alpha-dashboard__actions",
    )
    assert action_controls is not None
    assert [child.text for child in action_controls.children] == [
        "Action controls",
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
    ]
    assert {child.kind for child in action_controls.children} == {"label"}
    assert all(child.on_click is None for child in action_controls.children)

    archive_review_status = _find_element_by_class(
        ui,
        "async-scholar-local-alpha-dashboard__archive-review-status",
    )
    assert archive_review_status is not None
    assert [child.text for child in archive_review_status.children] == [
        "Archive review status",
        "Archive artifacts: metadata only",
        "Reviewer summary: metadata only",
        "Detected events archived: 9999",
        "Alert previews archived: pending confirmation",
        "Transcript text displayed: no",
        "Recording displayed: no",
        "Private paths displayed: no",
        "Delete/export execution: no",
        "Gate D not passed",
        "Product Promise Alpha not passed",
    ]
    assert {child.kind for child in archive_review_status.children} == {"label"}
    assert all(child.on_click is None for child in archive_review_status.children)

    rendered = "\n".join(ui.texts)
    assert "Gate D passed" not in rendered
    assert "Product Promise Alpha passed" not in rendered
    assert "satisfied" not in rendered.casefold()
    for private_value in PRIVATE_RENDER_VALUES:
        assert private_value not in rendered


def _dashboard_module():
    return importlib.import_module("async_scholar.ui.local_alpha_dashboard")


class StaticStatusSource:
    def __init__(self, snapshots: list[object]) -> None:
        self._snapshots = snapshots
        self.calls = 0

    def status(self) -> object:
        index = min(self.calls, len(self._snapshots) - 1)
        self.calls += 1
        return self._snapshots[index]


class StaticEventSource:
    def __init__(self, batches: list[list[object]]) -> None:
        self._batches = batches
        self.calls = 0

    def __call__(self) -> list[object]:
        index = min(self.calls, len(self._batches) - 1)
        self.calls += 1
        return self._batches[index]


class StaticAlertSource:
    def __init__(self, batches: list[list[object]]) -> None:
        self._batches = batches
        self.calls = 0

    def alerts(self) -> list[object]:
        index = min(self.calls, len(self._batches) - 1)
        self.calls += 1
        return self._batches[index]


class StaticArchiveSource:
    def __init__(self, batches: list[list[object]]) -> None:
        self._batches = batches
        self.calls = 0

    def items(self) -> list[object]:
        index = min(self.calls, len(self._batches) - 1)
        self.calls += 1
        return self._batches[index]


class FakeElement:
    def __init__(
        self,
        ui: FakeUI,
        kind: str,
        text: str | None = None,
        on_click=None,
    ) -> None:
        self.ui = ui
        self.kind = kind
        self.text = text
        self.on_click = on_click
        self.children: list[FakeElement] = []
        self.class_names: list[str] = []
        if ui._stack:
            ui._stack[-1].children.append(self)
        else:
            ui.roots.append(self)

    def __enter__(self) -> FakeElement:
        self.ui._stack.append(self)
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.ui._stack.pop()

    def classes(self, *_classes: str) -> FakeElement:
        self.class_names.extend(_classes)
        return self

    def props(self, *_props: str) -> FakeElement:
        return self

    def tooltip(self, *_tooltip: str) -> FakeElement:
        return self

    def clear(self) -> None:
        self.children.clear()


class FakeUI:
    def __init__(self) -> None:
        self.roots: list[FakeElement] = []
        self._stack: list[FakeElement] = []

    def column(self) -> FakeElement:
        return self._element("column")

    def row(self) -> FakeElement:
        return self._element("row")

    def card(self) -> FakeElement:
        return self._element("card")

    def label(self, text: object = "") -> FakeElement:
        return self._element("label", str(text))

    def button(
        self,
        text: str = "",
        *args: object,
        icon: str | None = None,
        on_click=None,
        **_kwargs: object,
    ) -> FakeElement:
        if args:
            raise AssertionError(f"unexpected positional button args: {args!r}")
        label = text or icon or ""
        return self._element("button", label, on_click)

    @property
    def texts(self) -> list[str]:
        return [element.text for element in self._walk() if element.text is not None]

    def click(self, text: str) -> None:
        matches = [
            element
            for element in self._walk()
            if element.kind == "button" and element.text == text
        ]
        assert matches, f"button {text!r} not found"
        callback = matches[0].on_click
        assert callable(callback)
        callback()

    def _element(
        self,
        kind: str,
        text: str | None = None,
        on_click=None,
    ) -> FakeElement:
        return FakeElement(self, kind, text, on_click)

    def _walk(self) -> list[FakeElement]:
        elements: list[FakeElement] = []
        stack = list(reversed(self.roots))
        while stack:
            element = stack.pop()
            elements.append(element)
            stack.extend(reversed(element.children))
        return elements


def _find_element_by_class(ui: FakeUI, class_name: str) -> FakeElement | None:
    for element in ui._walk():
        if any(class_name in value.split() for value in element.class_names):
            return element
    return None
