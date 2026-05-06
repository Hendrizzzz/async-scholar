from __future__ import annotations

import importlib
import math
from dataclasses import fields

import pytest

from async_scholar.audio import (
    DEFAULT_MIC_SIGNAL_CLIPPING_THRESHOLD,
    DEFAULT_MIC_SIGNAL_DIAGNOSTIC_CONFIG,
    DEFAULT_MIC_SIGNAL_SILENCE_THRESHOLD,
    InvalidMicrophoneSignalDiagnosticConfigError,
    InvalidMicrophoneSignalReadingError,
    MicrophoneSignalDiagnosticConfig,
    MicrophoneSignalDiagnosticSummary,
    diagnose_microphone_signal,
)
from async_scholar.audio.level_meter import MicrophoneLevelReading


def test_signal_diagnostic_module_import_is_safe_and_exported() -> None:
    module = importlib.import_module("async_scholar.audio.mic_signal_diagnostics")
    audio = importlib.import_module("async_scholar.audio")

    assert "SoundDeviceMicrophoneSource" not in module.__dict__
    assert "MicrophonePcmChunk" not in module.__dict__
    assert module.MicrophoneSignalDiagnosticConfig is MicrophoneSignalDiagnosticConfig
    assert module.MicrophoneSignalDiagnosticSummary is MicrophoneSignalDiagnosticSummary
    assert module.diagnose_microphone_signal is diagnose_microphone_signal
    assert audio.MicrophoneSignalDiagnosticConfig is MicrophoneSignalDiagnosticConfig
    assert audio.MicrophoneSignalDiagnosticSummary is MicrophoneSignalDiagnosticSummary
    assert audio.diagnose_microphone_signal is diagnose_microphone_signal
    assert MicrophoneSignalDiagnosticConfig() == DEFAULT_MIC_SIGNAL_DIAGNOSTIC_CONFIG
    assert pytest.approx(0.01) == DEFAULT_MIC_SIGNAL_SILENCE_THRESHOLD
    assert pytest.approx(0.98) == DEFAULT_MIC_SIGNAL_CLIPPING_THRESHOLD


def test_empty_readings_return_safe_no_data_summary() -> None:
    summary = diagnose_microphone_signal([])

    assert summary == MicrophoneSignalDiagnosticSummary(
        reading_count=0,
        silent_reading_count=0,
        clipped_reading_count=0,
        peak_level=0.0,
        average_rms_level=0.0,
        silence_detected=False,
        clipping_detected=False,
    )


def test_silence_detected_from_low_rms_readings() -> None:
    summary = diagnose_microphone_signal(
        [
            _reading(normalized_peak_level=0.0, normalized_rms_level=0.0),
            _reading(normalized_peak_level=0.015, normalized_rms_level=0.01),
        ]
    )

    assert summary.reading_count == 2
    assert summary.silent_reading_count == 2
    assert summary.clipped_reading_count == 0
    assert summary.peak_level == pytest.approx(0.015)
    assert summary.average_rms_level == pytest.approx(0.005)
    assert summary.silence_detected is True
    assert summary.clipping_detected is False


def test_non_silent_audio_has_no_signal_health_flags() -> None:
    summary = diagnose_microphone_signal(
        [
            _reading(normalized_peak_level=0.2, normalized_rms_level=0.05),
            _reading(normalized_peak_level=0.4, normalized_rms_level=0.1),
        ]
    )

    assert summary.reading_count == 2
    assert summary.silent_reading_count == 0
    assert summary.clipped_reading_count == 0
    assert summary.peak_level == pytest.approx(0.4)
    assert summary.average_rms_level == pytest.approx(0.075)
    assert summary.silence_detected is False
    assert summary.clipping_detected is False


def test_clipping_detected_from_high_peak_reading() -> None:
    summary = diagnose_microphone_signal(
        [
            _reading(normalized_peak_level=0.97, normalized_rms_level=0.2),
            _reading(normalized_peak_level=0.98, normalized_rms_level=0.35),
        ]
    )

    assert summary.reading_count == 2
    assert summary.silent_reading_count == 0
    assert summary.clipped_reading_count == 1
    assert summary.peak_level == pytest.approx(0.98)
    assert summary.average_rms_level == pytest.approx(0.275)
    assert summary.silence_detected is False
    assert summary.clipping_detected is True


