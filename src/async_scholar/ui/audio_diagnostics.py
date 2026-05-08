"""Privacy-safe NiceGUI audio diagnostics shell."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Protocol

SAFE_AUDIO_DIAGNOSTICS_FIELDS = (
    "status_label",
    "sample_rate_label",
    "channels_label",
    "peak_level_label",
    "rms_level_label",
    "clipping_label",
    "silence_label",
    "chunk_count_label",
    "elapsed_seconds_label",
)

_STATUS_LABELS = {
    "active": "Monitoring",
    "attention": "Attention needed",
    "error": "Attention needed",
    "idle": "Idle",
    "monitoring": "Monitoring",
    "ready": "Ready",
    "running": "Monitoring",
    "unavailable": "Unavailable",
    "unknown": "Unknown",
}


class AudioDiagnosticsSource(Protocol):
    """Injected source that supplies a snapshot-like diagnostics object."""

    def diagnostics(self) -> object:
        """Return the latest diagnostics snapshot."""


@dataclass(frozen=True)
class AudioDiagnosticsModel:
    """Allowlisted audio diagnostics display model."""

    status_label: str
    sample_rate_label: str
    channels_label: str
    peak_level_label: str
    rms_level_label: str
    clipping_label: str
    silence_label: str
    chunk_count_label: str
    elapsed_seconds_label: str


def normalize_audio_diagnostics(snapshot: object | None) -> AudioDiagnosticsModel:
    """Normalize a snapshot-like object into safe, controlled display labels."""

    return diagnostics_to_audio_model(snapshot)


def diagnostics_to_audio_model(snapshot: object | None) -> AudioDiagnosticsModel:
    """Convert allowlisted diagnostics fields into a safe display model."""

    status = _snapshot_value(snapshot, "status", "run_status", "state")
    sample_rate = _snapshot_value(snapshot, "sample_rate_hz", "sample_rate")
    channels = _snapshot_value(snapshot, "channels", "channel_count")
    peak_level = _snapshot_value(snapshot, "peak_level", "peak")
    rms_level = _snapshot_value(snapshot, "rms_level", "rms")
    clipping = _snapshot_value(snapshot, "clipping", "is_clipping", "clipped")
    silence = _snapshot_value(snapshot, "silence", "is_silent", "silent")
    chunk_count = _snapshot_value(snapshot, "chunk_count", "chunks")
    elapsed_seconds = _snapshot_value(snapshot, "elapsed_seconds", "elapsed")

    return AudioDiagnosticsModel(
        status_label=f"Status: {_status_value(status)}",
        sample_rate_label=_sample_rate_label(sample_rate),
        channels_label=_channels_label(channels),
        peak_level_label=_level_label("Peak", peak_level),
        rms_level_label=_level_label("RMS", rms_level),
        clipping_label=_state_label("Clipping", clipping),
        silence_label=_state_label("Silence", silence),
        chunk_count_label=_chunk_count_label(chunk_count),
        elapsed_seconds_label=_elapsed_seconds_label(elapsed_seconds),
    )


def format_audio_diagnostics_model(model: AudioDiagnosticsModel) -> tuple[str, ...]:
    """Return the renderable, allowlisted text for an audio diagnostics model."""

    return tuple(getattr(model, field) for field in SAFE_AUDIO_DIAGNOSTICS_FIELDS)


class AudioDiagnosticsView:
    """Controller for the audio diagnostics panel."""

    def __init__(self, source: AudioDiagnosticsSource | None, ui: Any) -> None:
        self._source = source
        self._ui = ui
        self._labels: list[Any] = []
        self.model = diagnostics_to_audio_model(self._read_diagnostics())
        self._render()

    def refresh(self) -> AudioDiagnosticsModel:
        """Refresh from the injected source only."""

        self.model = diagnostics_to_audio_model(self._read_diagnostics())
        text_values = format_audio_diagnostics_model(self.model)
        for label, text in zip(self._labels, text_values, strict=True):
            _set_label_text(label, text)
        return self.model

    def _read_diagnostics(self) -> object | None:
        if self._source is None:
            return None

        diagnostics = getattr(self._source, "diagnostics", None)
        if not callable(diagnostics):
            return None

        try:
            return diagnostics()
        except Exception:
            return None

    def _render(self) -> None:
        self._ui.label("Audio diagnostics")
        for text in format_audio_diagnostics_model(self.model):
            self._labels.append(self._ui.label(text))
        self._ui.button("Refresh", on_click=self.refresh)


def render_audio_diagnostics_view(
    source: AudioDiagnosticsSource | None = None,
    *,
    ui: Any | None = None,
) -> AudioDiagnosticsView:
    """Render the audio diagnostics panel and return its controller."""

    resolved_ui = ui if ui is not None else _default_ui()
    return AudioDiagnosticsView(source=source, ui=resolved_ui)


def _default_ui() -> Any:
    from nicegui import ui

    return ui


def _snapshot_value(snapshot: object | None, *names: str) -> object | None:
    if snapshot is None:
        return None

    if isinstance(snapshot, dict):
        for name in names:
            if name in snapshot:
                return snapshot[name]
        return None

    for name in names:
        try:
            return getattr(snapshot, name)
        except AttributeError:
            continue
        except Exception:
            return None
    return None


def _status_value(value: object | None) -> str:
    if not isinstance(value, str):
        return "Unavailable"

    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    return _STATUS_LABELS.get(normalized, "Unknown")


def _sample_rate_label(value: object | None) -> str:
    sample_rate = _bounded_int(value, minimum=1, maximum=768_000)
    if sample_rate is None:
        return "Sample rate: unknown"
    return f"Sample rate: {sample_rate} Hz"


def _channels_label(value: object | None) -> str:
    channels = _bounded_int(value, minimum=1, maximum=64)
    if channels is None:
        return "Channels: unknown"
    return f"Channels: {channels}"


def _level_label(name: str, value: object | None) -> str:
    level = _bounded_float(value, minimum=0.0, maximum=1.0)
    if level is None:
        return f"{name}: unknown"
    return f"{name}: {_format_number(level * 100.0)}%"


def _state_label(name: str, value: object | None) -> str:
    normalized = _bool_value(value)
    if normalized is None:
        return f"{name}: unknown"
    return f"{name}: {'yes' if normalized else 'no'}"


def _chunk_count_label(value: object | None) -> str:
    chunk_count = _bounded_int(value, minimum=0, maximum=1_000_000_000)
    if chunk_count is None:
        return "Chunks: unknown"
    return f"Chunks: {chunk_count}"


def _elapsed_seconds_label(value: object | None) -> str:
    elapsed_seconds = _bounded_float(value, minimum=0.0, maximum=1_000_000_000.0)
    if elapsed_seconds is None:
        return "Elapsed: unknown"
    return f"Elapsed: {_format_number(elapsed_seconds)}s"


def _bounded_int(value: object | None, *, minimum: int, maximum: int) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        normalized = value
    elif isinstance(value, float) and isfinite(value) and value.is_integer():
        normalized = int(value)
    else:
        return None

    if minimum <= normalized <= maximum:
        return normalized
    return None


def _bounded_float(
    value: object | None,
    *,
    minimum: float,
    maximum: float,
) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None

    normalized = float(value)
    if isfinite(normalized) and minimum <= normalized <= maximum:
        return normalized
    return None


def _bool_value(value: object | None) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _format_number(value: float) -> str:
    text = f"{value:.1f}"
    return text.removesuffix(".0")


def _set_label_text(label: object, text: str) -> None:
    set_text = getattr(label, "set_text", None)
    if callable(set_text):
        set_text(text)
        return

    try:
        label.text = text  # type: ignore[attr-defined]
    except Exception:
        return
