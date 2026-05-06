"""Import-safe microphone capture boundary contracts.

This module intentionally defines contracts only. It does not enumerate audio
devices, request microphone permission, start capture, run VAD/STT, or persist
audio. Raw PCM bytes are private in-memory payloads carried only by
``MicrophonePcmChunk`` instances.
"""

from __future__ import annotations

import math
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from numbers import Real
from typing import Protocol, runtime_checkable

DEFAULT_MIC_SAMPLE_RATE_HZ = 16_000
DEFAULT_MIC_CHANNEL_COUNT = 1
DEFAULT_MIC_CHUNK_DURATION_SECONDS = 1.0


@dataclass(frozen=True)
class MicrophoneCaptureConfig:
    """Configuration shared by future microphone source implementations."""

    sample_rate_hz: int = DEFAULT_MIC_SAMPLE_RATE_HZ
    channel_count: int = DEFAULT_MIC_CHANNEL_COUNT
    chunk_duration_seconds: float = DEFAULT_MIC_CHUNK_DURATION_SECONDS

    def __post_init__(self) -> None:
        _validate_positive_int(self.sample_rate_hz, "sample_rate_hz")
        _validate_positive_int(self.channel_count, "channel_count")
        _validate_finite_positive_seconds(
            self.chunk_duration_seconds,
            "chunk_duration_seconds",
        )
        object.__setattr__(
            self,
            "chunk_duration_seconds",
            float(self.chunk_duration_seconds),
        )


@dataclass(frozen=True)
class MicrophonePcmChunk:
    """Private in-memory PCM bytes with capture timing metadata.

    ``pcm_bytes`` is excluded from ``repr`` so accidental object formatting does
    not expose audio payload contents.
    """

    start_seconds: float
    end_seconds: float
    pcm_bytes: bytes = field(repr=False)
    sample_rate_hz: int = DEFAULT_MIC_SAMPLE_RATE_HZ
    channel_count: int = DEFAULT_MIC_CHANNEL_COUNT

    def __post_init__(self) -> None:
        _validate_finite_non_negative_seconds(
            self.start_seconds,
            "start_seconds",
        )
        _validate_finite_non_negative_seconds(
            self.end_seconds,
            "end_seconds",
        )
        if self.end_seconds < self.start_seconds:
            raise ValueError(
                "end_seconds must be greater than or equal to start_seconds",
            )
        if not isinstance(self.pcm_bytes, bytes):
            raise TypeError("pcm_bytes must be bytes")
        _validate_positive_int(self.sample_rate_hz, "sample_rate_hz")
        _validate_positive_int(self.channel_count, "channel_count")
        object.__setattr__(self, "start_seconds", float(self.start_seconds))
        object.__setattr__(self, "end_seconds", float(self.end_seconds))

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.start_seconds


@runtime_checkable
class MicrophoneSource(Protocol):
    """Boundary for future microphone sources that yield PCM chunks in time order."""

    config: MicrophoneCaptureConfig

    def __aiter__(self) -> AsyncIterator[MicrophonePcmChunk]:
        """Yield in-memory PCM chunks without persisting or logging audio bytes."""


def _validate_positive_int(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _validate_finite_positive_seconds(value: float, field_name: str) -> None:
    if not _is_finite_real(value) or value <= 0.0:
        raise ValueError(f"{field_name} must be finite and positive")


def _validate_finite_non_negative_seconds(value: float, field_name: str) -> None:
    if not _is_finite_real(value) or value < 0.0:
        raise ValueError(f"{field_name} must be finite and non-negative")


def _is_finite_real(value: object) -> bool:
    return (
        isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value)
    )


DEFAULT_MIC_CAPTURE_CONFIG = MicrophoneCaptureConfig()


__all__ = [
    "DEFAULT_MIC_CAPTURE_CONFIG",
    "DEFAULT_MIC_CHANNEL_COUNT",
    "DEFAULT_MIC_CHUNK_DURATION_SECONDS",
    "DEFAULT_MIC_SAMPLE_RATE_HZ",
    "MicrophoneCaptureConfig",
    "MicrophonePcmChunk",
    "MicrophoneSource",
]
