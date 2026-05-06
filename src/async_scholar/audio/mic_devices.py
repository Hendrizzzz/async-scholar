"""Import-safe microphone device-listing boundary contracts.

This module intentionally defines metadata and provider contracts only. It does
not enumerate devices, request microphone permission, start capture, record
audio, run VAD/STT, or persist audio.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class MicrophoneDeviceMetadata:
    """Metadata for one microphone input device supplied by a provider."""

    device_id: str
    display_name: str
    input_channel_count: int
    default_sample_rate_hz: int
    is_default: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "device_id",
            _validate_non_blank_string(self.device_id, "device_id"),
        )
        object.__setattr__(
            self,
            "display_name",
            _validate_non_blank_string(self.display_name, "display_name"),
        )
        _validate_positive_int(self.input_channel_count, "input_channel_count")
        _validate_positive_int(self.default_sample_rate_hz, "default_sample_rate_hz")
        if not isinstance(self.is_default, bool):
            raise TypeError("is_default must be a boolean")


@runtime_checkable
class MicrophoneDeviceProvider(Protocol):
    """Boundary for providers that list microphone device metadata."""

    def list_microphone_devices(self) -> Sequence[MicrophoneDeviceMetadata]:
        """Return a deterministic metadata listing without touching capture."""


@dataclass(frozen=True)
class StaticMicrophoneDeviceProvider:
    """Deterministic in-memory microphone device provider for tests."""

    devices: Sequence[MicrophoneDeviceMetadata] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "devices",
            validate_microphone_device_listing(self.devices),
        )

    def list_microphone_devices(self) -> tuple[MicrophoneDeviceMetadata, ...]:
        return self.devices


def validate_microphone_device_listing(
    devices: Sequence[MicrophoneDeviceMetadata],
) -> tuple[MicrophoneDeviceMetadata, ...]:
    """Validate and freeze a microphone device listing."""

    if isinstance(devices, str | bytes | bytearray | memoryview):
        raise TypeError("devices must be a sequence of MicrophoneDeviceMetadata")
    if not isinstance(devices, Sequence):
        raise TypeError("devices must be a sequence of MicrophoneDeviceMetadata")

    device_tuple = tuple(devices)
    seen_device_ids: set[str] = set()
    for index, device in enumerate(device_tuple):
        if not isinstance(device, MicrophoneDeviceMetadata):
            raise TypeError(f"devices[{index}] must be MicrophoneDeviceMetadata")
        if device.device_id in seen_device_ids:
            raise ValueError(
                f"duplicate device_id in microphone listing: {device.device_id}",
            )
        seen_device_ids.add(device.device_id)
    return device_tuple


def _validate_non_blank_string(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    normalized_value = value.strip()
    if not normalized_value:
        raise ValueError(f"{field_name} must be non-blank")
    return normalized_value


def _validate_positive_int(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


__all__ = [
    "MicrophoneDeviceMetadata",
    "MicrophoneDeviceProvider",
    "StaticMicrophoneDeviceProvider",
    "validate_microphone_device_listing",
]
