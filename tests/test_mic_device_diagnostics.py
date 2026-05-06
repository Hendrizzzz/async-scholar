from __future__ import annotations

import runpy
import subprocess
import sys

import pytest

from async_scholar.audio import (
    MicrophoneDeviceDiagnosticSummary,
    MicrophoneDeviceMetadata,
    StaticMicrophoneDeviceProvider,
    collect_microphone_device_diagnostics,
)


def test_microphone_device_diagnostics_support_empty_listings() -> None:
    summary = collect_microphone_device_diagnostics(
        StaticMicrophoneDeviceProvider(),
    )

    assert summary == MicrophoneDeviceDiagnosticSummary(
        device_count=0,
        default_device_count=0,
        has_default_device=False,
        max_input_channel_count=0,
        default_sample_rates_hz=(),
    )


def test_microphone_device_diagnostics_summarize_single_default_device() -> None:
    provider = StaticMicrophoneDeviceProvider(
        [
            MicrophoneDeviceMetadata(
                device_id="primary-secret-id",
                display_name="Primary private microphone",
                input_channel_count=2,
                default_sample_rate_hz=48_000,
                is_default=True,
            ),
        ],
    )

    summary = collect_microphone_device_diagnostics(provider)

    assert summary.device_count == 1
    assert summary.default_device_count == 1
    assert summary.has_default_device is True
    assert summary.max_input_channel_count == 2
    assert summary.default_sample_rates_hz == (48_000,)


def test_microphone_device_diagnostics_summarize_multiple_devices() -> None:
    provider = StaticMicrophoneDeviceProvider(
        [
            MicrophoneDeviceMetadata(
                device_id="built-in",
                display_name="Built-in microphone",
                input_channel_count=1,
                default_sample_rate_hz=16_000,
            ),
            MicrophoneDeviceMetadata(
                device_id="usb",
                display_name="USB microphone",
                input_channel_count=2,
                default_sample_rate_hz=48_000,
                is_default=True,
            ),
            MicrophoneDeviceMetadata(
                device_id="virtual",
                display_name="Virtual microphone",
                input_channel_count=8,
                default_sample_rate_hz=16_000,
            ),
        ],
    )

    summary = collect_microphone_device_diagnostics(provider)

    assert summary == MicrophoneDeviceDiagnosticSummary(
        device_count=3,
        default_device_count=1,
        has_default_device=True,
        max_input_channel_count=8,
        default_sample_rates_hz=(16_000, 48_000),
    )


def test_microphone_device_diagnostics_summarize_no_default_device() -> None:
    provider = StaticMicrophoneDeviceProvider(
        [
            MicrophoneDeviceMetadata(
                device_id="one",
                display_name="One",
                input_channel_count=1,
                default_sample_rate_hz=44_100,
            ),
            MicrophoneDeviceMetadata(
                device_id="two",
                display_name="Two",
                input_channel_count=2,
                default_sample_rate_hz=48_000,
            ),
        ],
    )

    summary = collect_microphone_device_diagnostics(provider)

    assert summary.device_count == 2
    assert summary.default_device_count == 0
    assert summary.has_default_device is False
    assert summary.max_input_channel_count == 2
    assert summary.default_sample_rates_hz == (44_100, 48_000)


def test_microphone_device_diagnostics_allow_multiple_defaults_as_metadata() -> None:
    provider = StaticMicrophoneDeviceProvider(
        [
            MicrophoneDeviceMetadata(
                device_id="system-default",
                display_name="System default",
                input_channel_count=1,
                default_sample_rate_hz=16_000,
                is_default=True,
            ),
            MicrophoneDeviceMetadata(
                device_id="app-default",
                display_name="App default",
                input_channel_count=2,
                default_sample_rate_hz=48_000,
                is_default=True,
            ),
        ],
    )

    summary = collect_microphone_device_diagnostics(provider)

    assert summary.default_device_count == 2
    assert summary.has_default_device is True
    assert summary.max_input_channel_count == 2
    assert summary.default_sample_rates_hz == (16_000, 48_000)


def test_microphone_device_diagnostics_validate_provider_output() -> None:
    provider = object.__new__(StaticMicrophoneDeviceProvider)
    object.__setattr__(provider, "devices", ("not device metadata",))

    with pytest.raises(
        TypeError,
        match=r"devices\[0\] must be MicrophoneDeviceMetadata",
    ):
        collect_microphone_device_diagnostics(provider)


def test_microphone_device_diagnostics_repr_is_privacy_safe() -> None:
    provider = StaticMicrophoneDeviceProvider(
        [
            MicrophoneDeviceMetadata(
                device_id="private-device-id-123",
                display_name="Private Owner Microphone",
                input_channel_count=2,
                default_sample_rate_hz=48_000,
                is_default=True,
            ),
        ],
    )

    summary = collect_microphone_device_diagnostics(provider)
    summary_repr = repr(summary)

    assert "private-device-id-123" not in summary_repr
    assert "Private Owner Microphone" not in summary_repr
    assert "MicrophoneDeviceMetadata" not in summary_repr
    assert "provider" not in summary.__dict__
    assert "devices" not in summary.__dict__


def test_microphone_device_diagnostic_imports_do_not_load_hardware_or_models() -> None:
    code = """
import sys

import async_scholar.audio
import async_scholar.audio.mic_device_diagnostics

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


def test_cli_help_stays_import_safe_for_device_diagnostic_boundary() -> None:
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
