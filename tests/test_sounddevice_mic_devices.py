from __future__ import annotations

import runpy
import subprocess
import sys
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from async_scholar.audio import (
    InvalidSoundDeviceMicrophoneMetadataError,
    MicrophoneDeviceProvider,
    SoundDeviceMicrophoneDeviceProvider,
)

_MISSING = object()


def test_sounddevice_provider_imports_stay_lazy() -> None:
    code = """
import sys

import async_scholar.audio
import async_scholar.audio.sounddevice_mic_devices
from async_scholar.audio import SoundDeviceMicrophoneDeviceProvider

_provider = SoundDeviceMicrophoneDeviceProvider()
if "sounddevice" in sys.modules:
    raise SystemExit("sounddevice imported before listing")
"""

    subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )


def test_cli_help_stays_lazy_for_sounddevice_provider() -> None:
    try:
        sys.argv = ["async_scholar", "--help"]
        runpy.run_module("async_scholar", run_name="__main__")
    except SystemExit as exc:
        if exc.code not in (0, None):
            raise

    assert "sounddevice" not in sys.modules


def test_sounddevice_provider_queries_only_when_listing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    _install_fake_sounddevice(
        monkeypatch,
        devices=[
            {
                "name": "Laptop microphone",
                "max_input_channels": 2,
                "default_samplerate": 48_000.0,
            },
        ],
        calls=calls,
    )
    provider: MicrophoneDeviceProvider = SoundDeviceMicrophoneDeviceProvider()

    assert calls == []
    assert provider.list_microphone_devices()[0].device_id == "sounddevice:0"
    assert calls == ["query_devices"]


def test_sounddevice_provider_maps_input_devices_and_filters_outputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    _install_fake_sounddevice(
        monkeypatch,
        devices=[
            {
                "name": "Speakers",
                "max_input_channels": 0,
                "default_samplerate": 48_000.0,
            },
            {
                "name": "Laptop microphone",
                "max_input_channels": 2,
                "default_samplerate": 48_000.0,
            },
            {
                "name": "USB microphone",
                "max_input_channels": 1,
                "default_samplerate": 16_000,
            },
        ],
        default_device=(2, 0),
        calls=calls,
    )

    devices = SoundDeviceMicrophoneDeviceProvider().list_microphone_devices()

    assert [device.device_id for device in devices] == [
        "sounddevice:1",
        "sounddevice:2",
    ]
    assert [device.display_name for device in devices] == [
        "Laptop microphone",
        "USB microphone",
    ]
    assert [device.input_channel_count for device in devices] == [2, 1]
    assert [device.default_sample_rate_hz for device in devices] == [48_000, 16_000]
    assert [device.is_default for device in devices] == [False, True]
    assert calls == ["query_devices"]


def test_sounddevice_provider_accepts_record_index_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_sounddevice(
        monkeypatch,
        devices=[
            {
                "index": 7,
                "name": "Interface microphone",
                "max_input_channels": 4,
                "default_samplerate": 44_100.0,
            },
        ],
        default_device=(7, 3),
    )

    devices = SoundDeviceMicrophoneDeviceProvider().list_microphone_devices()

    assert devices[0].device_id == "sounddevice:7"
    assert devices[0].is_default is True


@pytest.mark.parametrize(
    "default_device",
    [
        _MISSING,
        None,
        (-1, 0),
        [None, 0],
        [],
    ],
)
def test_sounddevice_provider_handles_missing_or_no_default_device(
    monkeypatch: pytest.MonkeyPatch,
    default_device: object,
) -> None:
    _install_fake_sounddevice(
        monkeypatch,
        devices=[
            {
                "name": "Only microphone",
                "max_input_channels": 1,
                "default_samplerate": 16_000.0,
            },
        ],
        default_device=default_device,
    )

    devices = SoundDeviceMicrophoneDeviceProvider().list_microphone_devices()

    assert devices[0].is_default is False


