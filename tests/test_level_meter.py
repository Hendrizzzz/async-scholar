from __future__ import annotations

import asyncio
import importlib
import inspect
import math
import struct
from dataclasses import dataclass, fields

import pytest

from async_scholar.audio import (
    DeterministicFakeMicrophoneSource,
    MicrophonePcmChunk,
)
from async_scholar.audio.level_meter import (
    InvalidMicrophoneLevelInputError,
    MicrophoneLevelReading,
    collect_microphone_level_readings,
    measure_microphone_level,
)


def test_level_meter_module_import_is_safe_and_exported() -> None:
    module = importlib.import_module("async_scholar.audio.level_meter")
    audio = importlib.import_module("async_scholar.audio")

    assert module.MicrophoneLevelReading is MicrophoneLevelReading
    assert audio.MicrophoneLevelReading is MicrophoneLevelReading
    assert audio.measure_microphone_level is measure_microphone_level
    assert audio.collect_microphone_level_readings is collect_microphone_level_readings


def test_silence_returns_zero_levels_without_retaining_pcm() -> None:
    chunk = _chunk(_pcm16(0, 0, 0, 0), start_seconds=1.0, end_seconds=1.25)

    reading = measure_microphone_level(chunk)

    assert reading == MicrophoneLevelReading(
        start_seconds=1.0,
        end_seconds=1.25,
        sample_rate_hz=16_000,
        channel_count=1,
        frame_count=4,
        sample_count=4,
        peak_amplitude=0,
        normalized_peak_level=0.0,
        normalized_rms_level=0.0,
    )
    _assert_privacy_safe(reading)


def test_positive_and_negative_samples_set_peak_and_rms() -> None:
    chunk = _chunk(_pcm16(0, 16_384, -16_384))

    reading = measure_microphone_level(chunk)

    assert reading.peak_amplitude == 16_384
    assert reading.normalized_peak_level == pytest.approx(0.5)
    assert reading.normalized_rms_level == pytest.approx(math.sqrt(2 / 3) * 0.5)


def test_full_scale_negative_sample_normalizes_to_one() -> None:
    chunk = _chunk(_pcm16(-32_768))

    reading = measure_microphone_level(chunk)

    assert reading.peak_amplitude == 32_768
    assert reading.normalized_peak_level == pytest.approx(1.0)
    assert reading.normalized_rms_level == pytest.approx(1.0)


def test_empty_pcm_chunk_returns_zero_levels() -> None:
    chunk = _chunk(b"", start_seconds=2.0, end_seconds=2.0)

    reading = measure_microphone_level(chunk)

    assert reading.frame_count == 0
    assert reading.sample_count == 0
    assert reading.peak_amplitude == 0
    assert reading.normalized_peak_level == 0.0
    assert reading.normalized_rms_level == 0.0


def test_invalid_pcm_byte_length_raises_clear_error() -> None:
    chunk = _chunk(b"\x00")

    with pytest.raises(InvalidMicrophoneLevelInputError, match="16-bit"):
        measure_microphone_level(chunk)


def test_invalid_sample_width_assumption_raises_clear_error() -> None:
    chunk = _UnsupportedSampleWidthChunk(
        start_seconds=0.0,
        end_seconds=0.1,
        sample_rate_hz=16_000,
        channel_count=1,
        sample_width_bytes=1,
        pcm_bytes=b"\x00\x00",
    )

    with pytest.raises(InvalidMicrophoneLevelInputError, match="sample_width_bytes=2"):
        measure_microphone_level(chunk)  # type: ignore[arg-type]


def test_multichannel_pcm_counts_complete_frames_and_rms() -> None:
    chunk = _chunk(
        _pcm16(1_000, -1_000, 2_000, -2_000),
        channel_count=2,
    )

    reading = measure_microphone_level(chunk)

    assert reading.channel_count == 2
    assert reading.sample_count == 4
    assert reading.frame_count == 2
    assert reading.peak_amplitude == 2_000
    expected_rms = math.sqrt((1_000**2 + 1_000**2 + 2_000**2 + 2_000**2) / 4)
    assert reading.normalized_rms_level == pytest.approx(expected_rms / 32_768)


def test_incompatible_channel_framing_raises_clear_error() -> None:
    chunk = _chunk(_pcm16(1, 2, 3), channel_count=2)

    with pytest.raises(InvalidMicrophoneLevelInputError, match="complete frames"):
        measure_microphone_level(chunk)


def test_collects_fake_source_readings_in_chunk_order() -> None:
    source = _fake_source(
        [
            _pcm16(1_000),
            _pcm16(2_000),
            _pcm16(-32_768),
        ],
    )

    readings = asyncio.run(collect_microphone_level_readings(source))

    assert [reading.start_seconds for reading in readings] == sorted(
        reading.start_seconds for reading in readings
    )
    assert [reading.peak_amplitude for reading in readings] == [1_000, 2_000, 32_768]


@dataclass(frozen=True)
class _UnsupportedSampleWidthChunk:
    start_seconds: float
    end_seconds: float
    sample_rate_hz: int
    channel_count: int
    sample_width_bytes: int
    pcm_bytes: bytes


def _pcm16(*samples: int) -> bytes:
    if not samples:
        return b""
    return struct.pack(f"<{len(samples)}h", *samples)


def _chunk(
    pcm_bytes: bytes,
    *,
    start_seconds: float = 0.0,
    end_seconds: float = 0.25,
    sample_rate_hz: int = 16_000,
    channel_count: int = 1,
) -> MicrophonePcmChunk:
    signature = inspect.signature(MicrophonePcmChunk)
    values = {
        "start_seconds": start_seconds,
        "end_seconds": end_seconds,
        "sample_rate_hz": sample_rate_hz,
        "channel_count": channel_count,
        "pcm_bytes": pcm_bytes,
        "pcm": pcm_bytes,
    }
    kwargs = {}
    for name, parameter in signature.parameters.items():
        if name in values:
            kwargs[name] = values[name]
        elif parameter.default is inspect.Parameter.empty:
            raise AssertionError(f"Unhandled MicrophonePcmChunk parameter: {name}")
    return MicrophonePcmChunk(**kwargs)


def _fake_source(
    pcm_payloads: list[bytes],
) -> DeterministicFakeMicrophoneSource:
    try:
        return DeterministicFakeMicrophoneSource(pcm_payloads=pcm_payloads)
    except TypeError:
        return DeterministicFakeMicrophoneSource(pcm_payloads)


def _assert_privacy_safe(reading: MicrophoneLevelReading) -> None:
    field_names = {field.name for field in fields(reading)}
    forbidden_field_fragments = {
        "audio",
        "chunk",
        "device",
        "file",
        "media",
        "path",
        "pcm",
        "recording",
        "secret",
        "source",
        "text",
        "transcript",
    }
    assert not any(
        fragment in field_name.lower()
        for fragment in forbidden_field_fragments
        for field_name in field_names
    )
    reading_repr = repr(reading).lower()
    assert "b'" not in reading_repr
    assert "pcm" not in reading_repr
    assert "source" not in reading_repr
