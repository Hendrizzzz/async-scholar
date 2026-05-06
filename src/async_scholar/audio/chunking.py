"""Deterministic aggregation of VAD speech windows into STT chunks."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from math import isfinite

from async_scholar.audio.vad import SpeechWindow


def _validate_seconds(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"{name} must be a number of seconds")

    seconds = float(value)
    if not isfinite(seconds):
        raise ValueError(f"{name} must be finite")
    if seconds < 0.0:
        raise ValueError(f"{name} must be non-negative")
    return seconds


@dataclass(frozen=True)
class VadChunkingConfig:
    """Configuration for VAD-to-STT chunk aggregation."""

    pre_roll_seconds: float = 0.5
    post_roll_seconds: float = 0.8
    minimum_window_seconds: float = 8.0
    target_window_seconds: float = 15.0
    maximum_window_seconds: float = 30.0
    overlap_seconds: float = 1.0
    max_silence_before_flush_seconds: float = 2.0

    def __post_init__(self) -> None:
        fields = (
            "pre_roll_seconds",
            "post_roll_seconds",
            "minimum_window_seconds",
            "target_window_seconds",
            "maximum_window_seconds",
            "overlap_seconds",
            "max_silence_before_flush_seconds",
        )
        values = {
            field: _validate_seconds(getattr(self, field), field) for field in fields
        }
        for field, value in values.items():
            object.__setattr__(self, field, value)

        if self.maximum_window_seconds <= 0.0:
            raise ValueError("maximum_window_seconds must be greater than 0")
        if self.minimum_window_seconds > self.target_window_seconds:
            raise ValueError(
                "minimum_window_seconds must be less than or equal to "
                "target_window_seconds"
            )
        if self.target_window_seconds > self.maximum_window_seconds:
            raise ValueError(
                "target_window_seconds must be less than or equal to "
                "maximum_window_seconds"
            )
        if self.overlap_seconds >= self.maximum_window_seconds:
            raise ValueError("overlap_seconds must be less than maximum_window_seconds")


@dataclass(frozen=True)
class SttChunkWindow:
    """A deterministic seconds-based window suitable for STT input."""

    start_seconds: float
    end_seconds: float

    def __post_init__(self) -> None:
        start_seconds = _validate_seconds(self.start_seconds, "start_seconds")
        end_seconds = _validate_seconds(self.end_seconds, "end_seconds")
        if end_seconds < start_seconds:
            raise ValueError(
                "end_seconds must be greater than or equal to start_seconds"
            )
        object.__setattr__(self, "start_seconds", start_seconds)
        object.__setattr__(self, "end_seconds", end_seconds)

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.start_seconds


DEFAULT_VAD_CHUNKING_CONFIG = VadChunkingConfig()


@dataclass(frozen=True)
class _ValidatedSpeechWindow:
    start_seconds: float
    end_seconds: float


@dataclass(frozen=True)
class _SpeechGroup:
    start_seconds: float
    end_seconds: float
    overlap_before: bool


def aggregate_speech_windows(
    speech_windows: Iterable[SpeechWindow],
    *,
    audio_duration_seconds: float | None = None,
    config: VadChunkingConfig | None = None,
) -> list[SttChunkWindow]:
    """Aggregate ordered VAD speech windows into deterministic STT chunks.

    Speech windows close enough to share context are merged, tiny bursts are
    padded to the configured minimum where possible, and long ranges are split
    into bounded overlapping chunks.
    """

    if config is None:
        config = DEFAULT_VAD_CHUNKING_CONFIG
    elif not isinstance(config, VadChunkingConfig):
        raise TypeError("config must be a VadChunkingConfig")

    audio_duration = _validate_optional_audio_duration(audio_duration_seconds)
    windows = _validate_speech_windows(speech_windows)
    if not windows:
        return []

    groups = _group_speech_windows(windows, config, audio_duration)
    chunks: list[SttChunkWindow] = []
    for group in groups:
        for chunk in _chunks_for_group(group, config, audio_duration):
            chunks.append(_clamp_to_order(chunk, chunks))
    return chunks


def _validate_optional_audio_duration(
    audio_duration_seconds: float | None,
) -> float | None:
    if audio_duration_seconds is None:
        return None
    return _validate_seconds(audio_duration_seconds, "audio_duration_seconds")


def _validate_speech_windows(
    speech_windows: Iterable[SpeechWindow],
) -> list[_ValidatedSpeechWindow]:
    if isinstance(speech_windows, str | bytes):
        raise TypeError("speech_windows must be an iterable of SpeechWindow values")

    try:
        raw_windows = list(speech_windows)
    except TypeError as exc:
        raise TypeError(
            "speech_windows must be an iterable of SpeechWindow values"
        ) from exc

    validated: list[_ValidatedSpeechWindow] = []
    previous_start: float | None = None
    previous_end: float | None = None
    for index, window in enumerate(raw_windows):
        try:
            start_seconds = window.start_seconds
            end_seconds = window.end_seconds
        except AttributeError as exc:
            raise TypeError(
                f"speech_windows[{index}] must expose start_seconds and end_seconds"
            ) from exc

        start = _validate_seconds(
            start_seconds,
            f"speech_windows[{index}].start_seconds",
        )
        end = _validate_seconds(end_seconds, f"speech_windows[{index}].end_seconds")
        if end < start:
            raise ValueError(
                f"speech_windows[{index}].end_seconds must be greater than or "
                "equal to start_seconds"
            )
        if previous_start is not None and start < previous_start:
            raise ValueError("speech_windows must be ordered by start_seconds")
        if previous_end is not None and start < previous_end:
            raise ValueError("speech_windows must be ordered and non-overlapping")

        validated.append(_ValidatedSpeechWindow(start, end))
        previous_start = start
        previous_end = end

    return validated


def _group_speech_windows(
    windows: list[_ValidatedSpeechWindow],
    config: VadChunkingConfig,
    audio_duration: float | None,
) -> list[_SpeechGroup]:
    groups: list[_SpeechGroup] = []
    group_start = windows[0].start_seconds
    group_end = windows[0].end_seconds
    overlap_before = False

    for window in windows[1:]:
        silence_gap = window.start_seconds - group_end
        candidate_end = window.end_seconds
        candidate_duration = _planned_single_chunk_duration(
            group_start,
            candidate_end,
            overlap_before,
            config,
            audio_duration,
        )
        current_duration = _planned_single_chunk_duration(
            group_start,
            group_end,
            overlap_before,
            config,
            audio_duration,
        )

        flush_for_silence = silence_gap > config.max_silence_before_flush_seconds
        flush_for_maximum = candidate_duration > config.maximum_window_seconds
        flush_for_target = (
            candidate_duration > config.target_window_seconds
            and current_duration >= config.minimum_window_seconds
        )

        if flush_for_silence or flush_for_maximum or flush_for_target:
            groups.append(_SpeechGroup(group_start, group_end, overlap_before))
            group_start = window.start_seconds
            group_end = window.end_seconds
            overlap_before = not flush_for_silence
        else:
            group_end = window.end_seconds

    groups.append(_SpeechGroup(group_start, group_end, overlap_before))
    return groups


def _planned_single_chunk_duration(
    speech_start: float,
    speech_end: float,
    overlap_before: bool,
    config: VadChunkingConfig,
    audio_duration: float | None,
) -> float:
    start, end = _padded_span(
        speech_start,
        speech_end,
        overlap_before,
        config,
        audio_duration,
    )
    start, end = _expand_to_minimum(start, end, config, audio_duration)
    return end - start


def _chunks_for_group(
    group: _SpeechGroup,
    config: VadChunkingConfig,
    audio_duration: float | None,
) -> list[SttChunkWindow]:
    start, end = _padded_span(
        group.start_seconds,
        group.end_seconds,
        group.overlap_before,
        config,
        audio_duration,
    )
    start, end = _expand_to_minimum(start, end, config, audio_duration)
    return _split_span(start, end, config)


def _padded_span(
    speech_start: float,
    speech_end: float,
    overlap_before: bool,
    config: VadChunkingConfig,
    audio_duration: float | None,
) -> tuple[float, float]:
    start = speech_start - config.pre_roll_seconds
    if overlap_before:
        start -= config.overlap_seconds
    start = max(0.0, start)
    end = speech_end + config.post_roll_seconds

    if audio_duration is not None:
        start = min(start, audio_duration)
        end = min(end, audio_duration)
    end = max(start, end)
    return start, end


def _expand_to_minimum(
    start: float,
    end: float,
    config: VadChunkingConfig,
    audio_duration: float | None,
) -> tuple[float, float]:
    needed = config.minimum_window_seconds - (end - start)
    if needed <= 0.0:
        return start, end

    if audio_duration is None:
        return start, end + needed

    end_extension = min(needed, max(0.0, audio_duration - end))
    end += end_extension
    needed -= end_extension

    start_extension = min(needed, start)
    start -= start_extension
    needed -= start_extension

    end_extension = min(needed, max(0.0, audio_duration - end))
    end += end_extension
    return start, end


def _split_span(
    start: float,
    end: float,
    config: VadChunkingConfig,
) -> list[SttChunkWindow]:
    if end - start <= config.maximum_window_seconds:
        return [SttChunkWindow(start, end)]

    chunks: list[SttChunkWindow] = []
    cursor = start
    step_seconds = config.maximum_window_seconds - config.overlap_seconds
    while end - cursor > config.maximum_window_seconds:
        chunk_end = cursor + config.maximum_window_seconds
        chunks.append(SttChunkWindow(cursor, chunk_end))
        cursor += step_seconds

    if end - cursor < config.minimum_window_seconds and chunks:
        cursor = max(chunks[-1].start_seconds, end - config.minimum_window_seconds)

    chunks.append(SttChunkWindow(cursor, end))
    return chunks


def _clamp_to_order(
    chunk: SttChunkWindow,
    existing_chunks: list[SttChunkWindow],
) -> SttChunkWindow:
    if not existing_chunks:
        return chunk

    previous_start = existing_chunks[-1].start_seconds
    if chunk.start_seconds >= previous_start:
        return chunk

    return SttChunkWindow(previous_start, max(previous_start, chunk.end_seconds))
