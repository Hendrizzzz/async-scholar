from __future__ import annotations

import asyncio
import io
import json
import struct

import pytest

import async_scholar.audio.mic_level_diagnostic as mic_level_diagnostic
from async_scholar.audio.mic_level_diagnostic import (
    DEFAULT_MIC_LEVEL_DIAGNOSTIC_MAX_CHUNKS,
    DEFAULT_MIC_LEVEL_DIAGNOSTIC_SECONDS,
    InvalidMicrophoneLevelDiagnosticConfigError,
    collect_microphone_level_diagnostic,
    format_microphone_level_diagnostic_report,
    main,
    run_microphone_level_diagnostic,
)
from async_scholar.audio.mic_source import MicrophoneCaptureConfig, MicrophonePcmChunk


def _pcm(*samples: int) -> bytes:
    return b"".join(struct.pack("<h", sample) for sample in samples)


def _chunk(
    start_seconds: float,
    end_seconds: float,
    *samples: int,
    sample_rate_hz: int = 16_000,
    channel_count: int = 1,
) -> MicrophonePcmChunk:
    return MicrophonePcmChunk(
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        pcm_bytes=_pcm(*samples),
        sample_rate_hz=sample_rate_hz,
        channel_count=channel_count,
    )


class FakeMicrophoneSource:
    def __init__(
        self,
        chunks: list[MicrophonePcmChunk],
        *,
        config: MicrophoneCaptureConfig | None = None,
    ) -> None:
        self.chunks = chunks
        self.config = config or MicrophoneCaptureConfig()
        self.stopped = False

    async def _iter_chunks(self):
        for chunk in self.chunks:
            yield chunk

    def stop(self) -> None:
        self.stopped = True


class SecretReprMicrophoneSource(FakeMicrophoneSource):
    def __repr__(self) -> str:
        return "SECRET_SOURCE sounddevice:9 pcm_bytes"


class ClosingChunkIterator:
    def __init__(self, chunks: list[MicrophonePcmChunk]) -> None:
        self._chunks = iter(chunks)
        self.closed = False

    def __aiter__(self):
        return self

    async def __anext__(self) -> MicrophonePcmChunk:
        try:
            return next(self._chunks)
        except StopIteration as exc:
            raise StopAsyncIteration from exc

    async def aclose(self) -> None:
        self.closed = True


class ClosingIteratorMicrophoneSource:
    def __init__(self, chunks: list[MicrophonePcmChunk]) -> None:
        self.config = MicrophoneCaptureConfig()
        self.iterator = ClosingChunkIterator(chunks)

    def _iter_chunks(self) -> ClosingChunkIterator:
        return self.iterator


def test_import_path_keeps_sounddevice_source_lazy() -> None:
    assert "SoundDeviceMicrophoneSource" not in mic_level_diagnostic.__dict__


def test_help_path_does_not_create_live_source(
    capsys: pytest.CaptureFixture[str],
) -> None:
    created_sources = 0

    def source_factory(
        config: MicrophoneCaptureConfig,
        device_id: str | None,
        max_chunks: int,
    ) -> FakeMicrophoneSource:
        nonlocal created_sources
        created_sources += 1
        return FakeMicrophoneSource([], config=config)

    with pytest.raises(SystemExit) as exc_info:
        main(["--help"], source_factory=source_factory)

    assert exc_info.value.code == 0
    assert created_sources == 0
    help_output = capsys.readouterr().out
    assert "--seconds" in help_output
    assert "--max-chunks" in help_output
    assert "--device-id" in help_output


@pytest.mark.parametrize(
    "argv",
    [
        ["--seconds", "0"],
        ["--seconds", "-1"],
        ["--seconds", "nan"],
        ["--max-chunks", "0"],
        ["--max-chunks", "-1"],
        ["--max-chunks", "1.5"],
        ["--device-id", "default"],
        ["--device-id", "sounddevice:"],
        ["--device-id", "sounddevice:-1"],
    ],
)
def test_argument_validation_rejects_invalid_inputs_without_source(
    argv: list[str],
) -> None:
    created_sources = 0

    def source_factory(
        config: MicrophoneCaptureConfig,
        device_id: str | None,
        max_chunks: int,
    ) -> FakeMicrophoneSource:
        nonlocal created_sources
        created_sources += 1
        return FakeMicrophoneSource([], config=config)

    with pytest.raises(SystemExit) as exc_info:
        main(argv, source_factory=source_factory)

    assert exc_info.value.code == 2
    assert created_sources == 0


