import asyncio
import json
import struct
import wave
from pathlib import Path

import pytest

from async_scholar.audio import (
    MicrophoneCaptureConfig,
    MicrophonePcmChunk,
    MicrophoneSignalDiagnosticConfig,
    mic_recording_diagnostic,
)
from async_scholar.audio.mic_recording_diagnostic import (
    DEFAULT_MIC_RECORDING_DIAGNOSTIC_REPORT_FILENAME,
    DEFAULT_MIC_RECORDING_DIAGNOSTIC_WAV_FILENAME,
    InvalidMicrophoneRecordingDiagnosticConfigError,
    record_microphone_diagnostic,
)


class FakeMicrophoneSource:
    def __init__(
        self,
        *,
        config: MicrophoneCaptureConfig,
        chunks: list[MicrophonePcmChunk],
    ) -> None:
        self.config = config
        self._chunks = chunks

    async def __aiter__(self):
        for chunk in self._chunks:
            yield chunk


class CountingMicrophoneSource:
    def __init__(
        self,
        *,
        config: MicrophoneCaptureConfig,
        chunks: list[MicrophonePcmChunk],
    ) -> None:
        self.config = config
        self._chunks = chunks
        self.pull_count = 0

    def __aiter__(self):
        return self

    async def __anext__(self) -> MicrophonePcmChunk:
        if self.pull_count >= len(self._chunks):
            raise StopAsyncIteration
        chunk = self._chunks[self.pull_count]
        self.pull_count += 1
        return chunk


