from __future__ import annotations

import importlib
import importlib.util
import sys
from dataclasses import asdict
from math import inf, nan
from pathlib import Path
from types import SimpleNamespace

import pytest

FORBIDDEN_MODULES = (
    "async_scholar.demo",
    "async_scholar.rules",
    "async_scholar.artifacts",
    "async_scholar.alert_dispatch",
    "async_scholar.alerts",
    "async_scholar.desktop_notifier",
    "async_scholar.telegram_notifier",
    "async_scholar.audio",
    "async_scholar.stt",
    "async_scholar.scheduler",
    "async_scholar.browser",
    "fastapi",
)


class FakeElement:
    def __init__(
        self,
        ui: FakeUI,
        *,
        text: str | None = None,
        on_click: object | None = None,
    ) -> None:
        self._ui = ui
        self.text = text
        self.on_click = on_click
        self.children: list[FakeElement] = []
        if ui._stack:
            ui._stack[-1].children.append(self)
        else:
            ui.roots.append(self)

    def __enter__(self) -> FakeElement:
        self._ui._stack.append(self)
        return self

    def __exit__(self, *_exc: object) -> None:
        self._ui._stack.pop()

    def classes(self, _classes: str) -> FakeElement:
        return self

    def props(self, _props: str) -> FakeElement:
        return self

    def tooltip(self, _text: str) -> FakeElement:
        return self

    def clear(self) -> None:
        self.children.clear()

    def rendered_text(self) -> list[str]:
        text = [self.text] if self.text is not None else []
        for child in self.children:
            text.extend(child.rendered_text())
        return text


class FakeUI:
    def __init__(self) -> None:
        self.roots: list[FakeElement] = []
        self.buttons: list[FakeElement] = []
        self._stack: list[FakeElement] = []

    def column(self) -> FakeElement:
        return FakeElement(self)

    def label(self, text: str) -> FakeElement:
        return FakeElement(self, text=text)

    def button(
        self,
        text: str = "",
        *,
        icon: str | None = None,
        on_click: object | None = None,
    ) -> FakeElement:
        button = FakeElement(self, text=text or icon, on_click=on_click)
        self.buttons.append(button)
        return button

    def rendered_text(self) -> list[str]:
        text: list[str] = []
        for root in self.roots:
            text.extend(root.rendered_text())
        return text


def test_event_timeline_module_import_is_safe() -> None:
    for module_name in FORBIDDEN_MODULES:
        sys.modules.pop(module_name, None)

    package = importlib.import_module("async_scholar")
    module_path = Path(package.__file__).parent / "ui" / "event_timeline.py"
    spec = importlib.util.spec_from_file_location(
        "_event_timeline_import_safety_probe",
        module_path,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)

    for module_name in FORBIDDEN_MODULES:
        assert module_name not in sys.modules

    source = module_path.read_text(encoding="utf-8")
    forbidden_references = (
        "async_scholar.demo",
        "async_scholar.rules",
        "async_scholar.artifacts",
        "async_scholar.alert_dispatch",
        "async_scholar.alerts",
        "async_scholar.desktop_notifier",
        "async_scholar.telegram_notifier",
        "async_scholar.audio",
        "async_scholar.stt",
        "async_scholar.scheduler",
        "async_scholar.browser",
        "run_fixture_demo",
        "fastapi",
        "FastAPI",
    )
    for reference in forbidden_references:
        assert reference not in source


def test_event_normalization_and_formatting_from_source() -> None:
    from async_scholar.ui.event_timeline import (
        format_event_timeline_event,
        normalize_event_timeline_events,
    )

    def source() -> list[object]:
        return [
            {
                "event_type": "attendance_prompt",
                "detected_at": 12.34,
                "confidence": 0.876,
                "message": "raw message must not render",
            },
            SimpleNamespace(
                type="question",
                timestamp="2026-05-08T08:10:30Z",
                confidence="42",
            ),
        ]

    events = normalize_event_timeline_events(source)

    assert [event.event_type_label for event in events] == [
        "Attendance prompt",
        "Question",
    ]
    assert events[0].detected_time_label == "12.3s"
    assert events[0].confidence_label == "88% confidence"
    assert events[1].detected_time_label == "2026-05-08 08:10:30Z"
    assert events[1].confidence_label == "42% confidence"
    assert (
        format_event_timeline_event(events[0])
        == "Attendance prompt - 12.3s - 88% confidence"
    )


