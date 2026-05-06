"""Lazy sounddevice microphone device provider.

This module may be imported freely. The real ``sounddevice`` package is only
loaded from the listing path, and this provider only reads device metadata.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib import import_module
from math import isfinite
from numbers import Integral, Real
from typing import Any

from async_scholar.audio.mic_devices import (
    MicrophoneDeviceMetadata,
    validate_microphone_device_listing,
)


class InvalidSoundDeviceMicrophoneMetadataError(ValueError):
    """Raised when sounddevice returns invalid microphone metadata."""


@dataclass(frozen=True)
class SoundDeviceMicrophoneDeviceProvider:
    """Microphone device provider backed by lazy sounddevice metadata listing."""

    def list_microphone_devices(self) -> tuple[MicrophoneDeviceMetadata, ...]:
        sounddevice = import_module("sounddevice")
        raw_devices = _device_listing(sounddevice.query_devices())
        default_input_index = _default_input_device_index(sounddevice)

        devices: list[MicrophoneDeviceMetadata] = []
        for listing_index, raw_device in enumerate(raw_devices):
            device = _device_mapping(raw_device, listing_index)
            sounddevice_index = _sounddevice_index(device, listing_index)
            input_channels = _input_channel_count(device, sounddevice_index)
            if input_channels == 0:
                continue

            devices.append(
                MicrophoneDeviceMetadata(
                    device_id=f"sounddevice:{sounddevice_index}",
                    display_name=_display_name(device, sounddevice_index),
                    input_channel_count=input_channels,
                    default_sample_rate_hz=_default_sample_rate_hz(
                        device,
                        sounddevice_index,
                    ),
                    is_default=sounddevice_index == default_input_index,
                ),
            )

        return validate_microphone_device_listing(devices)


def _device_listing(raw_devices: object) -> tuple[object, ...]:
    if isinstance(raw_devices, Mapping):
        raise InvalidSoundDeviceMicrophoneMetadataError(
            "sounddevice.query_devices() must return a sequence of device metadata",
        )
    if isinstance(raw_devices, str | bytes | bytearray | memoryview):
        raise InvalidSoundDeviceMicrophoneMetadataError(
            "sounddevice.query_devices() must return a sequence of device metadata",
        )
    if not isinstance(raw_devices, Sequence):
        raise InvalidSoundDeviceMicrophoneMetadataError(
            "sounddevice.query_devices() must return a sequence of device metadata",
        )
    return tuple(raw_devices)


def _device_mapping(raw_device: object, listing_index: int) -> Mapping[str, Any]:
    if not isinstance(raw_device, Mapping):
        raise InvalidSoundDeviceMicrophoneMetadataError(
            f"sounddevice device at index {listing_index} must be a metadata mapping",
        )
    return raw_device


def _sounddevice_index(device: Mapping[str, Any], listing_index: int) -> int:
    if "index" not in device:
        return listing_index

    raw_index = device["index"]
    if isinstance(raw_index, bool) or not isinstance(raw_index, Integral):
        raise InvalidSoundDeviceMicrophoneMetadataError(
            f"sounddevice device index at listing index {listing_index} "
            "must be a non-negative integer",
        )
    sounddevice_index = int(raw_index)
    if sounddevice_index < 0:
        raise InvalidSoundDeviceMicrophoneMetadataError(
            f"sounddevice device index at listing index {listing_index} "
            "must be a non-negative integer",
        )
    return sounddevice_index


def _input_channel_count(device: Mapping[str, Any], sounddevice_index: int) -> int:
    raw_channels = _required_field(
        device,
        "max_input_channels",
        sounddevice_index,
    )
    if isinstance(raw_channels, bool) or not isinstance(raw_channels, Integral):
        raise InvalidSoundDeviceMicrophoneMetadataError(
            "sounddevice max_input_channels for device "
            f"{sounddevice_index} must be a non-negative integer",
        )
    input_channels = int(raw_channels)
    if input_channels < 0:
        raise InvalidSoundDeviceMicrophoneMetadataError(
            "sounddevice max_input_channels for device "
            f"{sounddevice_index} must be a non-negative integer",
        )
    return input_channels


def _display_name(device: Mapping[str, Any], sounddevice_index: int) -> str:
    raw_name = _required_field(device, "name", sounddevice_index)
    if not isinstance(raw_name, str):
        raise InvalidSoundDeviceMicrophoneMetadataError(
            f"sounddevice name for device {sounddevice_index} must be a string",
        )
    display_name = raw_name.strip()
    if not display_name:
        raise InvalidSoundDeviceMicrophoneMetadataError(
            f"sounddevice name for device {sounddevice_index} must be non-blank",
        )
    return display_name


def _default_sample_rate_hz(
    device: Mapping[str, Any],
    sounddevice_index: int,
) -> int:
    raw_sample_rate = _required_field(
        device,
        "default_samplerate",
        sounddevice_index,
    )
    if isinstance(raw_sample_rate, bool) or not isinstance(raw_sample_rate, Real):
        raise InvalidSoundDeviceMicrophoneMetadataError(
            "sounddevice default_samplerate for device "
            f"{sounddevice_index} must be a positive whole-number hertz value",
        )

    sample_rate = float(raw_sample_rate)
    if not isfinite(sample_rate) or sample_rate <= 0 or not sample_rate.is_integer():
        raise InvalidSoundDeviceMicrophoneMetadataError(
            "sounddevice default_samplerate for device "
            f"{sounddevice_index} must be a positive whole-number hertz value",
        )
    return int(sample_rate)


def _required_field(
    device: Mapping[str, Any],
    field_name: str,
    sounddevice_index: int,
) -> object:
    if field_name not in device:
        raise InvalidSoundDeviceMicrophoneMetadataError(
            f"sounddevice device {sounddevice_index} is missing {field_name}",
        )
    return device[field_name]


def _default_input_device_index(sounddevice: object) -> int | None:
    default_metadata = getattr(sounddevice, "default", None)
    if default_metadata is None:
        return None

    try:
        default_device = default_metadata.device
    except AttributeError:
        return None

    return _coerce_default_input_device_index(default_device)


def _coerce_default_input_device_index(default_device: object) -> int | None:
    if default_device is None:
        return None

    if isinstance(default_device, bool):
        raise InvalidSoundDeviceMicrophoneMetadataError(
            "sounddevice default input device index must be an integer",
        )
    if isinstance(default_device, Integral):
        return _normalize_default_input_device_index(int(default_device))

    if isinstance(default_device, str | bytes | bytearray | memoryview):
        raise InvalidSoundDeviceMicrophoneMetadataError(
            "sounddevice default.device must be an integer or input/output sequence",
        )
    if isinstance(default_device, Sequence):
        if len(default_device) == 0:
            return None
        raw_input_device = default_device[0]
        if raw_input_device is None:
            return None
        if isinstance(raw_input_device, bool) or not isinstance(
            raw_input_device,
            Integral,
        ):
            raise InvalidSoundDeviceMicrophoneMetadataError(
                "sounddevice default input device index must be an integer",
            )
        return _normalize_default_input_device_index(int(raw_input_device))

    raise InvalidSoundDeviceMicrophoneMetadataError(
        "sounddevice default.device must be an integer or input/output sequence",
    )


def _normalize_default_input_device_index(default_input_index: int) -> int | None:
    if default_input_index < 0:
        return None
    return default_input_index


__all__ = [
    "InvalidSoundDeviceMicrophoneMetadataError",
    "SoundDeviceMicrophoneDeviceProvider",
]