def test_record_microphone_diagnostic_writes_wav_and_scalar_report(
    tmp_path: Path,
) -> None:
    config = MicrophoneCaptureConfig(
        sample_rate_hz=8000,
        channel_count=1,
        chunk_duration_seconds=1.0,
    )
    first_chunk = _chunk(config, [0, 1000, -2000, 4000], start_seconds=0.0)
    second_chunk = _chunk(config, [0, 0, 0, 0], start_seconds=0.0005)
    source = FakeMicrophoneSource(config=config, chunks=[first_chunk, second_chunk])

    result = asyncio.run(
        record_microphone_diagnostic(
            source,
            tmp_path,
            seconds=10,
            max_chunks=2,
            timestamp="20260102T030405Z",
            signal_config=MicrophoneSignalDiagnosticConfig(
                silence_threshold=0.01,
                clipping_threshold=0.98,
            ),
        ),
    )

    expected_dir = tmp_path / "audio-diagnostic-20260102T030405Z"
    assert result.artifact_dir == expected_dir
    assert (
        result.wav_path == expected_dir / DEFAULT_MIC_RECORDING_DIAGNOSTIC_WAV_FILENAME
    )
    assert (
        result.report_path
        == expected_dir / DEFAULT_MIC_RECORDING_DIAGNOSTIC_REPORT_FILENAME
    )
    assert result.wav_path.exists()
    assert result.report_path.exists()

    with wave.open(str(result.wav_path), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 8000
        assert wav_file.getnframes() == 8
        assert wav_file.readframes(8) == first_chunk.pcm_bytes + second_chunk.pcm_bytes

    report = json.loads(result.report_path.read_text(encoding="utf-8"))
    assert report == {
        "artifact_filenames": {
            "report": DEFAULT_MIC_RECORDING_DIAGNOSTIC_REPORT_FILENAME,
            "wav": DEFAULT_MIC_RECORDING_DIAGNOSTIC_WAV_FILENAME,
        },
        "average_rms_level": pytest.approx(0.03496227794613525),
        "channel_count": 1,
        "chunk_count": 2,
        "clipping_detected": False,
        "peak_level": pytest.approx(0.1220703125),
        "sample_rate_hz": 8000,
        "silence_detected": True,
        "total_audio_seconds": pytest.approx(0.001),
    }
    serialized_report = result.report_path.read_text(encoding="utf-8")
    assert str(tmp_path) not in serialized_report
    assert "pcm" not in serialized_report.lower()
    assert "device" not in serialized_report.lower()
    assert "transcript" not in serialized_report.lower()
    assert "source" not in serialized_report.lower()


def test_record_microphone_diagnostic_trims_to_seconds_bound(
    tmp_path: Path,
) -> None:
    config = MicrophoneCaptureConfig(
        sample_rate_hz=4,
        channel_count=1,
        chunk_duration_seconds=1.0,
    )
    source = FakeMicrophoneSource(
        config=config,
        chunks=[_chunk(config, [1, 2, 3, 4], start_seconds=0.0)],
    )

    result = asyncio.run(
        record_microphone_diagnostic(
            source,
            tmp_path,
            seconds=0.5,
            max_chunks=1,
            timestamp="trim-test",
        ),
    )

    with wave.open(str(result.wav_path), "rb") as wav_file:
        assert wav_file.getnframes() == 2
        assert wav_file.readframes(2) == _pcm16([1, 2])
    assert result.report.chunk_count == 1
    assert result.report.total_audio_seconds == pytest.approx(0.5)


def test_record_microphone_diagnostic_respects_max_chunks(tmp_path: Path) -> None:
    config = MicrophoneCaptureConfig(
        sample_rate_hz=8000,
        channel_count=1,
        chunk_duration_seconds=1.0,
    )
    source = FakeMicrophoneSource(
        config=config,
        chunks=[
            _chunk(config, [1, 2], start_seconds=0.0),
            _chunk(config, [3, 4], start_seconds=0.00025),
        ],
    )

    result = asyncio.run(
        record_microphone_diagnostic(
            source,
            tmp_path,
            seconds=10,
            max_chunks=1,
            timestamp="max-chunks-test",
        ),
    )

    with wave.open(str(result.wav_path), "rb") as wav_file:
        assert wav_file.getnframes() == 2
        assert wav_file.readframes(2) == _pcm16([1, 2])
    assert result.report.chunk_count == 1


def test_record_microphone_diagnostic_does_not_pull_extra_chunk_after_limit(
    tmp_path: Path,
) -> None:
    config = MicrophoneCaptureConfig(
        sample_rate_hz=4,
        channel_count=1,
        chunk_duration_seconds=1.0,
    )
    source = CountingMicrophoneSource(
        config=config,
        chunks=[
            _chunk(config, [1, 2, 3, 4], start_seconds=0.0),
            _chunk(config, [5, 6, 7, 8], start_seconds=1.0),
        ],
    )

    result = asyncio.run(
        record_microphone_diagnostic(
            source,
            tmp_path,
            seconds=0.5,
            max_chunks=2,
            timestamp="bounded-pulls-test",
        ),
    )

    assert source.pull_count == 1
    assert result.report.chunk_count == 1
    with wave.open(str(result.wav_path), "rb") as wav_file:
        assert wav_file.getnframes() == 2
        assert wav_file.readframes(2) == _pcm16([1, 2])


def test_record_microphone_diagnostic_rejects_unbounded_inputs(
    tmp_path: Path,
) -> None:
    config = MicrophoneCaptureConfig(
        sample_rate_hz=8000,
        channel_count=1,
        chunk_duration_seconds=1.0,
    )
    source = FakeMicrophoneSource(
        config=config,
        chunks=[_chunk(config, [1], start_seconds=0.0)],
    )

    with pytest.raises(InvalidMicrophoneRecordingDiagnosticConfigError):
        asyncio.run(
            record_microphone_diagnostic(
                source,
                tmp_path,
                seconds=0,
                max_chunks=1,
                timestamp="invalid-seconds",
            ),
        )

    with pytest.raises(InvalidMicrophoneRecordingDiagnosticConfigError):
        asyncio.run(
            record_microphone_diagnostic(
                source,
                tmp_path,
                seconds=1,
                max_chunks=0,
                timestamp="invalid-max-chunks",
            ),
        )

    for invalid_max_chunks in (True, 1.5, float("nan"), float("inf")):
        with pytest.raises(InvalidMicrophoneRecordingDiagnosticConfigError):
            asyncio.run(
                record_microphone_diagnostic(
                    source,
                    tmp_path,
                    seconds=1,
                    max_chunks=invalid_max_chunks,  # type: ignore[arg-type]
                    timestamp=f"invalid-max-chunks-{invalid_max_chunks}",
                ),
            )


def test_record_microphone_diagnostic_rejects_private_path_timestamps(
    tmp_path: Path,
) -> None:
    config = MicrophoneCaptureConfig(
        sample_rate_hz=8000,
        channel_count=1,
        chunk_duration_seconds=1.0,
    )
    source = FakeMicrophoneSource(
        config=config,
        chunks=[_chunk(config, [1], start_seconds=0.0)],
    )

    with pytest.raises(InvalidMicrophoneRecordingDiagnosticConfigError):
        asyncio.run(
            record_microphone_diagnostic(
                source,
                tmp_path,
                seconds=1,
                max_chunks=1,
                timestamp="..\\private",
            ),
        )
    assert not list(tmp_path.iterdir())


def test_record_microphone_diagnostic_rejects_chunk_config_mismatch(
    tmp_path: Path,
) -> None:
    config = MicrophoneCaptureConfig(
        sample_rate_hz=8000,
        channel_count=1,
        chunk_duration_seconds=1.0,
    )
    mismatched_chunk = MicrophonePcmChunk(
        start_seconds=0.0,
        end_seconds=1.0,
        pcm_bytes=_pcm16([1, 2]),
        sample_rate_hz=16000,
        channel_count=1,
    )
    source = FakeMicrophoneSource(config=config, chunks=[mismatched_chunk])

    with pytest.raises(InvalidMicrophoneRecordingDiagnosticConfigError):
        asyncio.run(
            record_microphone_diagnostic(
                source,
                tmp_path,
                seconds=1,
                max_chunks=1,
                timestamp="mismatch-test",
            ),
        )


def test_module_help_is_lazy_and_writes_no_files(tmp_path: Path) -> None:
    def fail_source_factory(
        _config: MicrophoneCaptureConfig,
        _device_id: str | None,
        _max_chunks: int,
    ) -> FakeMicrophoneSource:
        raise AssertionError("help should not build a microphone source")

    with pytest.raises(SystemExit) as error:
        mic_recording_diagnostic.main(
            ["--help"],
            source_factory=fail_source_factory,
            timestamp_factory=lambda: "help-test",
        )

    assert error.value.code == 0
    assert not list(tmp_path.iterdir())


def test_module_main_uses_injected_source_and_timestamp(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_seen = None
    device_id_seen = None
    max_chunks_seen = None

    def source_factory(
        config: MicrophoneCaptureConfig,
        device_id: str | None,
        max_chunks: int,
    ) -> FakeMicrophoneSource:
        nonlocal config_seen, device_id_seen, max_chunks_seen
        config_seen = config
        device_id_seen = device_id
        max_chunks_seen = max_chunks
        return FakeMicrophoneSource(
            config=config,
            chunks=[_chunk(config, [10, -10], start_seconds=0.0)],
        )

    exit_code = mic_recording_diagnostic.main(
        [
            "--output-root",
            str(tmp_path),
            "--seconds",
            "1",
            "--max-chunks",
            "1",
            "--device-id",
            "test-device",
        ],
        source_factory=source_factory,
        timestamp_factory=lambda: "main-test",
    )

    assert exit_code == 0
    assert config_seen == MicrophoneCaptureConfig()
    assert device_id_seen == "test-device"
    assert max_chunks_seen == 1
    report = json.loads(capsys.readouterr().out)
    assert report["artifact_filenames"] == {
        "report": DEFAULT_MIC_RECORDING_DIAGNOSTIC_REPORT_FILENAME,
        "wav": DEFAULT_MIC_RECORDING_DIAGNOSTIC_WAV_FILENAME,
    }
    assert str(tmp_path) not in json.dumps(report)
    assert (
        tmp_path
        / "audio-diagnostic-main-test"
        / DEFAULT_MIC_RECORDING_DIAGNOSTIC_REPORT_FILENAME
    ).exists()


def test_package_exports_recording_diagnostic_api() -> None:
    import async_scholar.audio as audio

    assert audio.record_microphone_diagnostic is record_microphone_diagnostic
    assert (
        audio.DEFAULT_MIC_RECORDING_DIAGNOSTIC_WAV_FILENAME
        == DEFAULT_MIC_RECORDING_DIAGNOSTIC_WAV_FILENAME
    )


def _chunk(
    config: MicrophoneCaptureConfig,
    samples: list[int],
    *,
    start_seconds: float,
) -> MicrophonePcmChunk:
    frame_count = len(samples) // config.channel_count
    end_seconds = start_seconds + (frame_count / config.sample_rate_hz)
    return MicrophonePcmChunk(
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        pcm_bytes=_pcm16(samples),
        sample_rate_hz=config.sample_rate_hz,
        channel_count=config.channel_count,
    )


def _pcm16(samples: list[int]) -> bytes:
    return struct.pack(f"<{len(samples)}h", *samples)