def test_private_fields_are_omitted_from_model_and_rendering() -> None:
    from async_scholar.ui.event_timeline import (
        SAFE_EVENT_TIMELINE_FIELDS,
        event_to_timeline_model,
        render_event_timeline_view,
    )

    private_values = (
        "secret-message",
        "segment-123",
        "event-123",
        "session-123",
        "private transcript text",
        "C:\\private\\lecture.wav",
        "C:\\models\\local.bin",
        "C:\\generated\\media.png",
        "alert payload",
        "dispatch result",
        "retry decision",
        "token-value",
        "cookie-value",
        "browser-auth-state",
        "raw exception value",
        "traceback value",
        "unknown metadata value",
    )
    raw_event = {
        "event_type": "attendance_prompt",
        "detected_at": 2,
        "confidence": 0.5,
        "message": private_values[0],
        "source_segment_id": private_values[1],
        "event_id": private_values[2],
        "session_id": private_values[3],
        "transcript_text": private_values[4],
        "raw_audio_path": private_values[5],
        "model_path": private_values[6],
        "generated_media_path": private_values[7],
        "alert_payload": private_values[8],
        "dispatch_result": private_values[9],
        "retry_decision": private_values[10],
        "token": private_values[11],
        "cookie": private_values[12],
        "auth_browser_data": private_values[13],
        "exception": private_values[14],
        "traceback": private_values[15],
        "metadata": private_values[16],
    }

    model = event_to_timeline_model(raw_event)
    assert tuple(asdict(model)) == SAFE_EVENT_TIMELINE_FIELDS

    fake_ui = FakeUI()
    render_event_timeline_view(lambda: [raw_event], ui=fake_ui)
    rendered = "\n".join(fake_ui.rendered_text())

    for private_value in private_values:
        assert private_value not in rendered
        assert private_value not in repr(model)

    assert "Attendance prompt - 2s - 50% confidence" in rendered


@pytest.mark.parametrize(
    ("event_type", "expected_label"),
    [
        ("not-a-real-type", "Event"),
        ("C:\\private\\type-token", "Event"),
        (123, "Event"),
    ],
)
def test_unknown_event_type_normalizes_to_controlled_label(
    event_type: object,
    expected_label: str,
) -> None:
    from async_scholar.ui.event_timeline import event_to_timeline_model

    model = event_to_timeline_model(
        {"event_type": event_type, "detected_at": 4, "confidence": 0.1}
    )

    assert model.event_type_label == expected_label
    assert "private" not in model.event_type_label.lower()
    assert "token" not in model.event_type_label.lower()


@pytest.mark.parametrize(
    ("detected_at", "confidence"),
    [
        (-1, 0.7),
        (inf, 0.7),
        (nan, 0.7),
        ("C:\\private\\timeline.txt", "token-confidence"),
        (3, -0.1),
        (3, inf),
        (3, nan),
        (3, 101),
        (3, True),
    ],
)
def test_untrusted_numeric_and_confidence_values_normalize_safely(
    detected_at: object,
    confidence: object,
) -> None:
    from async_scholar.ui.event_timeline import event_to_timeline_model

    model = event_to_timeline_model(
        {
            "event_type": "attendance_prompt",
            "detected_at": detected_at,
            "confidence": confidence,
        }
    )

    formatted = f"{model.detected_time_label} {model.confidence_label}".lower()
    assert "nan" not in formatted
    assert "inf" not in formatted
    assert "private" not in formatted
    assert "token" not in formatted
    if detected_at in {-1, inf} or isinstance(detected_at, str):
        assert model.detected_time_label == "unknown time"
    if confidence in {-0.1, inf, 101, True} or isinstance(confidence, str):
        assert model.confidence_label == "unknown confidence"


def test_empty_timeline_rendering() -> None:
    from async_scholar.ui.event_timeline import render_event_timeline_view

    fake_ui = FakeUI()
    view = render_event_timeline_view(lambda: [], ui=fake_ui)

    assert view.events == []
    assert "No events yet" in fake_ui.rendered_text()


def test_callback_wiring_refreshes_from_fake_source_and_fake_nicegui() -> None:
    from async_scholar.ui.event_timeline import render_event_timeline_view

    calls = 0

    def source() -> list[dict[str, object]]:
        nonlocal calls
        calls += 1
        return [
            {
                "event_type": "attendance_prompt" if calls == 1 else "quiz",
                "detected_at": calls,
                "confidence": 0.25 * calls,
                "message": f"private-message-{calls}",
            }
        ]

    fake_ui = FakeUI()
    view = render_event_timeline_view(source, ui=fake_ui)

    assert calls == 1
    assert view.events[0].event_type_label == "Attendance prompt"
    assert "Attendance prompt - 1s - 25% confidence" in fake_ui.rendered_text()

    refresh_button = fake_ui.buttons[0]
    assert callable(refresh_button.on_click)
    refresh_button.on_click()

    rendered = "\n".join(fake_ui.rendered_text())
    assert calls == 2
    assert view.events[0].event_type_label == "Quiz"
    assert "Quiz - 2s - 50% confidence" in rendered
    assert "Attendance prompt - 1s - 25% confidence" not in rendered
    assert "private-message-1" not in rendered
    assert "private-message-2" not in rendered
