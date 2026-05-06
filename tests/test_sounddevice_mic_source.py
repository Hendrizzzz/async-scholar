from __future__ import annotations

import asyncio
import runpy
import subprocess
import sys
from types import ModuleType
from typing import Any

import pytest

from async_scholar.audio import MicrophoneCaptureConfig, MicrophoneSource
from async_scholar.audio.sounddevice_mic_source import (
    SoundDeviceMicrophoneCaptureError,
    SoundDeviceMicrophoneSource,
)


def test_sounddevice_source_imports_stay_lazy() -> None:
    code = """
import sys

import async_scholar.audio
import async_scholar.audio.sounddevice_mic_source
from async_scholar.audio import SoundDeviceMicrophoneSource

_source = SoundDeviceMicrophoneSource()
if "sounddevice" in sys.modules:
    raise SystemExit("sounddevice imported before source iteration")
"""

    subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )


def test_cli_help_stays_lazy_for_sounddevice_source() -> None:
    try:
        sys.argv = ["async_scholar", "--help"]
        runpy.run_module("async_scholar", run_name="__main__")
    except SystemExit as exc:
        if exc.code not in (0, None):
            raise

    assert "sounddevice" not in sys.modules


def test_sounddevice_source_opens_stream_only_when_iterated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []
    _install_fake_sounddevice(monkeypatch, reads=[b"\x00\x00"], calls=calls)
    source: MicrophoneSource = SoundDeviceMicrophoneSource(max_chunks=1)

    assert calls == []

    chunks = asyncio.run(_collect_chunks(source))

    assert len(chunks) == 1
    assert calls == [
        (
            "open",
            {
                "samplerate": 16_000,
                "channels": 1,
                "dtype": "int16",
                "blocksize": 16_000,
                "device": None,
            },
        ),
        "start",
        ("read", 16_000),
        "stop",
        "close",
    ]


def test_sounddevice_source_passes_configured_stream_parameters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []
    _install_fake_sounddevice(monkeypatch, reads=[b"\x00" * 8], calls=calls)
    source = SoundDeviceMicrophoneSource(
        config=MicrophoneCaptureConfig(
            sample_rate_hz=8_000,
            channel_count=2,
            chunk_duration_seconds=0.25,
        ),
        device_id="sounddevice:7",
        max_chunks=1,
    )

    chunks = asyncio.run(_collect_chunks(source))

    assert len(chunks) == 1
    assert calls[0] == (
        "open",
        {
            "samplerate": 8_000,
            "channels": 2,
            "dtype": "int16",
            "blocksize": 2_000,
            "device": 7,
        },
    )


def test_sounddevice_source_yields_pcm_chunks_with_deterministic_timing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_sounddevice(
        monkeypatch,
        reads=[(b"\x01\x00\x02\x00", False), (b"\x03\x00\x04\x00", False)],
    )
    source = SoundDeviceMicrophoneSource(
        config=MicrophoneCaptureConfig(
            sample_rate_hz=10,
            channel_count=1,
            chunk_duration_seconds=0.2,
        ),
        max_chunks=2,
    )

    chunks = asyncio.run(_collect_chunks(source))

    assert [chunk.pcm_bytes for chunk in chunks] == [
        b"\x01\x00\x02\x00",
        b"\x03\x00\x04\x00",
    ]
    assert [(chunk.start_seconds, chunk.end_seconds) for chunk in chunks] == [
        (0.0, 0.2),
        (0.2, 0.4),
    ]
    assert [chunk.sample_rate_hz for chunk in chunks] == [10, 10]
    assert [chunk.channel_count for chunk in chunks] == [1, 1]


def test_sounddevice_source_bounded_iteration_closes_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []
    _install_fake_sounddevice(
        monkeypatch,
        reads=[b"\x00\x00", b"\x01\x00", b"\x02\x00"],
        calls=calls,
    )
    source = SoundDeviceMicrophoneSource(max_chunks=2)

    chunks = asyncio.run(_collect_chunks(source))

    assert len(chunks) == 2
    assert calls.count(("read", 16_000)) == 2
    assert calls[-2:] == ["stop", "close"]


