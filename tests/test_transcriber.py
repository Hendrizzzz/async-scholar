import wave
from pathlib import Path

import pytest

from async_scholar.audio import FileAudioSource, InvalidWavFileError
from async_scholar.stt import DeterministicFakeTranscriber


def _write_wav(
    path: Path,
    *,
    frame_count: int,
    sample_rate: int = 10,
    sample_width_bytes: int = 2,
    channel_count: int = 1,
    sample_value: int = 0,
) -> Path:
    frame = sample_value.to_bytes(
        sample_width_bytes,
        byteorder="little",
        signed=True,
    )
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channel_count)
        wav_file.setsampwidth(sample_width_bytes)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(frame * frame_count * channel_count)
    return path


def test_fake_transcriber_output_is_deterministic_for_same_wav(
    tmp_path: Path,
) -> None:
    wav_path = _write_wav(tmp_path / "lecture.wav", frame_count=12)
    transcriber = DeterministicFakeTranscriber(chunk_duration_seconds=0.5)

    first = transcriber.transcribe(wav_path)
    second = transcriber.transcribe(FileAudioSource(wav_path))

    assert first == second
    assert [segment.segment_id for segment in first] == [
        f"{first[0].session_id}-segment-0001",
        f"{first[0].session_id}-segment-0002",
        f"{first[0].session_id}-segment-0003",
    ]
    assert [segment.text for segment in first] == [
        "Deterministic fake transcript segment 1 of 3.",
        "Deterministic fake transcript segment 2 of 3.",
        "Deterministic fake transcript segment 3 of 3.",
    ]


def test_fake_transcriber_uses_chunk_timing_from_audio_duration(
    tmp_path: Path,
) -> None:
    wav_path = _write_wav(tmp_path / "partial-final-chunk.wav", frame_count=11)
    transcriber = DeterministicFakeTranscriber(chunk_duration_seconds=0.4)

    segments = transcriber.transcribe(wav_path)

    assert [(segment.start_seconds, segment.end_seconds) for segment in segments] == [
        (0.0, 0.4),
        (0.4, 0.8),
        (0.8, 1.1),
    ]


def test_fake_transcriber_handles_empty_and_silent_wavs(tmp_path: Path) -> None:
    empty_wav_path = _write_wav(tmp_path / "empty.wav", frame_count=0)
    silent_wav_path = _write_wav(tmp_path / "silent.wav", frame_count=1)
    transcriber = DeterministicFakeTranscriber(chunk_duration_seconds=0.5)

    assert transcriber.transcribe(empty_wav_path) == []

    silent_segments = transcriber.transcribe(silent_wav_path)
    assert len(silent_segments) == 1
    assert silent_segments[0].start_seconds == 0.0
    assert silent_segments[0].end_seconds == 0.1
    assert silent_segments[0].text == "Deterministic fake transcript segment 1 of 1."


def test_fake_transcriber_propagates_missing_and_invalid_wav_errors(
    tmp_path: Path,
) -> None:
    transcriber = DeterministicFakeTranscriber()
    invalid_path = tmp_path / "not-a-wav.wav"
    invalid_path.write_text("not wav data", encoding="utf-8")

    with pytest.raises(FileNotFoundError):
        transcriber.transcribe(tmp_path / "missing.wav")

    with pytest.raises(InvalidWavFileError):
        transcriber.transcribe(invalid_path)
