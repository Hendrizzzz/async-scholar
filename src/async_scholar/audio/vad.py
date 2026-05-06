"""Minimal Silero VAD wrapper for local audio files."""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from numbers import Real
from os import PathLike


@dataclass(frozen=True, slots=True)
class SpeechWindow:
    """A detected speech span in seconds."""

    start_seconds: float
    end_seconds: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.start_seconds):
            raise ValueError("Speech window start must be finite.")
        if not math.isfinite(self.end_seconds):
            raise ValueError("Speech window end must be finite.")
        if self.start_seconds < 0:
            raise ValueError("Speech window start must be non-negative.")
        if self.end_seconds <= self.start_seconds:
            raise ValueError("Speech window end must be after start.")


class InvalidVadTimestampError(ValueError):
    """Raised when Silero returns a timestamp shape AsyncScholar cannot use."""


ReadAudioFn = Callable[..., object]
GetSpeechTimestampsFn = Callable[..., Iterable[Mapping[str, object]]]
SileroRuntime = tuple[object, ReadAudioFn, GetSpeechTimestampsFn]
SileroRuntimeLoader = Callable[[], SileroRuntime]


@dataclass(slots=True)
class SileroVadDetector:
    """Lazy file-level adapter around Silero VAD."""

    sample_rate: int = 16_000
    loader: SileroRuntimeLoader | None = field(default=None, repr=False)
    _runtime: SileroRuntime | None = field(default=None, init=False, repr=False)

    def detect_file(self, audio_path: str | PathLike[str]) -> list[SpeechWindow]:
        """Run Silero VAD on a local audio file and return speech windows."""

        _validate_sample_rate(self.sample_rate)
        model, read_audio, get_speech_timestamps = self._ensure_runtime()
        audio = read_audio(str(audio_path), sampling_rate=self.sample_rate)
        timestamps = get_speech_timestamps(
            audio,
            model,
            sampling_rate=self.sample_rate,
            return_seconds=False,
        )
        return speech_windows_from_timestamps(
            timestamps,
            sample_rate=self.sample_rate,
        )

    def _ensure_runtime(self) -> SileroRuntime:
        if self._runtime is None:
            loader = self.loader or _load_silero_runtime
            self._runtime = loader()
        return self._runtime


def detect_speech_windows(
    audio_path: str | PathLike[str],
    *,
    sample_rate: int = 16_000,
) -> list[SpeechWindow]:
    """Detect speech windows in a local audio file with a lazily loaded model."""

    return SileroVadDetector(sample_rate=sample_rate).detect_file(audio_path)


def speech_windows_from_timestamps(
    timestamps: Iterable[Mapping[str, object]],
    *,
    sample_rate: int,
) -> list[SpeechWindow]:
    """Convert Silero sample-index timestamps into local speech windows."""

    _validate_sample_rate(sample_rate)
    return [
        _speech_window_from_timestamp(timestamp, index, sample_rate)
        for index, timestamp in enumerate(timestamps)
    ]


def _load_silero_runtime() -> SileroRuntime:
    from silero_vad import get_speech_timestamps, load_silero_vad, read_audio

    return load_silero_vad(), read_audio, get_speech_timestamps


def _speech_window_from_timestamp(
    timestamp: Mapping[str, object],
    timestamp_index: int,
    sample_rate: int,
) -> SpeechWindow:
    if not isinstance(timestamp, Mapping):
        raise InvalidVadTimestampError(
            f"Silero timestamp {timestamp_index} must be a mapping."
        )

    start_samples = _read_sample(timestamp, "start", timestamp_index)
    end_samples = _read_sample(timestamp, "end", timestamp_index)
    if start_samples < 0:
        raise InvalidVadTimestampError(
            f"Silero timestamp {timestamp_index} has a negative start sample."
        )
    if end_samples <= start_samples:
        raise InvalidVadTimestampError(
            f"Silero timestamp {timestamp_index} end sample must be after start."
        )
    return SpeechWindow(
        start_seconds=start_samples / sample_rate,
        end_seconds=end_samples / sample_rate,
    )


def _read_sample(
    timestamp: Mapping[str, object],
    key: str,
    timestamp_index: int,
) -> float:
    if key not in timestamp:
        raise InvalidVadTimestampError(
            f"Silero timestamp {timestamp_index} is missing {key!r}."
        )

    value = timestamp[key]
    if isinstance(value, bool) or not isinstance(value, Real):
        raise InvalidVadTimestampError(
            f"Silero timestamp {timestamp_index} {key!r} sample must be numeric."
        )

    sample = float(value)
    if not math.isfinite(sample):
        raise InvalidVadTimestampError(
            f"Silero timestamp {timestamp_index} {key!r} sample must be finite."
        )
    return sample


def _validate_sample_rate(sample_rate: int) -> None:
    if sample_rate <= 0:
        raise ValueError("Sample rate must be positive.")
