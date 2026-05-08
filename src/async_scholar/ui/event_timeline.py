"""Privacy-safe NiceGUI event timeline shell."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from math import isfinite
from typing import Any, Protocol

SAFE_EVENT_TIMELINE_FIELDS = (
    "event_type_label",
    "detected_time_label",
    "confidence_label",
)

_EVENT_TYPE_LABELS = {
    "attendance": "Attendance prompt",
    "attendance_prompt": "Attendance prompt",
    "roll_call": "Attendance prompt",
    "participation": "Participation prompt",
    "participation_prompt": "Participation prompt",
    "question": "Question",
    "assignment": "Assignment",
    "deadline": "Deadline",
    "quiz": "Quiz",
    "exam": "Exam",
    "important": "Important event",
    "important_event": "Important event",
}
_EVENT_TYPE_FIELDS = ("event_type", "type", "kind", "rule_type")
_DETECTED_TIME_FIELDS = (
    "detected_at",
    "detected_time",
    "timestamp",
    "time",
    "start_seconds",
    "seconds",
)
_CONFIDENCE_FIELDS = ("confidence", "score", "probability")
_ISO_LIKE_TIME = re.compile(
    r"^\d{4}-\d{2}-\d{2}"
    r"(?:[ T]\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?"
    r"(?:Z|[+-]\d{2}:?\d{2})?)?$"
)


class EventTimelineSource(Protocol):
    """Injected event provider used by the timeline shell."""

    def __call__(self) -> Iterable[object]:
        """Return event-like objects for display."""


@dataclass(frozen=True)
class EventTimelineEventModel:
    """Allowlisted display model for one event timeline row."""

    event_type_label: str
    detected_time_label: str
    confidence_label: str


def normalize_event_timeline_events(source: object) -> list[EventTimelineEventModel]:
    """Build safe timeline rows from an injected source or iterable."""

    return [event_to_timeline_model(event) for event in _iter_source_events(source)]


def event_to_timeline_model(event: object) -> EventTimelineEventModel:
    """Convert one event-like object to the safe timeline display model."""

    return EventTimelineEventModel(
        event_type_label=_normalize_event_type(
            _read_first_field(event, _EVENT_TYPE_FIELDS)
        ),
        detected_time_label=_normalize_detected_time(
            _read_first_field(event, _DETECTED_TIME_FIELDS)
        ),
        confidence_label=_normalize_confidence(
            _read_first_field(event, _CONFIDENCE_FIELDS)
        ),
    )


def format_event_timeline_event(event: EventTimelineEventModel) -> str:
    """Format one safe timeline model for a compact UI label."""

    return (
        f"{event.event_type_label} - "
        f"{event.detected_time_label} - "
        f"{event.confidence_label}"
    )


class EventTimelineView:
    """Controller for a rendered event timeline shell."""

    def __init__(self, source: object, ui: object) -> None:
        self._source = source
        self._ui = ui
        self._events_container: object | None = None
        self.events: list[EventTimelineEventModel] = []

    def render(self) -> EventTimelineView:
        """Render the shell and return this controller."""

        with self._ui.column().classes("async-scholar-event-timeline"):
            self._ui.label("Event timeline").classes(
                "async-scholar-event-timeline__title"
            )
            self._events_container = self._ui.column().classes(
                "async-scholar-event-timeline__items"
            )
            refresh_button = self._ui.button(icon="refresh", on_click=self.refresh)
            if hasattr(refresh_button, "props"):
                refresh_button.props("flat round dense")
            if hasattr(refresh_button, "tooltip"):
                refresh_button.tooltip("Refresh events")

        self.refresh()
        return self

    def refresh(self) -> list[EventTimelineEventModel]:
        """Refresh rows from the injected source only."""

        self.events = normalize_event_timeline_events(self._source)
        if self._events_container is not None:
            self._render_events()
        return self.events

    def _render_events(self) -> None:
        container = self._events_container
        if container is None:
            return

        if hasattr(container, "clear"):
            container.clear()

        with container:
            if not self.events:
                self._ui.label("No events yet").classes(
                    "async-scholar-event-timeline__empty"
                )
                return

            for event in self.events:
                self._ui.label(format_event_timeline_event(event)).classes(
                    "async-scholar-event-timeline__event"
                )


def render_event_timeline_view(
    source: object,
    *,
    ui: object | None = None,
) -> EventTimelineView:
    """Render an event timeline shell from an injected event source."""

    if ui is None:
        from nicegui import ui as nicegui_ui

        ui = nicegui_ui

    return EventTimelineView(source=source, ui=ui).render()


def _iter_source_events(source: object) -> Iterable[object]:
    events = _read_source(source)
    if events is None or isinstance(events, str | bytes):
        return ()
    try:
        return tuple(events)
    except TypeError:
        return (events,)


def _read_source(source: object) -> object:
    if source is None:
        return ()
    if callable(source):
        return source()

    get_events = _safe_getattr(source, "get_events")
    if callable(get_events):
        return get_events()

    events = _safe_getattr(source, "events")
    if callable(events):
        return events()
    if events is not None:
        return events

    return source


def _read_first_field(event: object, names: tuple[str, ...]) -> object:
    if isinstance(event, Mapping):
        for name in names:
            if name in event:
                return event[name]
        return None

    for name in names:
        value = _safe_getattr(event, name)
        if value is not None:
            return value
    return None


def _safe_getattr(obj: object, name: str) -> Any:
    try:
        return getattr(obj, name)
    except Exception:
        return None


def _normalize_event_type(value: object) -> str:
    if not isinstance(value, str):
        return "Event"

    token = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return _EVENT_TYPE_LABELS.get(token, "Event")


def _normalize_detected_time(value: object) -> str:
    number = _finite_number(value)
    if number is not None:
        if number < 0:
            return "unknown time"
        return _format_seconds(number)

    if isinstance(value, datetime):
        return value.isoformat(sep=" ", timespec="seconds")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        text = value.strip()
        if len(text) <= 64 and _ISO_LIKE_TIME.fullmatch(text):
            return text.replace("T", " ")

    return "unknown time"


def _format_seconds(seconds: float) -> str:
    if seconds.is_integer():
        return f"{int(seconds)}s"
    return f"{seconds:.1f}s"


def _normalize_confidence(value: object) -> str:
    number = _finite_number(value)
    if number is None:
        return "unknown confidence"

    if 0 <= number <= 1:
        percent = round(number * 100)
    elif 1 < number <= 100:
        percent = round(number)
    else:
        return "unknown confidence"

    return f"{percent}% confidence"


def _finite_number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        number = float(value)
    elif isinstance(value, str):
        text = value.strip()
        if not re.fullmatch(r"[+-]?\d+(?:\.\d+)?", text):
            return None
        number = float(text)
    else:
        return None

    if not isfinite(number):
        return None
    return number
