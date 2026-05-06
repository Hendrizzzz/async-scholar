from __future__ import annotations

import runpy
import subprocess
import sys

import pytest

from async_scholar.audio import (
    MicrophoneDeviceMetadata,
    MicrophoneDeviceProvider,
    StaticMicrophoneDeviceProvider,
    validate_microphone_device_listing,
)


def test_microphone_device_metadata_keeps_valid_values() -> None:
    device = MicrophoneDeviceMetadata(
        device_id=" laptop-array ",
        display_name=" Laptop microphone ",
        input_channel_count=2,
        default_sample_rate_hz=48_000,
        is_default=True,
    )

    assert device.device_id == "laptop-array"
    assert device.display_name == "Laptop microphone"
    assert device.input_channel_count == 2
    assert device.default_sample_rate_hz == 48_000
    assert device.is_default is True


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"device_id": ""}, "device_id must be non-blank"),
        ({"device_id": "   "}, "device_id must be non-blank"),
        ({"display_name": ""}, "display_name must be non-blank"),
        ({"display_name": "   "}, "display_name must be non-blank"),
        ({"input_channel_count": 0}, "input_channel_count must be positive"),
        ({"input_channel_count": -1}, "input_channel_count must be positive"),
        ({"default_sample_rate_hz": 0}, "default_sample_rate_hz must be positive"),
        (
            {"default_sample_rate_hz": -16_000},
            "default_sample_rate_hz must be positive",
        ),
    ],
)
def test_microphone_device_metadata_rejects_invalid_values(
    kwargs: dict[str, object],
    match: str,
) -> None:
    valid_kwargs: dict[str, object] = {
        "device_id": "mic-1",
        "display_name": "Laptop microphone",
        "input_channel_count": 1,
        "default_sample_rate_hz": 16_000,
    }
    valid_kwargs.update(kwargs)

    with pytest.raises(ValueError, match=match):
        MicrophoneDeviceMetadata(**valid_kwargs)


def test_microphone_device_listing_allows_empty_lists() -> None:
    provider = StaticMicrophoneDeviceProvider()

    assert validate_microphone_device_listing([]) == ()
    assert provider.list_microphone_devices() == ()


def test_microphone_device_listing_rejects_duplicate_device_ids() -> None:
    first = MicrophoneDeviceMetadata(
        device_id="same-device",
        display_name="First microphone",
        input_channel_count=1,
        default_sample_rate_hz=16_000,
    )
    second = MicrophoneDeviceMetadata(
        device_id="same-device",
        display_name="Second microphone",
        input_channel_count=2,
        default_sample_rate_hz=48_000,
    )

    with pytest.raises(ValueError, match="duplicate device_id"):
        validate_microphone_device_listing([first, second])
    with pytest.raises(ValueError, match="duplicate device_id"):
        StaticMicrophoneDeviceProvider([first, second])


def test_static_microphone_device_provider_returns_deterministic_listing() -> None:
    built_in = MicrophoneDeviceMetadata(
        device_id="built-in",
        display_name="Built-in microphone",
        input_channel_count=1,
        default_sample_rate_hz=16_000,
        is_default=True,
    )
    usb = MicrophoneDeviceMetadata(
        device_id="usb-audio",
        display_name="USB microphone",
        input_channel_count=2,
        default_sample_rate_hz=48_000,
    )
    provider: MicrophoneDeviceProvider = StaticMicrophoneDeviceProvider(
        [built_in, usb],
    )

    assert isinstance(provider, MicrophoneDeviceProvider)
    assert provider.list_microphone_devices() == (built_in, usb)
    assert provider.list_microphone_devices() is provider.list_microphone_devices()


def test_microphone_device_metadata_marks_default_device_metadata() -> None:
    default_device = MicrophoneDeviceMetadata(
        device_id="default",
        display_name="System default microphone",
        input_channel_count=1,
        default_sample_rate_hz=16_000,
        is_default=True,
    )
    alternate_device = MicrophoneDeviceMetadata(
        device_id="alternate",
        display_name="Alternate microphone",
        input_channel_count=2,
        default_sample_rate_hz=48_000,
    )
    provider = StaticMicrophoneDeviceProvider([default_device, alternate_device])

    default_devices = [
        device for device in provider.list_microphone_devices() if device.is_default
    ]

    assert default_devices == [default_device]
    assert alternate_device.is_default is False


def test_audio_device_imports_do_not_load_hardware_or_model_dependencies() -> None:
    code = """
import sys

import async_scholar.audio
import async_scholar.audio.mic_devices

banned = {
    "faster_whisper",
    "pyaudio",
    "silero_vad",
    "soundcard",
    "sounddevice",
    "torch",
    "torchaudio",
}
loaded = sorted(name for name in banned if name in sys.modules)
if loaded:
    raise SystemExit(f"unexpected eager imports: {loaded}")
"""

    subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )


def test_cli_help_stays_import_safe_for_device_listing_boundary() -> None:
    banned = {
        "faster_whisper",
        "pyaudio",
        "silero_vad",
        "soundcard",
        "sounddevice",
        "torch",
        "torchaudio",
    }

    try:
        sys.argv = ["async_scholar", "--help"]
        runpy.run_module("async_scholar", run_name="__main__")
    except SystemExit as exc:
        if exc.code not in (0, None):
            raise

    loaded = sorted(name for name in banned if name in sys.modules)
    assert loaded == []
