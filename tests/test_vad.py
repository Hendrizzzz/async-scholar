from __future__ import annotations

import importlib
import sys
import wave
from pathlib import Path

import pytest


def test_audio_package_import_does_not_import_silero_vad() -> None:
    sys.modules.pop("silero_vad", None)
    sys.modules.pop("async_scholar.audio", None)
    sys.modules.pop("async_scholar.audio.vad", None)

    audio = importlib.import_module("async_scholar.audio")

    assert "silero_vad" not in sys.modules
    assert audio.SileroVadDetector.__name__ == "SileroVadDetector"


def test_detector_loads_lazily_and_converts_samples_to_seconds() -> None:
    vad = importlib.import_module("async_scholar.audio.vad")
    events: list[tuple[object, ...]] = []
    model = object()

    def read_audio(path: str, *, sampling_rate: int) -> object:
        events.append(("read", path, sampling_rate))
        return "audio"

    def get_speech_timestamps(
        audio: object,
        loaded_model: object,
        *,
        sampling_rate: int,
        return_seconds: bool,
    ) -> list[dict[str, int]]:
        events.append(
            ("timestamps", audio, loaded_model, sampling_rate, return_seconds)
        )
        return [{"start": 1600, "end": 3200}]

    def loader() -> vad.SileroRuntime:
        events.append(("load",))
        return model, read_audio, get_speech_timestamps

    detector = vad.SileroVadDetector(loader=loader)

    assert events == []

    windows = detector.detect_file(Path("lecture.wav"))

    assert windows == [vad.SpeechWindow(start_seconds=0.1, end_seconds=0.2)]
    assert events == [
        ("load",),
        ("read", str(Path("lecture.wav")), 16_000),
        ("timestamps", "audio", model, 16_000, False),
    ]

    detector.detect_file("second.wav")

    assert events.count(("load",)) == 1


def test_detector_returns_empty_list_when_silero_finds_no_speech() -> None:
    vad = importlib.import_module("async_scholar.audio.vad")
    model = object()

    def read_audio(path: str, *, sampling_rate: int) -> object:
        return path, sampling_rate

    def get_speech_timestamps(
        audio: object,
        loaded_model: object,
        *,
        sampling_rate: int,
        return_seconds: bool,
    ) -> list[dict[str, int]]:
        return []

    detector = vad.SileroVadDetector(
        loader=lambda: (model, read_audio, get_speech_timestamps)
    )

    assert detector.detect_file("quiet.wav") == []


def test_detector_falls_back_to_local_pcm_wav_when_torchcodec_is_missing(
    tmp_path: Path,
) -> None:
    vad = importlib.import_module("async_scholar.audio.vad")
    audio_path = tmp_path / "synthetic.wav"
    _write_pcm16_wav(audio_path, [0, 16_384, -16_384])
    model = object()
    observed: dict[str, object] = {}

    def read_audio(path: str, *, sampling_rate: int) -> object:
        raise RuntimeError(
            "torchaudio version 2.11.0+cpu requires torchcodec for audio I/O"
        )

    def get_speech_timestamps(
        audio: object,
        loaded_model: object,
        *,
        sampling_rate: int,
        return_seconds: bool,
    ) -> list[dict[str, int]]:
        observed["audio"] = audio
        observed["model"] = loaded_model
        observed["sampling_rate"] = sampling_rate
        observed["return_seconds"] = return_seconds
        return [{"start": 1600, "end": 3200}]

    detector = vad.SileroVadDetector(
        loader=lambda: (model, read_audio, get_speech_timestamps)
    )

    assert detector.detect_file(audio_path) == [
        vad.SpeechWindow(start_seconds=0.1, end_seconds=0.2)
    ]
    assert observed["model"] is model
    assert observed["sampling_rate"] == 16_000
    assert observed["return_seconds"] is False
    fallback_audio = observed["audio"]
    assert tuple(fallback_audio.shape) == (3,)
    assert str(fallback_audio.dtype) == "torch.float32"
    assert float(fallback_audio[0]) == 0.0
    assert float(fallback_audio[1]) == pytest.approx(0.5)
    assert float(fallback_audio[2]) == pytest.approx(-0.5)


def test_detector_does_not_swallow_unrelated_audio_read_errors() -> None:
    vad = importlib.import_module("async_scholar.audio.vad")
    model = object()

    def read_audio(path: str, *, sampling_rate: int) -> object:
        raise ImportError("unrelated optional backend is missing")

    def get_speech_timestamps(
        audio: object,
        loaded_model: object,
        *,
        sampling_rate: int,
        return_seconds: bool,
    ) -> list[dict[str, int]]:
        return []

    detector = vad.SileroVadDetector(
        loader=lambda: (model, read_audio, get_speech_timestamps)
    )

    with pytest.raises(ImportError, match="unrelated optional backend"):
        detector.detect_file("synthetic.wav")


def test_torchcodec_fallback_rejects_malformed_wav(tmp_path: Path) -> None:
    vad = importlib.import_module("async_scholar.audio.vad")
    audio_path = tmp_path / "not-a-wav.wav"
    audio_path.write_bytes(b"not a wav")
    model = object()

    def read_audio(path: str, *, sampling_rate: int) -> object:
        raise RuntimeError("TorchCodec is required for load_with_torchcodec")

    def get_speech_timestamps(
        audio: object,
        loaded_model: object,
        *,
        sampling_rate: int,
        return_seconds: bool,
    ) -> list[dict[str, int]]:
        return []

    detector = vad.SileroVadDetector(
        loader=lambda: (model, read_audio, get_speech_timestamps)
    )

    with pytest.raises(ValueError, match="PCM WAV audio could not be read"):
        detector.detect_file(audio_path)


def test_torchcodec_fallback_rejects_unexpected_sample_rate(tmp_path: Path) -> None:
    vad = importlib.import_module("async_scholar.audio.vad")
    audio_path = tmp_path / "wrong-rate.wav"
    _write_pcm16_wav(audio_path, [0, 1024], sample_rate=8_000)
    model = object()

    def read_audio(path: str, *, sampling_rate: int) -> object:
        raise RuntimeError("TorchCodec is required for load_with_torchcodec")

    def get_speech_timestamps(
        audio: object,
        loaded_model: object,
        *,
        sampling_rate: int,
        return_seconds: bool,
    ) -> list[dict[str, int]]:
        return []

    detector = vad.SileroVadDetector(
        loader=lambda: (model, read_audio, get_speech_timestamps)
    )

    with pytest.raises(ValueError, match="requested sample rate"):
        detector.detect_file(audio_path)


@pytest.mark.parametrize(
    "timestamp",
    [
        {},
        {"start": 0},
        {"start": "0", "end": 10},
        {"start": True, "end": 10},
        {"start": float("nan"), "end": 10},
        {"start": -1, "end": 10},
        {"start": 20, "end": 20},
        {"start": 30, "end": 20},
        object(),
    ],
)
def test_invalid_timestamps_raise_local_error(timestamp: object) -> None:
    vad = importlib.import_module("async_scholar.audio.vad")

    with pytest.raises(vad.InvalidVadTimestampError):
        vad.speech_windows_from_timestamps([timestamp], sample_rate=16_000)


def _write_pcm16_wav(
    path: Path,
    samples: list[int],
    *,
    sample_rate: int = 16_000,
) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(
            b"".join(sample.to_bytes(2, "little", signed=True) for sample in samples)
        )
