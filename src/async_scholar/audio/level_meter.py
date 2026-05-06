"""Metadata-only PCM level readings for microphone chunks."""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from typing import Any

from async_scholar.audio.mic_source import MicrophonePcmChunk, MicrophoneSource

_SIGNED_16_BIT_SAMPLE_WIDTH_BYTES = 2
_SIGNED_16_BIT_FULL_SCALE = 32768.0


class InvalidMicrophoneLevelInputError(ValueError):
    """Raised when microphone PCM cannot be measured as signed 16-bit audio."""


@dataclass(frozen=True)
class MicrophoneLevelReading:
    """Safe scalar level metadata for one microphone PCM chunk."""

    start_seconds: float
    end_seconds: float
    sample_rate_hz: int
    channel_count: int
    frame_count: int
    sample_count: int
    peak_amplitude: int
    normalized_peak_level: float
    normalized_rms_level: float


def measure_microphone_level(chunk: MicrophonePcmChunk) -> MicrophoneLevelReading:
    """Measure a 16-bit little-endian signed PCM microphone chunk."""

    start_seconds = _required_seconds(chunk, ("start_seconds",), "start_seconds")
    end_seconds = _required_seconds(chunk, ("end_seconds",), "end_seconds")
    sample_rate_hz = _required_positive_int(
        chunk,
        ("sample_rate_hz",),
        "sample_rate_hz",
    )
    channel_count = _required_positive_int(
        chunk,
        ("channel_count",),
        "channel_count",
    )
    _validate_sample_width(chunk)
    pcm_bytes = _required_pcm_bytes(chunk)

    byte_count = len(pcm_bytes)
    if byte_count % _SIGNED_16_BIT_SAMPLE_WIDTH_BYTES != 0:
        raise InvalidMicrophoneLevelInputError(
            "Microphone PCM byte length must be divisible by 2 for signed "
            "16-bit little-endian samples.",
        )

    sample_count = byte_count // _SIGNED_16_BIT_SAMPLE_WIDTH_BYTES
    if sample_count % channel_count != 0:
        raise InvalidMicrophoneLevelInputError(
            "Microphone PCM sample count must be divisible by channel_count "
            "to form complete frames.",
        )

    frame_count = sample_count // channel_count
    if sample_count == 0:
        return MicrophoneLevelReading(
            start_seconds=start_seconds,
            end_seconds=end_seconds,
            sample_rate_hz=sample_rate_hz,
            channel_count=channel_count,
            frame_count=frame_count,
            sample_count=sample_count,
            peak_amplitude=0,
            normalized_peak_level=0.0,
            normalized_rms_level=0.0,
        )

    peak_amplitude = 0
    sum_squares = 0
    for (sample,) in struct.iter_unpack("<h", pcm_bytes):
        amplitude = abs(sample)
        peak_amplitude = max(peak_amplitude, amplitude)
        sum_squares += sample * sample

    return MicrophoneLevelReading(
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        sample_rate_hz=sample_rate_hz,
        channel_count=channel_count,
        frame_count=frame_count,
        sample_count=sample_count,
        peak_amplitude=peak_amplitude,
        normalized_peak_level=peak_amplitude / _SIGNED_16_BIT_FULL_SCALE,
        normalized_rms_level=math.sqrt(sum_squares / sample_count)
        / _SIGNED_16_BIT_FULL_SCALE,
    )


async def collect_microphone_level_readings(
    source: MicrophoneSource,
) -> list[MicrophoneLevelReading]:
    """Collect ordered metadata-only level readings from a microphone source."""

    readings: list[MicrophoneLevelReading] = []
    async for chunk in source:
        readings.append(measure_microphone_level(chunk))
    return readings


def _required_attr(value: object, names: tuple[str, ...], label: str) -> Any:
    for name in names:
        try:
            return getattr(value, name)
        except AttributeError:
            continue
    raise InvalidMicrophoneLevelInputError(
        f"Microphone PCM chunk is missing required {label}.",
    )


def _required_seconds(
    chunk: object,
    names: tuple[str, ...],
    label: str,
) -> float:
    value = _required_attr(chunk, names, label)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise InvalidMicrophoneLevelInputError(
            f"Microphone PCM chunk {label} must be a numeric second value.",
        )
    seconds = float(value)
    if not math.isfinite(seconds) or seconds < 0.0:
        raise InvalidMicrophoneLevelInputError(
            f"Microphone PCM chunk {label} must be finite and non-negative.",
        )
    return seconds


def _required_positive_int(
    chunk: object,
    names: tuple[str, ...],
    label: str,
) -> int:
    value = _required_attr(chunk, names, label)
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidMicrophoneLevelInputError(
            f"Microphone PCM chunk {label} must be a positive integer.",
        )
    if value <= 0:
        raise InvalidMicrophoneLevelInputError(
            f"Microphone PCM chunk {label} must be greater than zero.",
        )
    return value


def _validate_sample_width(chunk: object) -> None:
    sample_width_bytes = getattr(
        chunk,
        "sample_width_bytes",
        _SIGNED_16_BIT_SAMPLE_WIDTH_BYTES,
    )
    if (
        isinstance(sample_width_bytes, bool)
        or not isinstance(sample_width_bytes, int)
        or sample_width_bytes != _SIGNED_16_BIT_SAMPLE_WIDTH_BYTES
    ):
        raise InvalidMicrophoneLevelInputError(
            "Microphone level readings require signed 16-bit PCM with "
            "sample_width_bytes=2.",
        )


def _required_pcm_bytes(chunk: object) -> bytes | bytearray | memoryview:
    value = _required_attr(chunk, ("pcm_bytes", "pcm"), "PCM bytes")
    if not isinstance(value, bytes | bytearray | memoryview):
        raise InvalidMicrophoneLevelInputError(
            "Microphone PCM chunk data must be bytes-like.",
        )
    return value