@pytest.mark.parametrize(
    ("device", "match"),
    [
        (
            {"name": "Broken microphone", "default_samplerate": 48_000.0},
            "missing max_input_channels",
        ),
        (
            {
                "name": "Broken microphone",
                "max_input_channels": "2",
                "default_samplerate": 48_000.0,
            },
            "max_input_channels.*non-negative integer",
        ),
        (
            {
                "name": "Broken microphone",
                "max_input_channels": -1,
                "default_samplerate": 48_000.0,
            },
            "max_input_channels.*non-negative integer",
        ),
        (
            {
                "max_input_channels": 1,
                "default_samplerate": 48_000.0,
            },
            "missing name",
        ),
        (
            {
                "name": "   ",
                "max_input_channels": 1,
                "default_samplerate": 48_000.0,
            },
            "name.*non-blank",
        ),
        (
            {
                "name": "Broken microphone",
                "max_input_channels": 1,
            },
            "missing default_samplerate",
        ),
        (
            {
                "name": "Broken microphone",
                "max_input_channels": 1,
                "default_samplerate": 0,
            },
            "default_samplerate.*positive whole-number",
        ),
        (
            {
                "name": "Broken microphone",
                "max_input_channels": 1,
                "default_samplerate": 44_100.5,
            },
            "default_samplerate.*positive whole-number",
        ),
    ],
)
def test_sounddevice_provider_rejects_invalid_input_device_metadata(
    monkeypatch: pytest.MonkeyPatch,
    device: dict[str, object],
    match: str,
) -> None:
    _install_fake_sounddevice(monkeypatch, devices=[device])

    with pytest.raises(InvalidSoundDeviceMicrophoneMetadataError, match=match):
        SoundDeviceMicrophoneDeviceProvider().list_microphone_devices()


def test_sounddevice_provider_validates_duplicate_index_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_sounddevice(
        monkeypatch,
        devices=[
            {
                "index": 3,
                "name": "First microphone",
                "max_input_channels": 1,
                "default_samplerate": 16_000.0,
            },
            {
                "index": 3,
                "name": "Second microphone",
                "max_input_channels": 1,
                "default_samplerate": 48_000.0,
            },
        ],
    )

    with pytest.raises(ValueError, match=r"duplicate device_id.*sounddevice:3"):
        SoundDeviceMicrophoneDeviceProvider().list_microphone_devices()


def test_sounddevice_provider_does_not_capture_or_write_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    calls: list[str] = []
    _install_fake_sounddevice(
        monkeypatch,
        devices=[
            {
                "name": "Laptop microphone",
                "max_input_channels": 1,
                "default_samplerate": 48_000.0,
            },
        ],
        calls=calls,
    )

    devices = SoundDeviceMicrophoneDeviceProvider().list_microphone_devices()

    assert len(devices) == 1
    assert calls == ["query_devices"]
    assert list(tmp_path.iterdir()) == []


def _install_fake_sounddevice(
    monkeypatch: pytest.MonkeyPatch,
    *,
    devices: list[dict[str, object]],
    default_device: object = (None, None),
    calls: list[str] | None = None,
) -> ModuleType:
    module = ModuleType("sounddevice")
    call_log = calls if calls is not None else []

    def query_devices() -> list[dict[str, object]]:
        call_log.append("query_devices")
        return devices

    def forbidden_operation(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        call_log.append("forbidden")
        raise AssertionError("sounddevice capture operation was called")

    class ForbiddenInputStream:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            del args, kwargs
            forbidden_operation()

    module.query_devices = query_devices  # type: ignore[attr-defined]
    module.rec = forbidden_operation  # type: ignore[attr-defined]
    module.playrec = forbidden_operation  # type: ignore[attr-defined]
    module.InputStream = ForbiddenInputStream  # type: ignore[attr-defined]
    if default_device is not _MISSING:
        module.default = SimpleNamespace(device=default_device)  # type: ignore[attr-defined]

    monkeypatch.setitem(sys.modules, "sounddevice", module)
    return module
