"""NiceGUI archive/reviewer browser shell.

The shell intentionally renders only display-ready values supplied by an
injected source. It does not discover, read, export, or delete archive artifacts.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from math import isfinite
from typing import Any, Protocol

SAFE_ARCHIVE_BROWSER_FIELDS = (
    "title",
    "reviewer_excerpt",
    "reviewer_status_label",
    "event_count",
    "alert_count",
    "updated_time_label",
)

REVIEWER_EXCERPT_MAX_CHARS = 180
TITLE_MAX_CHARS = 80
UPDATED_TIME_MAX_CHARS = 60
COUNT_MAX = 9999

_PRIVATE_TEXT_MARKERS = (
    "auth",
    "browser profile",
    "cookie",
    "data/sessions",
    "data\\sessions",
    "debug/",
    "debug\\",
    ".env",
    ".jsonl",
    ".md",
    ".mp3",
    ".mp4",
    ".wav",
    "model-cache",
    "reviewer.md",
    "stderr",
    "stdout",
    "token",
    "traceback",
)

_STATUS_LABELS = {
    "available": "Reviewer available",
    "ready": "Reviewer available",
    "complete": "Reviewer available",
    "completed": "Reviewer available",
    "present": "Reviewer available",
    "true": "Reviewer available",
    "pending": "Reviewer pending",
    "processing": "Reviewer pending",
    "missing": "Reviewer unavailable",
    "unavailable": "Reviewer unavailable",
    "none": "Reviewer unavailable",
    "false": "Reviewer unavailable",
}


class ArchiveBrowserSource(Protocol):
    """Injected source for archive/reviewer display items."""

    def items(self) -> Iterable[Any]:
        """Return archive/reviewer item-like objects."""


@dataclass(frozen=True, slots=True)
class ArchiveBrowserItemModel:
    """Allowlisted archive/reviewer display model."""

    title: str
    reviewer_excerpt: str
    reviewer_status_label: str
    event_count: int
    alert_count: int
    updated_time_label: str


def normalize_archive_browser_items(
    items: Iterable[Any] | None,
) -> tuple[ArchiveBrowserItemModel, ...]:
    """Convert provider items into safe display models."""

    if items is None or isinstance(items, (str, bytes, Mapping)):
        return ()

    try:
        iterator = iter(items)
    except Exception:
        return ()

    models: list[ArchiveBrowserItemModel] = []
    try:
        for item in iterator:
            models.append(archive_item_to_browser_model(item))
    except Exception:
        return ()
    return tuple(models)


def archive_item_to_browser_model(item: Any) -> ArchiveBrowserItemModel:
    """Build an allowlisted display model from one provider item."""

    title = _safe_text(
        _first_value(item, ("title", "session_title", "reviewer_title")),
        default="Untitled session",
        max_chars=TITLE_MAX_CHARS,
        reject_private=True,
    )
    reviewer_excerpt = _safe_text(
        _first_value(
            item,
            ("reviewer_excerpt", "reviewer_summary", "summary", "excerpt"),
        ),
        default="",
        max_chars=REVIEWER_EXCERPT_MAX_CHARS,
        reject_private=True,
    )
    reviewer_status_label = _reviewer_status_label(
        _first_value(
            item,
            (
                "reviewer_status",
                "reviewer_availability",
                "reviewer_available",
                "has_reviewer",
                "status",
            ),
        )
    )
    event_count = _safe_count(_first_value(item, ("event_count", "events_count")))
    alert_count = _safe_count(_first_value(item, ("alert_count", "alerts_count")))
    updated_time_label = _safe_text(
        _first_value(
            item,
            ("updated_time_label", "updated_label", "updated_at", "updated_time"),
        ),
        default="Updated unknown",
        max_chars=UPDATED_TIME_MAX_CHARS,
        reject_private=True,
    )

    return ArchiveBrowserItemModel(
        title=title,
        reviewer_excerpt=reviewer_excerpt,
        reviewer_status_label=reviewer_status_label,
        event_count=event_count,
        alert_count=alert_count,
        updated_time_label=updated_time_label,
    )


def format_archive_browser_item(item: ArchiveBrowserItemModel) -> str:
    """Return a compact safe text summary for tests and simple renderers."""

    parts = [
        item.title,
        item.reviewer_status_label,
        f"Events: {item.event_count}",
        f"Alerts: {item.alert_count}",
        item.updated_time_label,
    ]
    if item.reviewer_excerpt:
        parts.append(item.reviewer_excerpt)
    return " | ".join(parts)


class ArchiveBrowserView:
    """Controller for the archive/reviewer browser shell."""

    def __init__(self, source: Any, ui: Any) -> None:
        self._source = source
        self._ui = ui
        self._items_container: Any | None = None
        self.items: tuple[ArchiveBrowserItemModel, ...] = ()

    def render(self) -> ArchiveBrowserView:
        """Render the browser shell and load the initial provider snapshot."""

        with self._ui.column().classes("async-scholar-archive-browser gap-3"):
            with self._ui.row().classes("items-center justify-between"):
                self._ui.label("Archive").classes("text-h6")
                self._ui.button("Refresh", on_click=self.refresh).props("outline")
            self._items_container = self._ui.column().classes("gap-2")
        self.refresh()
        return self

    def refresh(self) -> None:
        """Refresh from the injected source only."""

        self.items = normalize_archive_browser_items(_source_items(self._source))
        self._render_items()

    def _render_items(self) -> None:
        if self._items_container is None:
            return

        if hasattr(self._items_container, "clear"):
            self._items_container.clear()

        with self._items_container:
            if not self.items:
                self._ui.label("No archived sessions yet.").classes(
                    "text-body2 text-grey-7"
                )
                return

            for item in self.items:
                with self._ui.card().classes("w-full"):
                    self._ui.label(item.title).classes("text-subtitle1")
                    self._ui.label(item.reviewer_status_label).classes("text-body2")
                    self._ui.label(f"Events: {item.event_count}").classes("text-body2")
                    self._ui.label(f"Alerts: {item.alert_count}").classes("text-body2")
                    self._ui.label(item.updated_time_label).classes("text-caption")
                    if item.reviewer_excerpt:
                        self._ui.label(item.reviewer_excerpt).classes("text-body2")


def render_archive_browser_view(
    source: Any,
    ui: Any | None = None,
) -> ArchiveBrowserView:
    """Render the archive/reviewer browser shell."""

    if ui is None:
        from nicegui import ui as nicegui_ui

        ui = nicegui_ui
    return ArchiveBrowserView(source=source, ui=ui).render()


def _source_items(source: Any) -> Iterable[Any]:
    for method_name in ("items", "sessions"):
        method = getattr(source, method_name, None)
        if callable(method):
            try:
                result = method()
            except Exception:
                return ()
            return result if result is not None else ()
    return ()


def _first_value(item: Any, names: tuple[str, ...]) -> Any:
    if isinstance(item, Mapping):
        for name in names:
            if name in item:
                return item[name]
        return None

    for name in names:
        try:
            return getattr(item, name)
        except AttributeError:
            continue
    return None


def _safe_text(
    value: Any,
    *,
    default: str,
    max_chars: int,
    reject_private: bool,
) -> str:
    if not isinstance(value, str):
        return default

    normalized = " ".join(value.split())
    if not normalized:
        return default
    if reject_private and _looks_private(normalized):
        return default
    if len(normalized) <= max_chars:
        return normalized
    return f"{normalized[: max_chars - 3].rstrip()}..."


def _looks_private(value: str) -> bool:
    lowered = value.lower()
    if any(marker in lowered for marker in _PRIVATE_TEXT_MARKERS):
        return True
    if len(value) >= 3 and value[1] == ":" and value[2] in {"/", "\\"}:
        return True
    if "\\" in value:
        return True
    if lowered.startswith(("/", "~/", "./", "../")):
        return True
    if "/" in value:
        segments = [segment.strip() for segment in value.split("/") if segment.strip()]
        return len(segments) >= 2 and all(" " not in segment for segment in segments)
    return False


def _reviewer_status_label(value: Any) -> str:
    if isinstance(value, bool):
        return _STATUS_LABELS[str(value).lower()]
    if not isinstance(value, str):
        return "Reviewer unknown"

    normalized = " ".join(value.lower().replace("_", " ").replace("-", " ").split())
    key = normalized.replace(" ", "_")
    return _STATUS_LABELS.get(normalized, _STATUS_LABELS.get(key, "Reviewer unknown"))


def _safe_count(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return min(max(value, 0), COUNT_MAX)
    if isinstance(value, float):
        if not isfinite(value):
            return 0
        return min(max(int(value), 0), COUNT_MAX)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped.isdecimal():
            return 0
        return min(int(stripped), COUNT_MAX)
    return 0
