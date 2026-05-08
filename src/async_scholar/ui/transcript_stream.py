"""NiceGUI transcript stream surface for injected segment sources."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from math import isfinite
from typing import Any

SAFE_TRANSCRIPT_FIELDS = frozenset(
    {
        "text",
        "speaker",
        "start_seconds",
        "end_seconds",
    }
)

_TEXT_KEYS = ("text", "transcript", "content")
_SPEAKER_KEYS = ("speaker", "speaker_label")
_START_KEYS = ("start_seconds", "start_sec", "start", "start_time")
_END_KEYS = ("end_seconds", "end_sec", "end", "end_time")
_MAX_TEXT_CHARS = 2_000
_MAX_SPEAKER_CHARS = 40
_SPEAKER_PATTERN = re.compile(r"[A-Za-z0-9 ._-]+")


@dataclass(frozen=True)
class TranscriptSegmentModel:
    """Allowlisted transcript segment data safe for local UI rendering."""

    text: str
    speaker: str
    start_seconds: float | None
    end_seconds: float | None


class TranscriptStreamView:
    """Rendered transcript stream controller backed by an injected source."""

    def __init__(self, source: object, ui: object) -> None:
        self._source = source
        self._ui = ui
        self._stream = None
        self.segments: tuple[TranscriptSegmentModel, ...] = ()

    def render(self) -> TranscriptStreamView:
        with self._ui.column().classes("async-scholar-transcript-stream") as root:
            root.classes("w-full gap-3")
            with self._ui.row().classes("items-center justify-between w-full"):
                self._ui.label("Transcript").classes("text-lg font-semibold")
                self._ui.button(icon="refresh", on_click=self.refresh).props(
                    "flat round dense"
                ).tooltip("Refresh transcript")
            self._stream = self._ui.column().classes("w-full gap-2")

        self.refresh()
        return self

    def refresh(self) -> tuple[TranscriptSegmentModel, ...]:
        self.segments = normalize_transcript_segments(_load_segments(self._source))
        if self._stream is not None:
            self._stream.clear()
            with self._stream:
                if not self.segments:
                    self._ui.label("No transcript segments yet.").classes(
                        "text-sm text-gray-500"
                    )
                for segment in self.segments:
                    _render_segment(self._ui, segment)
        return self.segments


def render_transcript_stream_view(
    source: object,
    *,
    ui: object | None = None,
) -> TranscriptStreamView:
    """Render a transcript stream from an injected segment source."""

    if ui is None:
        from nicegui import ui as nicegui_ui

        ui = nicegui_ui
    return TranscriptStreamView(source, ui).render()


def normalize_transcript_segments(
    segments: Iterable[object],
) -> tuple[TranscriptSegmentModel, ...]:
    """Convert segment-like objects into allowlisted local UI models."""

    return tuple(segment_to_transcript_model(segment) for segment in segments)


def segment_to_transcript_model(segment: object) -> TranscriptSegmentModel:
    """Normalize one segment-like object without carrying private fields."""

    text = _coerce_text(_first_field(segment, _TEXT_KEYS))
    speaker = _coerce_speaker(_first_field(segment, _SPEAKER_KEYS))
    start_seconds = _coerce_seconds(_first_field(segment, _START_KEYS))
    end_seconds = _coerce_seconds(_first_field(segment, _END_KEYS))
    if (
        start_seconds is not None
        and end_seconds is not None
        and end_seconds < start_seconds
    ):
        end_seconds = None
    return TranscriptSegmentModel(
        text=text,
        speaker=speaker,
        start_seconds=start_seconds,
        end_seconds=end_seconds,
    )


def format_transcript_segment(segment: TranscriptSegmentModel) -> Mapping[str, str]:
    """Format an allowlisted segment for tests or non-NiceGUI renderers."""

    return {
        "time": _format_time_range(segment.start_seconds, segment.end_seconds),
        "speaker": segment.speaker,
        "text": segment.text,
    }


def _render_segment(ui: object, segment: TranscriptSegmentModel) -> None:
    formatted = format_transcript_segment(segment)
    with ui.column().classes("w-full gap-1 border-b border-gray-200 pb-2"):
        with ui.row().classes("items-center gap-2 text-xs text-gray-500"):
            ui.label(formatted["time"]).classes("font-mono")
            ui.label(formatted["speaker"]).classes("font-medium")
        ui.label(formatted["text"]).classes("text-sm whitespace-pre-wrap")


def _load_segments(source: object) -> tuple[object, ...]:
    if callable(source):
        loaded = source()
    elif hasattr(source, "segments") and callable(source.segments):
        loaded = source.segments()
    elif hasattr(source, "get_segments") and callable(source.get_segments):
        loaded = source.get_segments()
    else:
        loaded = source

    if loaded is None or isinstance(loaded, str | bytes):
        return ()
    if isinstance(loaded, Mapping):
        return (loaded,)
    try:
        return tuple(loaded)
    except TypeError:
        return ()


def _first_field(segment: object, names: tuple[str, ...]) -> Any:
    for name in names:
        value = _field_value(segment, name)
        if value is not None:
            return value
    return None


def _field_value(segment: object, name: str) -> Any:
    if isinstance(segment, Mapping):
        return segment.get(name)
    return getattr(segment, name, None)


def _coerce_text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    text = value.replace("\x00", "").strip()
    if len(text) > _MAX_TEXT_CHARS:
        return f"{text[: _MAX_TEXT_CHARS - 3]}..."
    return text


def _coerce_speaker(value: object) -> str:
    if not isinstance(value, str):
        return "Unknown speaker"
    speaker = " ".join(value.strip().split())
    if not speaker or len(speaker) > _MAX_SPEAKER_CHARS:
        return "Unknown speaker"
    if "/" in speaker or "\\" in speaker or ":" in speaker:
        return "Unknown speaker"
    if _SPEAKER_PATTERN.fullmatch(speaker) is None:
        return "Unknown speaker"
    return speaker


def _coerce_seconds(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        seconds = float(value)
    elif isinstance(value, str):
        normalized = value.strip()
        if not normalized or len(normalized) > 24:
            return None
        try:
            seconds = float(normalized)
        except ValueError:
            return None
    else:
        return None

    if not isfinite(seconds) or seconds < 0:
        return None
    return round(seconds, 3)


def _format_time_range(
    start_seconds: float | None,
    end_seconds: float | None,
) -> str:
    if start_seconds is None and end_seconds is None:
        return "time unknown"
    if start_seconds is not None and end_seconds is not None:
        return f"{_format_timestamp(start_seconds)} - {_format_timestamp(end_seconds)}"
    if start_seconds is not None:
        return _format_timestamp(start_seconds)
    return f"until {_format_timestamp(end_seconds)}"


def _format_timestamp(seconds: float) -> str:
    total_seconds = int(seconds)
    minutes, second = divmod(total_seconds, 60)
    hour, minute = divmod(minutes, 60)
    if hour:
        return f"{hour:02d}:{minute:02d}:{second:02d}"
    return f"{minute:02d}:{second:02d}"


__all__ = [
    "SAFE_TRANSCRIPT_FIELDS",
    "TranscriptSegmentModel",
    "TranscriptStreamView",
    "format_transcript_segment",
    "normalize_transcript_segments",
    "render_transcript_stream_view",
    "segment_to_transcript_model",
]
