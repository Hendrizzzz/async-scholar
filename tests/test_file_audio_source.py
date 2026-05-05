import wave

import pytest

from async_scholar.audio import FileAudioSource, InvalidWavFileError


def write_wav(
    path,
    *,
    sample_rate: int,
    channel_count: int,
    sample_width_bytes: int,
    frames: bytes,
) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(channel_count)
        wav_file.setsampwidth(sample_width_bytes)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(frames)


def test_reads_wav_metadata(tmp_path):
    wav_path = tmp_path / "lecture.wav"
    write_wav(
        wav_path,
        sample_rate=8_000,
        channel_count=2,
        sample_width_bytes=2,
        frames=b"\x00" * 16,
    )

    metadata = FileAudioSource(wav_path).metadata

    assert metadata.path == wav_path
    assert metadata.sample_rate == 8_000
    assert metadata.channel_count == 2
    assert metadata.sample_width_bytes == 2
    assert metadata.frame_count == 4
    assert metadata.duration_seconds == pytest.approx(0.0005)


def test_iterates_chunks_in_order_with_frame_derived_timing(tmp_path):
    wav_path = tmp_path / "lecture.wav"
    write_wav(
        wav_path,
        sample_rate=10,
        channel_count=1,
        sample_width_bytes=1,
        frames=b"abcdefghij",
    )

    chunks = list(FileAudioSource(wav_path).iter_chunks(0.3))

    assert [chunk.pcm_bytes for chunk in chunks] == [
        b"abc",
        b"def",
        b"ghi",
        b"j",
    ]
    assert [chunk.start_seconds for chunk in chunks] == pytest.approx(
        [0.0, 0.3, 0.6, 0.9]
    )
    assert [chunk.end_seconds for chunk in chunks] == pytest.approx(
        [0.3, 0.6, 0.9, 1.0]
    )


def test_missing_file_raises_clear_error(tmp_path):
    missing_path = tmp_path / "missing.wav"

    with pytest.raises(FileNotFoundError, match="WAV file not found"):
        FileAudioSource(missing_path)


def test_invalid_non_wav_file_raises_clear_error(tmp_path):
    invalid_path = tmp_path / "not-a-wav.wav"
    invalid_path.write_text("this is not a wav file", encoding="utf-8")

    with pytest.raises(InvalidWavFileError, match="valid WAV file"):
        FileAudioSource(invalid_path)


def test_rejects_chunk_duration_too_small_for_one_frame(tmp_path):
    wav_path = tmp_path / "lecture.wav"
    write_wav(
        wav_path,
        sample_rate=10,
        channel_count=1,
        sample_width_bytes=1,
        frames=b"abc",
    )

    source = FileAudioSource(wav_path)

    with pytest.raises(ValueError, match="at least one audio frame"):
        list(source.iter_chunks(0.01))
