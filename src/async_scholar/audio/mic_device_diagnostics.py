"""Import-safe microphone device diagnostic summaries.

This module consumes microphone device-listing providers and returns aggregate
metadata only. It does not enumerate hardware, request microphone permission,
start capture, record audio, run VAD/STT, or persist audio.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from async_scholar.audio.mic_devices import (
    MicrophoneDeviceProvider,
    validate_microphone_device_listing,
)


@dataclass(frozen=True)
class MicrophoneDeviceDiagnosticSummary:
    """Privacy-safe aggregate metadata for a microphone device listing."""

    device_count: int
    default_device_count: int
    has_default_device: bool
    max_input_channel_count: int
    default_sample_rates_hz: tuple[int, ...]

    def __post_init__(self) -> None:
        _validate_non_negative_int(self.device_count, "device_count")
        _validate_non_negative_int(
            self.default_device_count,
            "default_device_count",
        )
        if self.default_device_count > self.device_count:
            raise ValueError(
                "default_device_count must be less than or equal to device_count",
            )
        if not isinstance(self.has_default_device, bool):
            raise TypeError("has_default_device must be a boolean")
        if self.has_default_device != (self.default_device_count > 0):
            raise ValueError(
                "has_default_device must match whether default_device_count "
                "is positive",
            )
        _validate_non_negative_int(
            self.max_input_channel_count,
            "max_input_channel_count",
        )
        if self.device_count == 0 and self.max_input_channel_count != 0:
            raise ValueError(
                "max_input_channel_count must be 0 when device_count is 0",
            )
        object.__setattr__(
            self,
            "default_sample_rates_hz",
            _validate_default_sample_rates(self.default_sample_rates_hz),
        )


def collect_microphone_device_diagnostics(
    provider: MicrophoneDeviceProvider,
) -> MicrophoneDeviceDiagnosticSummary:
    """Collect safe aggregate metadata from a microphone device provider."""

    devices = validate_microphone_device_listing(provider.list_microphone_devices())
    default_device_count = sum(1 for device in devices if device.is_default)

    return MicrophoneDeviceDiagnosticSummary(
        device_count=len(devices),
        default_device_count=default_device_count,
        has_default_device=default_device_count > 0,
        max_input_channel_count=max(
            (device.input_channel_count for device in devices),
            default=0,
        ),
        default_sample_rates_hz=tuple(
            sorted({device.default_sample_rate_hz for device in devices}),
        ),
    )


def _validate_default_sample_rates(
    values: Sequence[int],
) -> tuple[int, ...]:
    if isinstance(values, str | bytes | bytearray | memoryview):
        raise TypeError("default_sample_rates_hz must be a sequence of integers")
    if not isinstance(values, Sequence):
        raise TypeError("default_sample_rates_hz must be a sequence of integers")

    value_tuple = tuple(values)
    previous_value: int | None = None
    seen_values: set[int] = set()
    for index, value in enumerate(value_tuple):
        _validate_positive_int(value, f"default_sample_rates_hz[{index}]")
        if value in seen_values:
            raise ValueError("default_sample_rates_hz must contain distinct values")
        if previous_value is not None and value < previous_value:
            raise ValueError("default_sample_rates_hz must be sorted")
        seen_values.add(value)
        previous_value = value
    return value_tuple


def _validate_non_negative_int(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _validate_positive_int(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


__all__ = [
    "MicrophoneDeviceDiagnosticSummary",
    "collect_microphone_device_diagnostics",
]
