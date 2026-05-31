"""Local alpha dashboard shell built from injected safe UI sources."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from typing import Any

from async_scholar.ui.alert_history import (
    format_alert_history_item,
    normalize_alert_history_alerts,
    render_alert_history_view,
)
from async_scholar.ui.archive_browser import (
    format_archive_browser_item,
    normalize_archive_browser_items,
    render_archive_browser_view,
)
from async_scholar.ui.event_timeline import (
    format_event_timeline_event,
    normalize_event_timeline_events,
    render_event_timeline_view,
)

_RUN_STATUS_LABELS = {
    "completed": "Completed",
    "failed": "Failed",
    "idle": "Idle",
    "not_started": "Not started",
    "pending": "Pending",
    "ready": "Ready",
    "running": "Running",
    "stopped": "Stopped",
    "unknown": "Unknown",
}
_SUMMARY_RUN_STATUS_LABELS = {
    key: label.casefold() for key, label in _RUN_STATUS_LABELS.items()
}
_LOCAL_DEMO_LAUNCH_LABELS = (
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
)
_DEMO_VERIFICATION_STATUS_LABELS = (
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
)
_BACKEND_EVIDENCE_TRAIL_LABELS = (
    "Backend evidence trail",
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
_LOCAL_ALPHA_DEMO_RUNBOOK_LABELS = (
    "Local alpha demo runbook",
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
_LOCAL_ALPHA_ARTIFACT_SUMMARY_LABELS = (
    "Local alpha artifact summary",
    "Fixture artifacts: events.jsonl, alerts.log, reviewer.md",
    "Static dashboard artifact: local HTML export",
    "Gate D evidence bundle: stdout metadata only",
    "Gate D handoff packet: stdout metadata only",
    "Archive/reviewer contents displayed: no",
    "Private paths displayed: no",
    "Artifact opening performed: no",
    "Generated artifacts committed: no",
    "product_judgment_evidence remains blocking",
    "Product Promise Alpha not passed",
)
_LOCAL_ALPHA_FIXTURE_HANDOFF_LABELS = (
    "One-command fixture demo handoff",
    "Wrapper: scripts\\run_local_alpha_fixture_demo.ps1",
    "Fixture evidence: existing fixture-demo command",
    "Dashboard export: local-alpha-dashboard-static-demo --output local-html-file",
    "Gate D bundle check: gate-d-local-evidence-bundle",
    "Gate D handoff packet check: gate-d-handoff-packet-local",
    "Raw command output displayed: no",
    "User paths displayed: no",
    "Browser/server launched by page: no",
    "Product judgment recorded: no",
    "product_judgment_evidence remains blocking",
    "Product Promise Alpha not passed",
)
_LOCAL_ALPHA_FIXTURE_SUMMARY_EXPORT_LABELS = (
    "Fixture demo summary export",
    "Summary export: scripts\\run_local_alpha_fixture_demo.ps1 "
    "-SummaryOutput <local-summary-json>",
    "Summary kind: local_alpha_fixture_demo_sanitized_summary",
    "Fixture artifacts generated: yes",
    "Static dashboard generated: yes",
    "Raw command output included: no",
    "Private paths included: no",
    "Browser/server launched: no",
    "Live delivery performed: no",
    "Product judgment recorded: no",
    "Gate D evidence bundle: blocked",
    "Gate D handoff packet: manual judgment required",
    "product_judgment_evidence remains blocking",
    "Product Promise Alpha not passed",
)
_LOCAL_ALPHA_FIXTURE_SUMMARY_EXPORT_INSPECTION_LABELS = tuple(
    "Live delivery perform&#101;d: no"
    if label == "Live delivery performed: no"
    else label
    for label in _LOCAL_ALPHA_FIXTURE_SUMMARY_EXPORT_LABELS
)
_DEMO_SOURCE_STATUS_LABELS = (
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
)
_MANUAL_REVIEW_STATUS_LABELS = (
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
)
_DEMO_REVIEW_CHECKLIST_LABELS = (
    "Demo review checklist",
    "Session status visible: yes",
    "Detected event summary visible: yes",
    "Alert preview requires confirmation: yes",
    "Archive/reviewer metadata visible: yes",
    "Gate D blocker visible: product_judgment_evidence",
    "Human product judgment required: yes",
    "Action execution allowed: no",
    "Product Promise Alpha not passed",
)
_HUMAN_JUDGMENT_NEXT_STEP_LABELS = (
    "Human judgment next step",
    "Manual inspection required: yes",
    "Product judgment recorded: no",
    "AI can complete product judgment: no",
    "AI can record product judgment: no",
    "product_judgment_evidence remains blocking",
    "Action execution allowed: no",
    "Product Promise Alpha not passed",
)
_CONFIRMATION_QUEUE_LABELS = (
    "Confirmation queue",
    "User confirmation required",
    "Alert status: pending",
    "Participation action sent: no",
    "Autonomous participation: no",
    "Live delivery: no",
    "Academic answer behavior: no",
)
_ACTION_CONTROLS_LABELS = (
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
)
_SOURCE_KIND_LABELS = {
    "fixture": "Fixture",
    "fixture_demo": "Fixture demo",
    "unknown": "Unknown",
}
_COUNT_MAX = 9999


@dataclass(frozen=True, slots=True)
class LocalAlphaDashboardSources:
    """Injected sources used by the local alpha dashboard shell."""

    session_status: object
    events: object
    alerts: object
    archive: object
    gate_d: object | None = None


@dataclass(frozen=True, slots=True)
class LocalAlphaSessionStatusModel:
    """Display-ready local alpha session status."""

    run_status_label: str
    source_kind_label: str
    segment_count: int
    event_count: int


@dataclass(frozen=True, slots=True)
class GateDStatusModel:
    """Fail-closed Gate D display model."""

    title: str
    status_label: str
    blocker_label: str
    judgment_label: str
    evidence_labels: tuple[str, ...]
    safety_label: str


class LocalAlphaDashboardView:
    """Controller for the rendered local alpha dashboard shell."""

    def __init__(self, sources: LocalAlphaDashboardSources, ui: Any) -> None:
        self._sources = sources
        self._ui = ui
        self._summary_status_container: Any | None = None
        self._evidence_digest_container: Any | None = None
        self._manual_review_status_container: Any | None = None
        self._demo_review_checklist_container: Any | None = None
        self._human_judgment_next_step_container: Any | None = None
        self._session_container: Any | None = None
        self._demo_source_status_container: Any | None = None
        self._local_demo_launch_container: Any | None = None
        self._demo_verification_status_container: Any | None = None
        self._backend_evidence_trail_container: Any | None = None
        self._local_alpha_demo_runbook_container: Any | None = None
        self._local_alpha_artifact_summary_container: Any | None = None
        self._local_alpha_fixture_handoff_container: Any | None = None
        self._local_alpha_fixture_summary_export_container: Any | None = None
        self._confirmation_queue_container: Any | None = None
        self._action_controls_container: Any | None = None
        self._archive_review_status_container: Any | None = None
        self._gate_d_container: Any | None = None
        self.session_status = LocalAlphaSessionStatusModel(
            run_status_label="Unknown",
            source_kind_label="Unknown",
            segment_count=0,
            event_count=0,
        )
        self.gate_d_status = normalize_gate_d_status(sources.gate_d)
        self.event_timeline: Any | None = None
        self.alert_history: Any | None = None
        self.archive_browser: Any | None = None

    def render(self) -> LocalAlphaDashboardView:
        """Render the dashboard shell and return this controller."""

        with self._ui.column().classes("async-scholar-local-alpha-dashboard gap-4"):
            with self._ui.row().classes("items-center justify-between w-full"):
                self._ui.label("AsyncScholar local alpha").classes(
                    "text-xl font-semibold"
                )
                self._ui.button(
                    "Refresh dashboard",
                    icon="refresh",
                    on_click=self.refresh,
                ).props("outline")
            self._summary_status_container = self._ui.row().classes(
                "async-scholar-local-alpha-dashboard__summary gap-2 flex-wrap"
            )
            self._gate_d_container = self._ui.column().classes(
                "async-scholar-local-alpha-dashboard__gate gap-1"
            )
            self._evidence_digest_container = self._ui.column().classes(
                "async-scholar-local-alpha-dashboard__evidence gap-1"
            )
            self._manual_review_status_container = self._ui.column().classes(
                "async-scholar-local-alpha-dashboard__manual-review gap-1"
            )
            self._demo_review_checklist_container = self._ui.column().classes(
                "async-scholar-local-alpha-dashboard__review-checklist gap-1"
            )
            self._human_judgment_next_step_container = self._ui.column().classes(
                "async-scholar-local-alpha-dashboard__human-judgment-next-step gap-1"
            )
            self._session_container = self._ui.column().classes(
                "async-scholar-local-alpha-dashboard__session gap-2"
            )
            self._demo_source_status_container = self._ui.column().classes(
                "async-scholar-local-alpha-dashboard__source-status gap-1"
            )
            self._local_demo_launch_container = self._ui.column().classes(
                "async-scholar-local-alpha-dashboard__launch gap-1"
            )
            self._demo_verification_status_container = self._ui.column().classes(
                "async-scholar-local-alpha-dashboard__verification gap-1"
            )
            self._backend_evidence_trail_container = self._ui.column().classes(
                "async-scholar-local-alpha-dashboard__backend-evidence-trail gap-1"
            )
            self._local_alpha_demo_runbook_container = self._ui.column().classes(
                "async-scholar-local-alpha-dashboard__runbook gap-1"
            )
            self._local_alpha_artifact_summary_container = self._ui.column().classes(
                "async-scholar-local-alpha-dashboard__artifact-summary gap-1"
            )
            self._local_alpha_fixture_handoff_container = self._ui.column().classes(
                "async-scholar-local-alpha-dashboard__fixture-handoff gap-1"
            )
            self._local_alpha_fixture_summary_export_container = (
                self._ui.column().classes(
                    "async-scholar-local-alpha-dashboard__fixture-summary-export gap-1"
                )
            )
            self._render_gate_d_status()
            self._render_evidence_digest_panel()
            self._render_manual_review_status_panel()
            self._render_demo_review_checklist_panel()
            self._render_human_judgment_next_step_panel()
            self._render_session_status()
            self._render_summary_status_strip()
            self._render_demo_source_status_panel()
            self._render_local_demo_launch_panel()
            self._render_demo_verification_status_panel()
            self._render_backend_evidence_trail_panel()
            self._render_local_alpha_demo_runbook_panel()
            self._render_local_alpha_artifact_summary_panel()
            self._render_local_alpha_fixture_handoff_panel()
            self._render_local_alpha_fixture_summary_export_panel()
            self.event_timeline = render_event_timeline_view(
                self._sources.events,
                ui=self._ui,
            )
            self.alert_history = render_alert_history_view(
                _ConfirmationRequiredAlertPreviewSource(self._sources.alerts),
                ui=self._ui,
            )
            self._confirmation_queue_container = self._ui.column().classes(
                "async-scholar-local-alpha-dashboard__confirmation gap-1"
            )
            self._render_confirmation_queue_panel()
            self._action_controls_container = self._ui.column().classes(
                "async-scholar-local-alpha-dashboard__actions gap-1"
            )
            self._render_action_controls_panel()
            self._archive_review_status_container = self._ui.column().classes(
                "async-scholar-local-alpha-dashboard__archive-review-status gap-1"
            )
            self._render_archive_review_status_panel()
            self.archive_browser = render_archive_browser_view(
                _MetadataOnlyArchiveSource(self._sources.archive),
                ui=self._ui,
            )
        return self

    def refresh(self) -> LocalAlphaDashboardView:
        """Refresh all dashboard sections from injected sources."""

        self._render_gate_d_status()
        self._render_evidence_digest_panel()
        self._render_manual_review_status_panel()
        self._render_demo_review_checklist_panel()
        self._render_human_judgment_next_step_panel()
        self._render_session_status()
        self._render_summary_status_strip()
        self._render_demo_source_status_panel()
        self._render_local_demo_launch_panel()
        self._render_demo_verification_status_panel()
        self._render_backend_evidence_trail_panel()
        self._render_local_alpha_demo_runbook_panel()
        self._render_local_alpha_artifact_summary_panel()
        self._render_local_alpha_fixture_handoff_panel()
        self._render_local_alpha_fixture_summary_export_panel()
        if self.event_timeline is not None:
            self.event_timeline.refresh()
        if self.alert_history is not None:
            self.alert_history.refresh()
        self._render_confirmation_queue_panel()
        self._render_action_controls_panel()
        self._render_archive_review_status_panel()
        if self.archive_browser is not None:
            self.archive_browser.refresh()
        return self

    def _render_gate_d_status(self) -> None:
        self.gate_d_status = normalize_gate_d_status(self._sources.gate_d)
        container = self._gate_d_container
        if container is None:
            return
        if hasattr(container, "clear"):
            container.clear()
        with container:
            self._ui.label(self.gate_d_status.title).classes("text-lg font-semibold")
            self._ui.label(self.gate_d_status.status_label).classes("text-sm")
            self._ui.label(self.gate_d_status.blocker_label).classes("text-sm")
            self._ui.label(self.gate_d_status.judgment_label).classes("text-sm")
            for evidence_label in self.gate_d_status.evidence_labels:
                self._ui.label(evidence_label).classes("text-sm")
            self._ui.label(self.gate_d_status.safety_label).classes("text-sm")

    def _render_evidence_digest_panel(self) -> None:
        container = self._evidence_digest_container
        if container is None:
            return
        if hasattr(container, "clear"):
            container.clear()
        labels = _normalize_evidence_digest_labels(self.gate_d_status)
        with container:
            for label in labels:
                self._ui.label(label).classes("text-sm")

    def _render_session_status(self) -> None:
        self.session_status = normalize_dashboard_session_status(
            self._sources.session_status
        )
        container = self._session_container
        if container is None:
            return
        if hasattr(container, "clear"):
            container.clear()
        with container:
            self._ui.label("Session status").classes("text-lg font-semibold")
            self._ui.label(f"Run status: {self.session_status.run_status_label}")
            self._ui.label(f"Source kind: {self.session_status.source_kind_label}")
            self._ui.label(f"Segments: {self.session_status.segment_count}")
            self._ui.label(f"Events: {self.session_status.event_count}")

    def _render_manual_review_status_panel(self) -> None:
        container = self._manual_review_status_container
        if container is None:
            return
        if hasattr(container, "clear"):
            container.clear()
        with container:
            for label in _MANUAL_REVIEW_STATUS_LABELS:
                self._ui.label(label).classes("text-sm")

    def _render_demo_review_checklist_panel(self) -> None:
        container = self._demo_review_checklist_container
        if container is None:
            return
        if hasattr(container, "clear"):
            container.clear()
        with container:
            for label in _DEMO_REVIEW_CHECKLIST_LABELS:
                self._ui.label(label).classes("text-sm")

    def _render_human_judgment_next_step_panel(self) -> None:
        container = self._human_judgment_next_step_container
        if container is None:
            return
        if hasattr(container, "clear"):
            container.clear()
        with container:
            for label in _HUMAN_JUDGMENT_NEXT_STEP_LABELS:
                self._ui.label(label).classes("text-sm")

    def _render_summary_status_strip(self) -> None:
        container = self._summary_status_container
        if container is None:
            return
        if hasattr(container, "clear"):
            container.clear()
        labels = _normalize_summary_status_strip(
            self.gate_d_status,
            self.session_status,
        )
        with container:
            for label in labels:
                self._ui.label(label).classes("text-sm")

    def _render_local_demo_launch_panel(self) -> None:
        container = self._local_demo_launch_container
        if container is None:
            return
        if hasattr(container, "clear"):
            container.clear()
        with container:
            for label in _LOCAL_DEMO_LAUNCH_LABELS:
                self._ui.label(label).classes("text-sm")

    def _render_demo_source_status_panel(self) -> None:
        container = self._demo_source_status_container
        if container is None:
            return
        if hasattr(container, "clear"):
            container.clear()
        with container:
            for label in _DEMO_SOURCE_STATUS_LABELS:
                self._ui.label(label).classes("text-sm")

    def _render_demo_verification_status_panel(self) -> None:
        container = self._demo_verification_status_container
        if container is None:
            return
        if hasattr(container, "clear"):
            container.clear()
        with container:
            for label in _DEMO_VERIFICATION_STATUS_LABELS:
                self._ui.label(label).classes("text-sm")

    def _render_backend_evidence_trail_panel(self) -> None:
        container = self._backend_evidence_trail_container
        if container is None:
            return
        if hasattr(container, "clear"):
            container.clear()
        with container:
            for label in _BACKEND_EVIDENCE_TRAIL_LABELS:
                self._ui.label(label).classes("text-sm")

    def _render_local_alpha_demo_runbook_panel(self) -> None:
        container = self._local_alpha_demo_runbook_container
        if container is None:
            return
        if hasattr(container, "clear"):
            container.clear()
        with container:
            for label in _LOCAL_ALPHA_DEMO_RUNBOOK_LABELS:
                self._ui.label(label).classes("text-sm")

    def _render_local_alpha_artifact_summary_panel(self) -> None:
        container = self._local_alpha_artifact_summary_container
        if container is None:
            return
        if hasattr(container, "clear"):
            container.clear()
        with container:
            for label in _LOCAL_ALPHA_ARTIFACT_SUMMARY_LABELS:
                self._ui.label(label).classes("text-sm")

    def _render_local_alpha_fixture_handoff_panel(self) -> None:
        container = self._local_alpha_fixture_handoff_container
        if container is None:
            return
        if hasattr(container, "clear"):
            container.clear()
        with container:
            for label in _LOCAL_ALPHA_FIXTURE_HANDOFF_LABELS:
                self._ui.label(label).classes("text-sm")

    def _render_local_alpha_fixture_summary_export_panel(self) -> None:
        container = self._local_alpha_fixture_summary_export_container
        if container is None:
            return
        if hasattr(container, "clear"):
            container.clear()
        with container:
            for label in _LOCAL_ALPHA_FIXTURE_SUMMARY_EXPORT_LABELS:
                self._ui.label(label).classes("text-sm")

    def _render_confirmation_queue_panel(self) -> None:
        container = self._confirmation_queue_container
        if container is None:
            return
        if hasattr(container, "clear"):
            container.clear()
        with container:
            for label in _CONFIRMATION_QUEUE_LABELS:
                self._ui.label(label).classes("text-sm")

    def _render_action_controls_panel(self) -> None:
        container = self._action_controls_container
        if container is None:
            return
        if hasattr(container, "clear"):
            container.clear()
        with container:
            for label in _ACTION_CONTROLS_LABELS:
                self._ui.label(label).classes("text-sm")

    def _render_archive_review_status_panel(self) -> None:
        container = self._archive_review_status_container
        if container is None:
            return
        if hasattr(container, "clear"):
            container.clear()
        labels = _normalize_archive_review_status_labels(self.session_status)
        with container:
            for label in labels:
                self._ui.label(label).classes("text-sm")


def render_local_alpha_dashboard(
    sources: LocalAlphaDashboardSources,
    *,
    ui: Any | None = None,
) -> LocalAlphaDashboardView:
    """Render the local alpha dashboard from injected sources."""

    if ui is None:
        from nicegui import ui as nicegui_ui

        ui = nicegui_ui
    return LocalAlphaDashboardView(sources=sources, ui=ui).render()


def normalize_dashboard_session_status(
    source: object,
) -> LocalAlphaSessionStatusModel:
    """Normalize a session status source into safe dashboard labels."""

    snapshot = _read_session_snapshot(source)
    return LocalAlphaSessionStatusModel(
        run_status_label=_RUN_STATUS_LABELS.get(
            _safe_token(_field(snapshot, "run_status")),
            "Unknown",
        ),
        source_kind_label=_SOURCE_KIND_LABELS.get(
            _safe_token(_field(snapshot, "source_kind")),
            "Unknown",
        ),
        segment_count=_safe_count(_field(snapshot, "segment_count")),
        event_count=_safe_count(_field(snapshot, "event_count")),
    )


def _normalize_summary_status_strip(
    gate_d_status: GateDStatusModel,
    session_status: LocalAlphaSessionStatusModel,
) -> tuple[str, ...]:
    return (
        _summary_gate_d_label(gate_d_status),
        "Product judgment: deferred",
        f"Session: {_summary_session_status_label(session_status)}",
        f"Detected events: {_summary_event_count_label(session_status)}",
        "Alert: pending confirmation",
        "Live delivery: no",
    )


def _normalize_evidence_digest_labels(
    gate_d_status: GateDStatusModel,
) -> tuple[str, ...]:
    return (
        "Evidence digest",
        "Local evidence bundle: metadata only",
        "Product judgment evidence: blocking",
        *gate_d_status.evidence_labels,
        "Gate D not passed",
        "Product Promise Alpha not passed",
    )


def _normalize_archive_review_status_labels(
    session_status: LocalAlphaSessionStatusModel,
) -> tuple[str, ...]:
    return (
        "Archive review status",
        "Archive artifacts: metadata only",
        "Reviewer summary: metadata only",
        f"Detected events archived: {_summary_event_count_label(session_status)}",
        "Alert previews archived: pending confirmation",
        "Transcript text displayed: no",
        "Recording displayed: no",
        "Private paths displayed: no",
        "Delete/export execution: no",
        "Gate D not passed",
        "Product Promise Alpha not passed",
    )


def _summary_gate_d_label(_gate_d_status: GateDStatusModel) -> str:
    return "Gate D: blocked"


def _summary_session_status_label(
    session_status: LocalAlphaSessionStatusModel,
) -> str:
    run_status_label = getattr(session_status, "run_status_label", None)
    return _SUMMARY_RUN_STATUS_LABELS.get(_safe_token(run_status_label), "unknown")


def _summary_event_count_label(
    session_status: LocalAlphaSessionStatusModel,
) -> int:
    return _safe_count(getattr(session_status, "event_count", None))


def normalize_gate_d_status(source: object | None) -> GateDStatusModel:
    """Return fail-closed Gate D state for the local alpha shell."""

    snapshot = _read_gate_d_snapshot(source)
    return GateDStatusModel(
        title="Gate D safety",
        status_label="Gate D not passed",
        blocker_label="Blocked on product_judgment_evidence",
        judgment_label="Human product judgment: deferred",
        evidence_labels=_gate_d_evidence_labels(snapshot),
        safety_label=(
            "Local alpha demo only: no real meeting, private meeting data, "
            "audio capture, live delivery, participation, or academic answers."
        ),
    )


def format_gate_d_status(model: GateDStatusModel) -> str:
    """Format Gate D status for compact test and text renderers."""

    return (
        f"{model.title} | {model.status_label} | {model.blocker_label} | "
        f"{model.judgment_label} | {' | '.join(model.evidence_labels)} | "
        f"{model.safety_label}"
    )


def format_local_alpha_dashboard_inspection(
    sources: LocalAlphaDashboardSources,
) -> str:
    """Format a no-server local alpha inspection summary."""

    gate_d = normalize_gate_d_status(sources.gate_d)
    session = normalize_dashboard_session_status(sources.session_status)
    events = _safe_event_models(sources.events)
    alerts = _safe_alert_models(sources.alerts)
    archive_items = _safe_archive_models(sources.archive)

    lines = [
        "AsyncScholar local alpha inspection",
        "Server started: no",
        "Browser opened: no",
        gate_d.title,
        gate_d.status_label,
        gate_d.blocker_label,
        gate_d.judgment_label,
        *gate_d.evidence_labels,
        "Session status",
        f"Run status: {session.run_status_label}",
        f"Source kind: {session.source_kind_label}",
        f"Segments: {session.segment_count}",
        f"Events: {session.event_count}",
        "Detected events",
        *(format_event_timeline_event(event) for event in events),
        "Alert preview",
        *(format_alert_history_item(alert) for alert in alerts),
        "Archive and reviewer",
        *(format_archive_browser_item(item) for item in archive_items),
        *_LOCAL_ALPHA_FIXTURE_HANDOFF_LABELS,
        *_LOCAL_ALPHA_FIXTURE_SUMMARY_EXPORT_INSPECTION_LABELS,
        "Safety boundary",
        gate_d.safety_label,
    ]
    return "\n".join(lines) + "\n"


class _ConfirmationRequiredAlertPreviewSource:
    def __init__(self, source: object) -> None:
        self._source = source

    def alerts(self) -> tuple[Mapping[str, object], ...]:
        return tuple(_preview_alert(alert) for alert in _read_alerts(self._source))


def _preview_alert(alert: object) -> Mapping[str, object]:
    return {
        "severity": _field(alert, "severity"),
        "status": "pending",
        "confirmation_required": True,
    }


class _MetadataOnlyArchiveSource:
    def __init__(self, source: object) -> None:
        self._source = source

    def items(self) -> tuple[Mapping[str, object], ...]:
        return tuple(
            _metadata_archive_item(item) for item in _read_archive_items(self._source)
        )


def _metadata_archive_item(item: object) -> Mapping[str, object]:
    return {
        "title": "Local archive summary",
        "reviewer_excerpt": "Reviewer artifact metadata only.",
        "reviewer_status": _first_field(
            item,
            (
                "reviewer_status",
                "reviewer_availability",
                "reviewer_available",
                "has_reviewer",
                "status",
            ),
        ),
        "event_count": _first_field(item, ("event_count", "events_count")),
        "alert_count": _first_field(item, ("alert_count", "alerts_count")),
        "updated_time_label": "Updated unknown",
    }


def _read_archive_items(source: object) -> tuple[object, ...]:
    try:
        if callable(source):
            value = source()
        else:
            value = None
            for method_name in ("items", "sessions"):
                method = getattr(source, method_name, None)
                if callable(method):
                    value = method()
                    break
            if value is None:
                value = source
    except Exception:
        return ()

    if value is None or isinstance(value, str | bytes | Mapping):
        return ()
    try:
        return tuple(value)
    except TypeError:
        return ()


def _first_field(item: object, names: tuple[str, ...]) -> object | None:
    for name in names:
        value = _field(item, name)
        if value is not None:
            return value
    return None


def _read_alerts(source: object) -> tuple[object, ...]:
    try:
        if callable(source):
            value = source()
        else:
            alerts = getattr(source, "alerts", None)
            value = alerts() if callable(alerts) else source
    except Exception:
        return ()

    if value is None or isinstance(value, str | bytes | Mapping):
        return ()
    try:
        return tuple(value)
    except TypeError:
        return ()


def _read_session_snapshot(source: object) -> object | None:
    try:
        if callable(source):
            return source()
        status = getattr(source, "status", None)
        if callable(status):
            return status()
    except Exception:
        return None
    return source


def _safe_event_models(source: object) -> tuple[object, ...]:
    try:
        return tuple(normalize_event_timeline_events(source))
    except Exception:
        return ()


def _safe_alert_models(source: object) -> tuple[object, ...]:
    try:
        return normalize_alert_history_alerts(
            _ConfirmationRequiredAlertPreviewSource(source).alerts()
        )
    except Exception:
        return ()


def _safe_archive_models(source: object) -> tuple[object, ...]:
    try:
        return normalize_archive_browser_items(
            _MetadataOnlyArchiveSource(source).items()
        )
    except Exception:
        return ()


def _read_gate_d_snapshot(source: object | None) -> Mapping[str, object] | None:
    try:
        value = source() if callable(source) else source
    except Exception:
        return None
    if not isinstance(value, Mapping):
        return None
    return value


def _gate_d_evidence_labels(snapshot: Mapping[str, object] | None) -> tuple[str, ...]:
    satisfactory_count = _safe_gate_d_count(snapshot, "satisfactory_evidence_count")
    missing_count = _safe_gate_d_count(snapshot, "missing_evidence_count")
    return (
        f"Satisfactory evidence: {satisfactory_count}",
        f"Missing evidence: {missing_count}",
        "Blocking evidence: product_judgment_evidence",
        "Ready for gate review: no",
        "Manual judgment required: yes",
        "Manual judgment recorded: no",
    )


def _safe_gate_d_count(
    snapshot: Mapping[str, object] | None,
    name: str,
) -> int:
    if snapshot is None:
        return 0
    if _field(snapshot, "product_judgment_evidence_status") != "blocking":
        return 0
    return _safe_count(_field(snapshot, name))


def _field(value: object, name: str) -> object | None:
    if isinstance(value, Mapping):
        return value.get(name)
    return getattr(value, name, None)


def _safe_token(value: object) -> str:
    if not isinstance(value, str):
        return "unknown"
    return value.strip().casefold().replace("-", "_").replace(" ", "_")


def _safe_count(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return min(max(value, 0), _COUNT_MAX)
    if isinstance(value, float):
        if not isfinite(value):
            return 0
        return min(max(int(value), 0), _COUNT_MAX)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped.isdecimal():
            return 0
        return min(int(stripped), _COUNT_MAX)
    return 0


__all__ = [
    "GateDStatusModel",
    "LocalAlphaDashboardSources",
    "LocalAlphaDashboardView",
    "LocalAlphaSessionStatusModel",
    "format_gate_d_status",
    "format_local_alpha_dashboard_inspection",
    "normalize_dashboard_session_status",
    "normalize_gate_d_status",
    "render_local_alpha_dashboard",
]
