"""Pure microphone signal-health diagnostics over level readings."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

from async_scholar.audio.level_meter import MicrophoneLevelReading

DEFAULT_MIC_SIGNAL_CLIPPING_THRESHOLD = 0.98
DEFAULT_MIC_SIGNAL_SILENCE_THRESHOLD = 0.01


class InvalidMicrophoneSignalDiagnosticConfigError(ValueError):
    """Raised when microphone signal diagnostic configuration is invalid."""


class InvalidMicrophoneSignalReadingError(ValueError):
    """Raised when a microphone level reading has invalid normalized values."""


@dataclass(frozen=True)
class MicrophoneSignalDiagnosticConfig:
    """Thresholds for scalar microphone signal diagnostics."""

    silence_threshold: float = DEFAULT_MIC_SIGNAL_SILENCE_THRESHOLD
    clipping_threshold: float = DEFAULT_MIC_SIGNAL_CLIPPING_THRESHOLD

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "silence_threshold",
            _validate_normalized_config_value(
                "silence_threshold",
                self.silence_threshold,
            ),
        )
        object.__setattr__(
            self,
            "clipping_threshold",
            _validate_normalized_config_value(
                "clipping_threshold",
                self.clipping_threshold,
            ),
        )


@dataclass(frozen=True)
class MicrophoneSignalDiagnosticSummary:
    """Privacy-safe scalar summary of microphone signal health."""

    reading_count: int
    silent_reading_count: int
    clipped_reading_count: int
    peak_level: float
    average_rms_level: float
    silence_detected: bool
    clipping_detected: bool


def diagnose_microphone_signal(
    readings: Iterable[MicrophoneLevelReading],
    config: MicrophoneSignalDiagnosticConfig | None = None,
) -> MicrophoneSignalDiagnosticSummary:
    """Summarize silence and clipping from scalar microphone level readings."""

    effective_config = config or DEFAULT_MIC_SIGNAL_DIAGNOSTIC_CONFIG
    reading_count = 0
    silent_reading_count = 0
    clipped_reading_count = 0
    peak_level = 0.0
    rms_level_sum = 0.0

    for index, reading in enumerate(readings):
        normalized_peak_level = _validate_reading_level(
            reading,
            index=index,
            field_name="normalized_peak_level",
        )
        normalized_rms_level = _validate_reading_level(
            reading,
            index=index,
            field_name="normalized_rms_level",
        )

        reading_count += 1
        peak_level = max(peak_level, normalized_peak_level)
        rms_level_sum += normalized_rms_level
        if normalized_rms_level <= effective_config.silence_threshold:
            silent_reading_count += 1
        if normalized_peak_level >= effective_config.clipping_threshold:
            clipped_reading_count += 1

    average_rms_level = rms_level_sum / reading_count if reading_count else 0.0
    return MicrophoneSignalDiagnosticSummary(
        reading_count=reading_count,
        silent_reading_count=silent_reading_count,
        clipped_reading_count=clipped_reading_count,
        peak_level=peak_level,
        average_rms_level=average_rms_level,
        silence_detected=silent_reading_count > 0,
        clipping_detected=clipped_reading_count > 0,
    )


def _validate_reading_level(
    reading: MicrophoneLevelReading,
    *,
    index: int,
    field_name: str,
) -> float:
    try:
        value = getattr(reading, field_name)
    except AttributeError as exc:
        raise InvalidMicrophoneSignalReadingError(
            f"reading[{index}].{field_name} is required"
        ) from exc
    return _validate_normalized_value(
        value,
        name=f"reading[{index}].{field_name}",
        error_type=InvalidMicrophoneSignalReadingError,
    )


def _validate_normalized_config_value(name: str, value: object) -> float:
    return _validate_normalized_value(
        value,
        name=name,
        error_type=InvalidMicrophoneSignalDiagnosticConfigError,
    )


def _validate_normalized_value(
    value: object,
    *,
    name: str,
    error_type: type[ValueError],
) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise error_type(
            f"{name} must be a finite normalized number between 0.0 and 1.0"
        )
    normalized_value = float(value)
    if not math.isfinite(normalized_value):
        raise error_type(f"{name} must be finite")
    if not 0.0 <= normalized_value <= 1.0:
        raise error_type(f"{name} must be between 0.0 and 1.0")
    return normalized_value


DEFAULT_MIC_SIGNAL_DIAGNOSTIC_CONFIG = MicrophoneSignalDiagnosticConfig()