def test_fake_source_diagnostic_summary_is_bounded() -> None:
    source = FakeMicrophoneSource(
        [
            _chunk(0.0, 0.25, 0, 1_000, -1_000),
            _chunk(0.25, 0.50, 0, 3_000, -3_000),
            _chunk(0.50, 0.75, 0, 8_000, -8_000),
        ]
    )

    report = asyncio.run(
        collect_microphone_level_diagnostic(source, seconds=10.0, max_chunks=2)
    )

    assert report.requested_duration_seconds == 10.0
    assert report.requested_max_chunks == 2
    assert report.chunk_count == 2
    assert report.total_audio_seconds == pytest.approx(0.5)
    assert report.peak_level > 0.0
    assert report.average_rms_level > 0.0
    assert report.sample_rate_hz == 16_000
    assert report.channel_count == 1
    assert report.any_chunks_observed is True


def test_diagnostic_closes_chunk_iterator_after_bounds() -> None:
    source = ClosingIteratorMicrophoneSource(
        [
            _chunk(0.0, 0.25, 0, 1_000),
            _chunk(0.25, 0.50, 0, 2_000),
        ]
    )

    report = asyncio.run(
        collect_microphone_level_diagnostic(source, seconds=10.0, max_chunks=1)
    )

    assert report.chunk_count == 1
    assert source.iterator.closed is True


def test_empty_capture_summary_uses_safe_zero_levels() -> None:
    source = FakeMicrophoneSource([])

    report = asyncio.run(
        collect_microphone_level_diagnostic(source, seconds=1.0, max_chunks=3)
    )

    assert report.chunk_count == 0
    assert report.total_audio_seconds == 0.0
    assert report.peak_level == 0.0
    assert report.average_rms_level == 0.0
    assert report.sample_rate_hz == 16_000
    assert report.channel_count == 1
    assert report.any_chunks_observed is False


def test_report_repr_and_output_are_privacy_safe() -> None:
    source = SecretReprMicrophoneSource(
        [_chunk(0.0, 0.25, 12_345)],
    )

    def source_factory(
        config: MicrophoneCaptureConfig,
        device_id: str | None,
        max_chunks: int,
    ) -> SecretReprMicrophoneSource:
        assert device_id == "sounddevice:9"
        return source

    report = asyncio.run(
        run_microphone_level_diagnostic(
            seconds=1.0,
            max_chunks=1,
            device_id="sounddevice:9",
            source_factory=source_factory,
        )
    )

    safe_text = repr(report) + format_microphone_level_diagnostic_report(report)
    assert "SECRET_SOURCE" not in safe_text
    assert "sounddevice:9" not in safe_text
    assert "pcm_bytes" not in safe_text
    assert "MicrophonePcmChunk" not in safe_text
    assert "b'" not in safe_text
    assert source.stopped is True


def test_module_command_prints_json_with_injected_source() -> None:
    calls: list[tuple[MicrophoneCaptureConfig, str | None, int]] = []

    def source_factory(
        config: MicrophoneCaptureConfig,
        device_id: str | None,
        max_chunks: int,
    ) -> FakeMicrophoneSource:
        calls.append((config, device_id, max_chunks))
        return FakeMicrophoneSource(
            [_chunk(0.0, 0.25, 0, 500), _chunk(0.25, 0.50, 0, 1_000)],
            config=config,
        )

    stdout = io.StringIO()

    exit_code = main(
        ["--seconds", "2", "--max-chunks", "2", "--device-id", "sounddevice:3"],
        source_factory=source_factory,
        stdout=stdout,
    )

    payload = json.loads(stdout.getvalue())
    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0][1] == "sounddevice:3"
    assert calls[0][2] == 2
    assert payload["requested_duration_seconds"] == 2.0
    assert payload["requested_max_chunks"] == 2
    assert payload["chunk_count"] == 2
    assert payload["any_chunks_observed"] is True
    assert "pcm_bytes" not in stdout.getvalue()
    assert "sounddevice:3" not in stdout.getvalue()


def test_module_command_has_no_file_writing_side_effects(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    def source_factory(
        config: MicrophoneCaptureConfig,
        device_id: str | None,
        max_chunks: int,
    ) -> FakeMicrophoneSource:
        return FakeMicrophoneSource([_chunk(0.0, 0.25, 0)], config=config)

    stdout = io.StringIO()

    assert main(["--seconds", "1"], source_factory=source_factory, stdout=stdout) == 0
    assert list(tmp_path.iterdir()) == []


def test_api_validation_happens_before_source_creation() -> None:
    created_sources = 0

    def source_factory(
        config: MicrophoneCaptureConfig,
        device_id: str | None,
        max_chunks: int,
    ) -> FakeMicrophoneSource:
        nonlocal created_sources
        created_sources += 1
        return FakeMicrophoneSource([], config=config)

    with pytest.raises(InvalidMicrophoneLevelDiagnosticConfigError):
        asyncio.run(
            run_microphone_level_diagnostic(
                seconds=DEFAULT_MIC_LEVEL_DIAGNOSTIC_SECONDS,
                max_chunks=DEFAULT_MIC_LEVEL_DIAGNOSTIC_MAX_CHUNKS,
                device_id="not-a-device",
                source_factory=source_factory,
            )
        )

    assert created_sources == 0
