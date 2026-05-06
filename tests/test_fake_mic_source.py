from __future__ import annotations

import asyncio
import subprocess
import sys

import pytest

from async_scholar.audio import (
    DeterministicFakeMicrophoneSource,
    MicrophoneCaptureConfig,
    MicrophonePcmChunk,
    MicrophoneSource,
)


def test_fake_mic_source_yields_deterministic_pcm_chunks() -> None:
    config = MicrophoneCaptureConfig(
        sample_rate_hz=8_000,
        channel_count=2,
        chunk_duration_seconds=0.25,
    )
    source: MicrophoneSource = DeterministicFakeMicrophoneSource(
        pcm_payloads=[b"chunk-a", b"chunk-b"],
        config=config,
    )

    chunks = asyncio.run(_collect_chunks(source))

    assert [chunk.pcm_bytes for chunk in chunks] == [b"chunk-a", b"chunk-b"]
    assert [(chunk.start_seconds, chunk.end_seconds) for chunk in chunks] == [
        (0.0, 0.25),
        (0.25, 0.5),
    ]
    assert [chunk.sample_rate_hz for chunk in chunks] == [8_000, 8_000]
    assert [chunk.channel_count for chunk in chunks] == [2, 2]


def test_fake_mic_source_empty_input_yields_no_chunks() -> None:
    source = DeterministicFakeMicrophoneSource(pcm_payloads=[])

    assert asyncio.run(_collect_chunks(source)) == []


def test_fake_mic_source_timestamps_are_contiguous() -> None:
    source = DeterministicFakeMicrophoneSource(
        pcm_payloads=[b"one", b"two", b"three"],
        config=MicrophoneCaptureConfig(chunk_duration_seconds=0.1),
    )

    chunks = asyncio.run(_collect_chunks(source))

    assert chunks[0].start_seconds == 0.0
    for previous, current in zip(chunks[:-1], chunks[1:], strict=True):
        assert previous.end_seconds == current.start_seconds
    assert chunks[-1].end_seconds == pytest.approx(0.3)


def test_fake_mic_source_can_be_iterated_more_than_once() -> None:
    source = DeterministicFakeMicrophoneSource(pcm_payloads=[b"first"])

    first_pass = asyncio.run(_collect_chunks(source))
    second_pass = asyncio.run(_collect_chunks(source))

    assert first_pass == second_pass
    assert first_pass == [
        MicrophonePcmChunk(
            start_seconds=0.0,
            end_seconds=1.0,
            pcm_bytes=b"first",
        ),
    ]


def test_fake_mic_source_repr_keeps_audio_payloads_private() -> None:
    private_payload = b"private raw microphone bytes"
    source = DeterministicFakeMicrophoneSource(pcm_payloads=[private_payload])

    chunks = asyncio.run(_collect_chunks(source))

    assert "private raw microphone bytes" not in repr(source)
    assert "pcm_payloads" not in repr(source)
    assert "private raw microphone bytes" not in repr(chunks[0])
    assert "pcm_bytes" not in repr(chunks[0])


@pytest.mark.parametrize(
    ("pcm_payloads", "match"),
    [
        (b"single-bytes-object", "pcm_payloads must be a sequence"),
        ("not bytes", "pcm_payloads must be a sequence"),
        ([bytearray(b"not immutable bytes")], r"pcm_payloads\[0\] must be bytes"),
        ([b"ok", "not bytes"], r"pcm_payloads\[1\] must be bytes"),
    ],
)
def test_fake_mic_source_rejects_invalid_payloads(
    pcm_payloads: object,
    match: str,
) -> None:
    with pytest.raises(TypeError, match=match):
        DeterministicFakeMicrophoneSource(pcm_payloads=pcm_payloads)


def test_fake_mic_source_rejects_invalid_config() -> None:
    with pytest.raises(TypeError, match="config must be a MicrophoneCaptureConfig"):
        DeterministicFakeMicrophoneSource(
            pcm_payloads=[b"chunk"],
            config=object(),
        )


def test_fake_mic_source_imports_do_not_load_hardware_or_model_dependencies() -> None:
    code = """
import sys

import async_scholar.audio
import async_scholar.audio.fake_mic_source

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


async def _collect_chunks(source: MicrophoneSource) -> list[MicrophonePcmChunk]:
    return [chunk async for chunk in source]
