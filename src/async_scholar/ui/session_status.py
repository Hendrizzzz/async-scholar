"""Minimal NiceGUI session status view shell."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from nicegui import ui

SAFE_STATUS_FIELDS = (
    "run_status",
    "source_kind",
    "segment_count",
    "event_count",
)

_ALLOWED_RUN_STATUSES = frozenset(
    {
        "completed",
        "failed",
        "idle",
        "not_started",
        "pending",
        "ready",
        "running",
        "stopped",
        "unknown",
    }
)
_ALLOWED_SOURCE_KINDS = frozenset({"fixture", "fixture_demo", "unknown"})

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
_SOURCE_KIND_LABELS = {
    "fixture": "Fixture",
    "fixture_demo": "Fixture demo",
    "unknown": "Unknown",
}
_FIELD_LABELS = {
    "run_status": "Run status",
    "source_kind": "Source kind",
    "segment_count": "Segments",
    "event_count": "Events",
}


class SessionStatusWorker(Protocol):
    """Worker surface observed by the UI shell."""

    def start(self) -> object:
        """Start the worker and return a status snapshot."""

    def stop(self) -> object:
        """Stop the worker and return a status snapshot."""

    def status(self) -> object:
        """Return the current status snapshot."""


@dataclass(frozen=True, slots=True)
class SessionStatusModel:
    """Privacy-safe status data rendered by the UI."""

    run_status: str
    source_kind: str
    segment_count: int
    event_count: int


@dataclass(frozen=True, slots=True)
class StatusDisplayRow:
    """Display-ready status row."""

    label: str
    value: str


class SessionStatusView:
    """Controller returned by the NiceGUI view for tests and UI callbacks."""

    def __init__(self, worker: SessionStatusWorker) -> None:
        self._worker = worker
        self._labels: dict[str, Any] = {}
        self._model = _snapshot_from_callback(worker.status)

    @property
    def model(self) -> SessionStatusModel:
        """Return the latest privacy-safe status model."""
        return self._model

    def bind_labels(self, labels: Mapping[str, Any]) -> None:
        """Bind NiceGUI label elements to safe status fields."""
        self._labels = {
            field_name: label
            for field_name, label in labels.items()
            if field_name in SAFE_STATUS_FIELDS
        }
        self._render_labels()

    def refresh(self) -> SessionStatusModel:
        """Refresh from the worker status surface."""
        return self._update_from(self._worker.status)

    def start(self) -> SessionStatusModel:
        """Start through the worker surface and refresh the safe model."""
        return self._update_from(self._worker.start)

    def stop(self) -> SessionStatusModel:
        """Stop through the worker surface and refresh the safe model."""
        return self._update_from(self._worker.stop)

    def _update_from(self, callback: Callable[[], object]) -> SessionStatusModel:
        self._model = _snapshot_from_callback(callback)
        self._render_labels()
        return self._model

    def _render_labels(self) -> None:
        row_values = {
            field_name: row.value
            for field_name, row in zip(
                SAFE_STATUS_FIELDS,
                format_status_model(self._model),
                strict=True,
            )
        }
        for field_name, value in row_values.items():
            label = self._labels.get(field_name)
            if label is not None:
                label.set_text(value)


def render_session_status_view(worker: SessionStatusWorker) -> SessionStatusView:
    """Render a minimal NiceGUI session status view for a worker."""
    view = SessionStatusView(worker)
    labels: dict[str, Any] = {}

    with ui.column().classes("gap-3 p-4"):
        ui.label("Session status").classes("text-lg font-semibold")
        with ui.grid(columns=2).classes("gap-x-4 gap-y-2 items-center"):
            for row in format_status_model(view.model):
                ui.label(row.label).classes("text-sm text-gray-600")
                field_name = _field_name_for_label(row.label)
                labels[field_name] = ui.label(row.value).classes("font-mono")
        with ui.row().classes("gap-2"):
            ui.button("Start", icon="play_arrow", on_click=view.start)
            ui.button("Stop", icon="stop", on_click=view.stop)
            ui.button("Refresh", icon="refresh", on_click=view.refresh)

    view.bind_labels(labels)
    return view


def snapshot_to_status_model(snapshot: object) -> SessionStatusModel:
    """Convert a worker snapshot into the allowlisted UI status model."""
    return SessionStatusModel(
        run_status=_safe_choice(
            _read_snapshot_field(snapshot, "run_status"),
            allowed_values=_ALLOWED_RUN_STATUSES,
        ),
        source_kind=_safe_choice(
            _read_snapshot_field(snapshot, "source_kind"),
            allowed_values=_ALLOWED_SOURCE_KINDS,
        ),
        segment_count=_safe_count(_read_snapshot_field(snapshot, "segment_count")),
        event_count=_safe_count(_read_snapshot_field(snapshot, "event_count")),
    )


def format_status_model(model: SessionStatusModel) -> tuple[StatusDisplayRow, ...]:
    """Return display labels and formatted values for the safe status model."""
    return (
        StatusDisplayRow(
            _FIELD_LABELS["run_status"],
            _RUN_STATUS_LABELS.get(model.run_status, _RUN_STATUS_LABELS["unknown"]),
        ),
        StatusDisplayRow(
            _FIELD_LABELS["source_kind"],
            _SOURCE_KIND_LABELS.get(
                model.source_kind,
                _SOURCE_KIND_LABELS["unknown"],
            ),
        ),
        StatusDisplayRow(_FIELD_LABELS["segment_count"], str(model.segment_count)),
        StatusDisplayRow(_FIELD_LABELS["event_count"], str(model.event_count)),
    )


def _snapshot_from_callback(callback: Callable[[], object]) -> SessionStatusModel:
    try:
        snapshot = callback()
    except Exception:
        return SessionStatusModel(
            run_status="failed",
            source_kind="unknown",
            segment_count=0,
            event_count=0,
        )
    return snapshot_to_status_model(snapshot)


def _read_snapshot_field(snapshot: object, field_name: str) -> object:
    if isinstance(snapshot, Mapping):
        return snapshot.get(field_name)
    return getattr(snapshot, field_name, None)


def _safe_choice(value: object, *, allowed_values: frozenset[str]) -> str:
    if not isinstance(value, str):
        return "unknown"
    normalized = value.strip().lower().replace("-", "_")
    if normalized in allowed_values:
        return normalized
    return "unknown"


def _safe_count(value: object) -> int:
    if isinstance(value, bool):
        return 0
    try:
        count = int(value)
    except (TypeError, ValueError):
        return 0
    return max(count, 0)


def _field_name_for_label(label: str) -> str:
    for field_name, field_label in _FIELD_LABELS.items():
        if field_label == label:
            return field_name
    return "run_status"


__all__ = [
    "SAFE_STATUS_FIELDS",
    "SessionStatusModel",
    "SessionStatusView",
    "SessionStatusWorker",
    "StatusDisplayRow",
    "format_status_model",
    "render_session_status_view",
    "snapshot_to_status_model",
]
