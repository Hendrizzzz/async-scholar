from __future__ import annotations

import importlib
import sys
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