def test_mixed_readings_report_silence_and_clipping_counts() -> None:
    config = MicrophoneSignalDiagnosticConfig(
        silence_threshold=0.02,
        clipping_threshold=0.9,
    )

    summary = diagnose_microphone_signal(
        [
            _reading(normalized_peak_level=0.01, normalized_rms_level=0.0),
            _reading(normalized_peak_level=0.5, normalized_rms_level=0.1),
            _reading(normalized_peak_level=1.0, normalized_rms_level=0.4),
        ],
        config=config,
    )

    assert summary.reading_count == 3
    assert summary.silent_reading_count == 1
    assert summary.clipped_reading_count == 1
    assert summary.peak_level == pytest.approx(1.0)
    assert summary.average_rms_level == pytest.approx(0.5 / 3)
    assert summary.silence_detected is True
    assert summary.clipping_detected is True


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("silence_threshold", math.nan),
        ("silence_threshold", math.inf),
        ("silence_threshold", -0.01),
        ("silence_threshold", 1.01),
        ("silence_threshold", True),
        ("clipping_threshold", math.nan),
        ("clipping_threshold", math.inf),
        ("clipping_threshold", -0.01),
        ("clipping_threshold", 1.01),
        ("clipping_threshold", "loud"),
    ],
)
def test_invalid_thresholds_raise_clear_exceptions(
    field_name: str,
    value: object,
) -> None:
    kwargs: dict[str, object] = {
        "silence_threshold": DEFAULT_MIC_SIGNAL_SILENCE_THRESHOLD,
        "clipping_threshold": DEFAULT_MIC_SIGNAL_CLIPPING_THRESHOLD,
        field_name: value,
    }

    with pytest.raises(
        InvalidMicrophoneSignalDiagnosticConfigError,
        match=field_name,
    ):
        MicrophoneSignalDiagnosticConfig(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("normalized_peak_level", math.nan),
        ("normalized_peak_level", math.inf),
        ("normalized_peak_level", -0.01),
        ("normalized_peak_level", 1.01),
        ("normalized_peak_level", True),
        ("normalized_rms_level", math.nan),
        ("normalized_rms_level", math.inf),
        ("normalized_rms_level", -0.01),
        ("normalized_rms_level", 1.01),
        ("normalized_rms_level", "quiet"),
    ],
)
def test_invalid_reading_values_raise_clear_exceptions(
    field_name: str,
    value: object,
) -> None:
    reading = _reading(**{field_name: value})

    with pytest.raises(
        InvalidMicrophoneSignalReadingError,
        match=rf"reading\[0\].{field_name}",
    ):
        diagnose_microphone_signal([reading])


def test_summary_fields_and_repr_are_privacy_safe() -> None:
    summary = diagnose_microphone_signal(
        [
            _reading(normalized_peak_level=0.9, normalized_rms_level=0.2),
        ]
    )

    assert {field.name for field in fields(summary)} == {
        "reading_count",
        "silent_reading_count",
        "clipped_reading_count",
        "peak_level",
        "average_rms_level",
        "silence_detected",
        "clipping_detected",
    }
    safe_text = repr(summary).lower()
    forbidden_fragments = {
        "b'",
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
        "microphonelevelreading",
    }
    assert not any(fragment in safe_text for fragment in forbidden_fragments)


def _reading(
    *,
    start_seconds: float = 0.0,
    end_seconds: float = 0.25,
    sample_rate_hz: int = 16_000,
    channel_count: int = 1,
    frame_count: int = 4_000,
    sample_count: int = 4_000,
    peak_amplitude: int = 0,
    normalized_peak_level: object = 0.0,
    normalized_rms_level: object = 0.0,
) -> MicrophoneLevelReading:
    return MicrophoneLevelReading(
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        sample_rate_hz=sample_rate_hz,
        channel_count=channel_count,
        frame_count=frame_count,
        sample_count=sample_count,
        peak_amplitude=peak_amplitude,
        normalized_peak_level=normalized_peak_level,  # type: ignore[arg-type]
        normalized_rms_level=normalized_rms_level,  # type: ignore[arg-type]
    )
