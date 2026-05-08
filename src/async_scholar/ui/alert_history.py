"""Privacy-safe NiceGUI alert history shell."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

SAFE_ALERT_HISTORY_FIELDS = (
    "title",
    "message",
    "severity_label",
    "status_label",
    "confirmation_required_label",
)

_SEVERITY_LABELS = {
    "urgent": "Severity: Urgent",
    "high": "Severity: High",
    "warning": "Severity: Warning",
    "normal": "Severity: Normal",
    "info": "Severity: Info",
    "low": "Severity: Low",
}

_STATUS_LABELS = {
    "pending": "Status: Pending",
    "sent": "Status: Sent",
    "delivered": "Status: Delivered",
    "confirmed": "Status: Confirmed",
    "dismissed": "Status: Dismissed",
    "failed": "Status: Failed",
    "skipped": "Status: Skipped",
}

_TRUE_CONFIRMATION_TOKENS = {"1", "required", "true", "yes"}
_FALSE_CONFIRMATION_TOKENS = {"0", "false", "no", "not_required"}


class AlertHistorySource(Protocol):
    """Injected source used by the UI to retrieve alert-like objects."""

    def alerts(self) -> Iterable[object]:
        """Return alert-like objects for display."""


@dataclass(frozen=True)
class AlertHistoryAlertModel:
    """Allowlisted alert history display model."""

    title: str
    message: str
    severity_label: str
    status_label: str
    confirmation_required_label: str


def normalize_alert_history_alerts(
    alerts: Iterable[object] | None,
) -> tuple[AlertHistoryAlertModel, ...]:
    """Convert alert-like objects into safe display models."""

    if alerts is None or isinstance(alerts, str | bytes):
        return ()
    return tuple(alert_to_history_model(alert) for alert in alerts)


def alert_to_history_model(alert: object) -> AlertHistoryAlertModel:
    """Convert one alert-like object into a safe display model."""

    severity_label = _severity_label(_field(alert, "severity"))
    status_label = _status_label(_field(alert, "status"))
    confirmation_required_label = _confirmation_required_label(alert)
    title = _title_for_severity(severity_label)
    message = _message_for_confirmation(confirmation_required_label)
    return AlertHistoryAlertModel(
        title=title,
        message=message,
        severity_label=severity_label,
        status_label=status_label,
        confirmation_required_label=confirmation_required_label,
    )


def format_alert_history_item(model: AlertHistoryAlertModel) -> str:
    """Return a compact, safe text summary for one alert history item."""

    return (
        f"{model.title} | {model.message} | {model.severity_label} | "
        f"{model.status_label} | {model.confirmation_required_label}"
    )


class AlertHistoryView:
    """Controller returned by the alert history render function."""

    def __init__(self, source: AlertHistorySource, ui: Any) -> None:
        self._source = source
        self._ui = ui
        self.alerts: tuple[AlertHistoryAlertModel, ...] = ()
        self._items_container: Any | None = None

    def render(self) -> AlertHistoryView:
        """Render the alert history shell and return this controller."""

        with self._ui.column().classes("gap-3"):
            self._ui.label("Alert History").classes("text-lg font-semibold")
            self._items_container = self._ui.column().classes("gap-2")
            self.refresh()
            self._ui.button(icon="refresh", on_click=self.refresh).props("flat round")
        return self

    def refresh(self) -> tuple[AlertHistoryAlertModel, ...]:
        """Refresh display state from the injected source only."""

        self.alerts = normalize_alert_history_alerts(self._source.alerts())
        if self._items_container is not None:
            self._items_container.clear()
            with self._items_container:
                self._render_alerts()
        return self.alerts

    def _render_alerts(self) -> None:
        if not self.alerts:
            self._ui.label("No alerts yet").classes("text-sm text-gray-500")
            return

        for alert in self.alerts:
            with self._ui.column().classes("gap-1 border rounded p-2"):
                self._ui.label(alert.title).classes("font-medium")
                self._ui.label(alert.message).classes("text-sm text-gray-600")
                self._ui.label(alert.severity_label).classes("text-sm")
                self._ui.label(alert.status_label).classes("text-sm")
                self._ui.label(alert.confirmation_required_label).classes("text-sm")


def render_alert_history_view(
    source: AlertHistorySource,
    ui: Any | None = None,
) -> AlertHistoryView:
    """Render the alert history shell using an injected alert source."""

    if ui is None:
        from nicegui import ui as nicegui_ui

        ui = nicegui_ui
    return AlertHistoryView(source=source, ui=ui).render()


def _field(alert: object, name: str) -> object | None:
    if isinstance(alert, Mapping):
        return alert.get(name)
    return getattr(alert, name, None)


def _severity_label(value: object) -> str:
    return _SEVERITY_LABELS.get(_token(value), "Severity: Unknown")


def _status_label(value: object) -> str:
    return _STATUS_LABELS.get(_token(value), "Status: Unknown")


def _confirmation_required_label(alert: object) -> str:
    value = _field(alert, "confirmation_required")
    if value is None:
        value = _field(alert, "requires_confirmation")
    if isinstance(value, bool):
        if value:
            return "Confirmation required"
        return "No confirmation required"

    token = _token(value)
    if token in _TRUE_CONFIRMATION_TOKENS:
        return "Confirmation required"
    if token in _FALSE_CONFIRMATION_TOKENS:
        return "No confirmation required"
    return "Confirmation status unknown"


def _title_for_severity(severity_label: str) -> str:
    if severity_label == "Severity: Urgent":
        return "Urgent alert"
    if severity_label == "Severity: Unknown":
        return "Alert"
    return "Alert"


def _message_for_confirmation(confirmation_required_label: str) -> str:
    if confirmation_required_label == "Confirmation required":
        return "Review confirmation before acting."
    if confirmation_required_label == "No confirmation required":
        return "No confirmation is required."
    return "Confirmation status is unavailable."


def _token(value: object) -> str:
    raw_value = getattr(value, "value", value)
    if not isinstance(raw_value, str):
        return ""
    return raw_value.strip().casefold().replace("-", "_").replace(" ", "_")