def test_sounddevice_source_stop_request_ends_iteration_cleanly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []
    _install_fake_sounddevice(
        monkeypatch,
        reads=[b"\x00\x00", b"\x01\x00"],
        calls=calls,
    )
    source = SoundDeviceMicrophoneSource()

    chunks = asyncio.run(_collect_one_then_stop(source))

    assert len(chunks) == 1
    assert calls.count(("read", 16_000)) == 1
    assert calls[-2:] == ["stop", "close"]


@pytest.mark.parametrize(
    "device_id",
    [
        "",
        "microphone:1",
        "sounddevice:",
        "sounddevice:-1",
        "sounddevice:1.5",
        "sounddevice:abc",
    ],
)
def test_sounddevice_source_rejects_invalid_device_ids_before_opening_stream(
    monkeypatch: pytest.MonkeyPatch,
    device_id: str,
) -> None:
    calls: list[object] = []
    _install_fake_sounddevice(monkeypatch, reads=[b"\x00\x00"], calls=calls)

    with pytest.raises(ValueError, match="sounddevice:<index>"):
        SoundDeviceMicrophoneSource(device_id=device_id, max_chunks=1)

    assert calls == []


def test_sounddevice_source_rejects_non_string_device_id_before_opening_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []
    _install_fake_sounddevice(monkeypatch, reads=[b"\x00\x00"], calls=calls)

    with pytest.raises(TypeError, match="sounddevice:<index>"):
        SoundDeviceMicrophoneSource(device_id=7, max_chunks=1)  # type: ignore[arg-type]

    assert calls == []


def test_sounddevice_source_closes_stream_when_read_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []
    _install_fake_sounddevice(
        monkeypatch,
        reads=[RuntimeError("read exploded")],
        calls=calls,
    )
    source = SoundDeviceMicrophoneSource(max_chunks=1)

    with pytest.raises(RuntimeError, match="read exploded"):
        asyncio.run(_collect_chunks(source))

    assert calls[-2:] == ["stop", "close"]


def test_sounddevice_source_closes_stream_when_read_overflows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []
    _install_fake_sounddevice(
        monkeypatch,
        reads=[(b"\x00\x00", True)],
        calls=calls,
    )
    source = SoundDeviceMicrophoneSource(max_chunks=1)

    with pytest.raises(SoundDeviceMicrophoneCaptureError, match="overflow"):
        asyncio.run(_collect_chunks(source))

    assert calls[-2:] == ["stop", "close"]


def test_sounddevice_source_does_not_write_recording_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    _install_fake_sounddevice(monkeypatch, reads=[b"\x00\x00"])
    source = SoundDeviceMicrophoneSource(max_chunks=1)

    chunks = asyncio.run(_collect_chunks(source))

    assert len(chunks) == 1
    assert list(tmp_path.iterdir()) == []


async def _collect_chunks(
    source: SoundDeviceMicrophoneSource | MicrophoneSource,
) -> list[Any]:
    return [chunk async for chunk in source]


async def _collect_one_then_stop(
    source: SoundDeviceMicrophoneSource,
) -> list[Any]:
    chunks = []
    async for chunk in source:
        chunks.append(chunk)
        source.stop()
    return chunks


def _install_fake_sounddevice(
    monkeypatch: pytest.MonkeyPatch,
    *,
    reads: list[object],
    calls: list[object] | None = None,
) -> ModuleType:
    module = ModuleType("sounddevice")
    call_log = calls if calls is not None else []
    pending_reads = list(reads)

    class FakeRawInputStream:
        def __init__(self, **kwargs: Any) -> None:
            call_log.append(("open", kwargs))

        def start(self) -> None:
            call_log.append("start")

        def read(self, frames: int) -> object:
            call_log.append(("read", frames))
            if not pending_reads:
                raise AssertionError("unexpected sounddevice read")
            read_result = pending_reads.pop(0)
            if isinstance(read_result, BaseException):
                raise read_result
            return read_result

        def stop(self) -> None:
            call_log.append("stop")

        def close(self) -> None:
            call_log.append("close")

    module.RawInputStream = FakeRawInputStream  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "sounddevice", module)
    return module
