"""Import-safe microphone source diagnostics.

This module consumes ``MicrophoneSource`` chunks and returns safe timing/count
metadata only. It does not inspect, retain, log, print, persist, or expose PCM
payload bytes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real

from async_scholar.audio.mic_source import MicrophoneSource


@dataclass(frozen=True)
class MicrophoneDiagnosticSummary:
    """Safe metadata summary for chunks produced by a microphone source."""

    chunk_count: int
    total_audio_seconds: float
    first_start_seconds: float | None
    last_end_seconds: float | None
    sample_rate_hz: int | None
    channel_count: int | None
    continuity_count: int
    gap_count: int
    overlap_count: int

    def __post_init__(self) -> None:
        _validate_non_negative_int(self.chunk_count, "chunk_count")
        _validate_finite_non_negative_seconds(
            self.total_audio_seconds,
            "total_audio_seconds",
        )
        _validate_optional_finite_non_negative_seconds(
            self.first_start_seconds,
            "first_start_seconds",
        )
        _validate_optional_finite_non_negative_seconds(
            self.last_end_seconds,
            "last_end_seconds",
        )
        if self.last_end_seconds is not None and self.first_start_seconds is None:
            raise ValueError(
                "first_start_seconds is required when last_end_seconds is set",
            )
        if self.first_start_seconds is not None and self.last_end_seconds is None:
            raise ValueError(
                "last_end_seconds is required when first_start_seconds is set",
            )
        if (
            self.first_start_seconds is not None
            and self.last_end_seconds is not None
            and self.last_end_seconds < self.first_start_seconds
        ):
            raise ValueError(
                "last_end_seconds must be greater than or equal to first_start_seconds",
            )
        _validate_optional_positive_int(self.sample_rate_hz, "sample_rate_hz")
        _validate_optional_positive_int(self.channel_count, "channel_count")
        _validate_non_negative_int(self.continuity_count, "continuity_count")
        _validate_non_negative_int(self.gap_count, "gap_count")
        _validate_non_negative_int(self.overlap_count, "overlap_count")

        transition_count = self.continuity_count + self.gap_count + self.overlap_count
        if self.chunk_count == 0:
            if self.total_audio_seconds != 0.0:
                raise ValueError(
                    "total_audio_seconds must be 0.0 when chunk_count is 0",
                )
            if (
                self.first_start_seconds is not None
                or self.last_end_seconds is not None
            ):
                raise ValueError(
                    "first_start_seconds and last_end_seconds must be None "
                    "when chunk_count is 0",
                )
            if self.sample_rate_hz is not None or self.channel_count is not None:
                raise ValueError(
                    "sample_rate_hz and channel_count must be None "
                    "when chunk_count is 0",
                )
        elif transition_count != self.chunk_count - 1:
            raise ValueError(
                "continuity_count, gap_count, and overlap_count must sum to "
                "chunk_count - 1",
            )


async def collect_microphone_diagnostics(
    source: MicrophoneSource,
) -> MicrophoneDiagnosticSummary:
    """Consume a microphone source and return safe timing/count diagnostics."""

    chunk_count = 0
    total_audio_seconds = 0.0
    first_start_seconds: float | None = None
    last_end_seconds: float | None = None
    sample_rate_hz: int | None = None
    channel_count: int | None = None
    continuity_count = 0
    gap_count = 0
    overlap_count = 0

    previous_start_seconds: float | None = None
    previous_end_seconds: float | None = None

    async for chunk in source:
        start_seconds = _required_attr(chunk, "start_seconds", chunk_count)
        end_seconds = _required_attr(chunk, "end_seconds", chunk_count)
        chunk_sample_rate_hz = _required_attr(chunk, "sample_rate_hz", chunk_count)
        chunk_channel_count = _required_attr(chunk, "channel_count", chunk_count)

        _validate_finite_non_negative_seconds(
            start_seconds,
            f"chunk {chunk_count} start_seconds",
        )
        _validate_finite_non_negative_seconds(
            end_seconds,
            f"chunk {chunk_count} end_seconds",
        )
        start_seconds = float(start_seconds)
        end_seconds = float(end_seconds)
        if end_seconds < start_seconds:
            raise ValueError(
                f"chunk {chunk_count} end_seconds must be greater than or equal "
                "to start_seconds",
            )

        _validate_positive_int(
            chunk_sample_rate_hz,
            f"chunk {chunk_count} sample_rate_hz",
        )
        _validate_positive_int(
            chunk_channel_count,
            f"chunk {chunk_count} channel_count",
        )

        if (
            previous_start_seconds is not None
            and start_seconds < previous_start_seconds
        ):
            raise ValueError(
                f"chunk {chunk_count} start_seconds must not move backward",
            )
        if previous_end_seconds is not None and end_seconds < previous_end_seconds:
            raise ValueError(f"chunk {chunk_count} end_seconds must not move backward")

        if sample_rate_hz is None:
            sample_rate_hz = chunk_sample_rate_hz
        elif chunk_sample_rate_hz != sample_rate_hz:
            raise ValueError("chunk sample_rate_hz must be consistent across source")

        if channel_count is None:
            channel_count = chunk_channel_count
        elif chunk_channel_count != channel_count:
            raise ValueError("chunk channel_count must be consistent across source")

        if chunk_count == 0:
            first_start_seconds = start_seconds
        elif previous_end_seconds is not None:
            if start_seconds == previous_end_seconds:
                continuity_count += 1
            elif start_seconds > previous_end_seconds:
                gap_count += 1
            else:
                overlap_count += 1

        total_audio_seconds += end_seconds - start_seconds
        last_end_seconds = end_seconds
        previous_start_seconds = start_seconds
        previous_end_seconds = end_seconds
        chunk_count += 1

    return MicrophoneDiagnosticSummary(
        chunk_count=chunk_count,
        total_audio_seconds=total_audio_seconds,
        first_start_seconds=first_start_seconds,
        last_end_seconds=last_end_seconds,
        sample_rate_hz=sample_rate_hz,
        channel_count=channel_count,
        continuity_count=continuity_count,
        gap_count=gap_count,
        overlap_count=overlap_count,
    )


def _required_attr(chunk: object, attr_name: str, chunk_index: int) -> object:
    try:
        return getattr(chunk, attr_name)
    except AttributeError as exc:
        raise TypeError(f"chunk {chunk_index} is missing {attr_name}") from exc


def _validate_non_negative_int(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _validate_positive_int(value: object, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _validate_optional_positive_int(value: int | None, field_name: str) -> None:
    if value is not None:
        _validate_positive_int(value, field_name)


def _validate_finite_non_negative_seconds(value: object, field_name: str) -> None:
    if not _is_finite_real(value) or value < 0.0:
        raise ValueError(f"{field_name} must be finite and non-negative")


def _validate_optional_finite_non_negative_seconds(
    value: float | None,
    field_name: str,
) -> None:
    if value is not None:
        _validate_finite_non_negative_seconds(value, field_name)


def _is_finite_real(value: object) -> bool:
    return (
        isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(value)
    )


__all__ = [
    "MicrophoneDiagnosticSummary",
    "collect_microphone_diagnostics",
]
