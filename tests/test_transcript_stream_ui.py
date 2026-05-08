from __future__ import annotations

import builtins
import importlib
import importlib.util
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FORBIDDEN_IMPORT_PREFIXES = (
    "async_scholar.demo",
    "async_scholar.audio",
    "async_scholar.stt",
    "async_scholar.artifacts",
    "async_scholar.scheduler",
    "async_scholar.browser",
    "fastapi",
)


class FakeElement:
    def __init__(
        self,
        ui: FakeUi,
        kind: str,
        *,
        text: str | None = None,
        icon: str | None = None,
        on_click: Any = None,
    ) -> None:
        self.ui = ui
        self.kind = kind
        self.text = text
        self.icon = icon
        self.on_click = on_click
        self.children: list[FakeElement] = []
        self.class_values: list[str] = []
        self.prop_values: list[str] = []
        self.tooltip_text: str | None = None
        if ui.stack:
            ui.stack[-1].children.append(self)
        ui.elements.append(self)
        if kind == "label" and text is not None:
            ui.labels.append(text)
        if kind == "button":
            ui.buttons.append(self)

    def __enter__(self) -> FakeElement:
        self.ui.stack.append(self)
        return self

    def __exit__(self, *args: object) -> None:
        self.ui.stack.pop()

    def classes(self, value: str) -> FakeElement:
        self.class_values.append(value)
        return self

    def props(self, value: str) -> FakeElement:
        self.prop_values.append(value)
        return self

    def tooltip(self, value: str) -> FakeElement:
        self.tooltip_text = value
        return self

    def clear(self) -> None:
        self.children.clear()


class FakeUi:
    def __init__(self) -> None:
        self.elements: list[FakeElement] = []
        self.labels: list[str] = []
        self.buttons: list[FakeElement] = []
        self.stack: list[FakeElement] = []

    def column(self) -> FakeElement:
        return FakeElement(self, "column")

    def row(self) -> FakeElement:
        return FakeElement(self, "row")

    def label(self, text: str) -> FakeElement:
        return FakeElement(self, "label", text=text)

    def button(
        self,
        text: str | None = None,
        *,
        icon: str | None = None,
        on_click: Any = None,
    ) -> FakeElement:
        return FakeElement(self, "button", text=text, icon=icon, on_click=on_click)


def load_transcript_module():
    return importlib.import_module("async_scholar.ui.transcript_stream")


def test_transcript_stream_import_is_safe(monkeypatch) -> None:
    module_name = "transcript_stream_under_test"
    module_path = Path("src/async_scholar/ui/transcript_stream.py")
    sys.modules.pop(module_name, None)
    imported: list[str] = []
    real_import = builtins.__import__

    def guarded_import(name: str, *args: object, **kwargs: object):
        imported.append(name)
        if name.startswith(FORBIDDEN_IMPORT_PREFIXES):
            raise AssertionError(f"forbidden import: {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    source = module_path.read_text(encoding="utf-8")

    assert "run_fixture_demo" not in source
    assert "from fastapi" not in source
    assert "import fastapi" not in source
    assert not any(name.startswith(FORBIDDEN_IMPORT_PREFIXES) for name in imported)


def test_safe_segment_normalization_and_formatting() -> None:
    module = load_transcript_module()

    segment = module.segment_to_transcript_model(
        {
            "text": "  Professor: attendance check.  ",
            "speaker": "Professor Kim",
            "start_seconds": "65.2",
            "end_seconds": 72.9,
        }
    )
    formatted = module.format_transcript_segment(segment)

    assert segment.text == "Professor: attendance check."
    assert segment.speaker == "Professor Kim"
    assert segment.start_seconds == 65.2
    assert segment.end_seconds == 72.9
    assert formatted == {
        "time": "01:05 - 01:12",
        "speaker": "Professor Kim",
        "text": "Professor: attendance check.",
    }


def test_private_fields_are_omitted_from_model_and_rendering() -> None:
    module = load_transcript_module()
    private_values = {
        "artifact_path": "C:\\Users\\student\\private\\transcript.jsonl",
        "source_path": "C:\\private\\class.mp4",
        "raw_audio_path": "C:\\private\\lecture.wav",
        "token": "secret-token",
        "cookie": "session-cookie",
        "auth_state": "browser-auth",
        "browser_profile": "profile-data",
        "model_path": "C:\\models\\local.bin",
        "generated_media": "C:\\media\\frame.png",
        "raw_exception": "Traceback (most recent call last)",
        "traceback": "ValueError: private stack",
        "alert_payload": {"message": "answer for me"},
        "metadata": {"unknown": "unknown-private"},
    }
    segment = {
        "text": "Here is the lecture text.",
        "speaker": "Student 1",
        "start_seconds": 1,
        "end_seconds": 2,
        **private_values,
    }

    model = module.segment_to_transcript_model(segment)
    fake_ui = FakeUi()
    module.render_transcript_stream_view([segment], ui=fake_ui)
    rendered = " ".join(fake_ui.labels)
    model_values = " ".join(str(value) for value in vars(model).values())

    assert set(vars(model)) == module.SAFE_TRANSCRIPT_FIELDS
    for value in private_values.values():
        assert str(value) not in model_values
        assert str(value) not in rendered


@dataclass(frozen=True)
class ObjectSegment:
    text: str
    speaker_label: str
    start_time: object
    end_time: object
    cookie: str


def test_untrusted_numeric_and_time_values_are_normalized() -> None:
    module = load_transcript_module()

    models = module.normalize_transcript_segments(
        [
            {
                "text": "Negative start is hidden.",
                "speaker": "C:\\private\\speaker.txt",
                "start_seconds": -3,
                "end_seconds": math.inf,
            },
            {
                "text": "End before start is hidden.",
                "speaker": "Learner 2",
                "start_seconds": 10,
                "end_seconds": 5,
            },
            ObjectSegment(
                text="Object segment works.",
                speaker_label="Teacher A",
                start_time=True,
                end_time="12.7",
                cookie="private-cookie",
            ),
        ]
    )

    assert models[0].speaker == "Unknown speaker"
    assert models[0].start_seconds is None
    assert models[0].end_seconds is None
    assert models[1].start_seconds == 10
    assert models[1].end_seconds is None
    assert models[2].speaker == "Teacher A"
    assert models[2].start_seconds is None
    assert models[2].end_seconds == 12.7


def test_empty_stream_rendering() -> None:
    module = load_transcript_module()
    fake_ui = FakeUi()

    view = module.render_transcript_stream_view([], ui=fake_ui)

    assert view.segments == ()
    assert "No transcript segments yet." in fake_ui.labels


def test_callback_refreshes_from_injected_source_only() -> None:
    module = load_transcript_module()
    fake_ui = FakeUi()
    calls = 0
    batches = [
        [{"text": "First segment.", "speaker": "Teacher", "start": 0, "end": 1}],
        [{"text": "Second segment.", "speaker": "Teacher", "start": 2, "end": 3}],
    ]

    def source() -> list[dict[str, object]]:
        nonlocal calls
        calls += 1
        return batches[min(calls - 1, len(batches) - 1)]

    view = module.render_transcript_stream_view(source, ui=fake_ui)

    assert calls == 1
    assert view.segments[0].text == "First segment."
    assert fake_ui.buttons
    assert fake_ui.buttons[0].icon == "refresh"

    fake_ui.buttons[0].on_click()

    assert calls == 2
    assert view.segments[0].text == "Second segment."
    assert "Second segment." in fake_ui.labels
