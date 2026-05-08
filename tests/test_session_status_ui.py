from __future__ import annotations

import importlib
import inspect
import sys
from dataclasses import asdict, dataclass
from types import SimpleNamespace
from typing import Any


def test_session_status_module_import_is_pipeline_safe() -> None:
    sys.modules.pop("async_scholar.ui.session_status", None)
    sys.modules.pop("async_scholar.demo", None)

    module = importlib.import_module("async_scholar.ui.session_status")

    assert "async_scholar.demo" not in sys.modules
    source = inspect.getsource(module)
    assert "run_fixture_demo" not in source
    assert "fastapi" not in source.lower()


def test_snapshot_to_status_model_uses_only_safe_fields() -> None:
    from async_scholar.ui.session_status import (
        SAFE_STATUS_FIELDS,
        format_status_model,
        snapshot_to_status_model,
    )

    snapshot = SimpleNamespace(
        run_status="completed",
        source_kind="fixture_demo",
        segment_count=5,
        event_count=2,
        artifact_paths=("C:\\private\\session\\transcript.jsonl",),
        transcript_text="private transcript words",
        raw_exception="Traceback with token",
        model_path="C:\\models\\private-model",
        browser_auth_state="cookie=value",
        generated_media="lecture.mp4",
    )

    model = snapshot_to_status_model(snapshot)
    rendered_rows = format_status_model(model)
    rendered_text = " ".join(row.value for row in rendered_rows)

    assert tuple(asdict(model)) == SAFE_STATUS_FIELDS
    assert model.run_status == "completed"
    assert model.source_kind == "fixture_demo"
    assert model.segment_count == 5
    assert model.event_count == 2
    assert "private" not in rendered_text.lower()
    assert "traceback" not in rendered_text.lower()
    assert "cookie" not in rendered_text.lower()
    assert "model" not in rendered_text.lower()
    assert "lecture.mp4" not in rendered_text


def test_status_formatting_normalizes_untrusted_values() -> None:
    from async_scholar.ui.session_status import (
        format_status_model,
        snapshot_to_status_model,
    )

    snapshot = {
        "run_status": "failed C:\\private\\traceback",
        "source_kind": "C:\\private\\source.wav",
        "segment_count": -3,
        "event_count": "not a count",
        "alert_payload": "secret",
    }

    model = snapshot_to_status_model(snapshot)
    rendered_text = " ".join(row.value for row in format_status_model(model))

    assert model.run_status == "unknown"
    assert model.source_kind == "unknown"
    assert model.segment_count == 0
    assert model.event_count == 0
    assert "private" not in rendered_text.lower()
    assert "secret" not in rendered_text.lower()


def test_rendered_callbacks_are_wired_to_worker_surface(monkeypatch: Any) -> None:
    from async_scholar.ui import session_status

    fake_ui = FakeUi()
    worker = FakeWorker()
    monkeypatch.setattr(session_status, "ui", fake_ui)

    view = session_status.render_session_status_view(worker)
    fake_ui.click("Start")
    fake_ui.click("Stop")
    fake_ui.click("Refresh")

    assert worker.calls == ["status", "start", "stop", "status"]
    assert view.model.run_status == "stopped"
    assert fake_ui.label_values_by_text["Run status"].text == "Run status"
    assert fake_ui.value_labels["run_status"].text == "Stopped"
    assert fake_ui.value_labels["source_kind"].text == "Fixture demo"
    assert fake_ui.value_labels["segment_count"].text == "3"
    assert fake_ui.value_labels["event_count"].text == "1"


@dataclass(frozen=True)
class FakeSnapshot:
    run_status: str
    source_kind: str = "fixture_demo"
    segment_count: int = 3
    event_count: int = 1
    artifact_paths: tuple[str, ...] = ("C:\\private\\artifact.jsonl",)


class FakeWorker:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self._snapshot = FakeSnapshot("idle")

    def status(self) -> FakeSnapshot:
        self.calls.append("status")
        return self._snapshot

    def start(self) -> FakeSnapshot:
        self.calls.append("start")
        self._snapshot = FakeSnapshot("running")
        return self._snapshot

    def stop(self) -> FakeSnapshot:
        self.calls.append("stop")
        self._snapshot = FakeSnapshot("stopped")
        return self._snapshot


class FakeUi:
    def __init__(self) -> None:
        self.buttons: dict[str, FakeElement] = {}
        self.label_values_by_text: dict[str, FakeElement] = {}
        self.value_labels: dict[str, FakeElement] = {}
        self._next_value_field: str | None = None

    def column(self) -> FakeElement:
        return FakeElement()

    def grid(self, *, columns: int) -> FakeElement:
        assert columns == 2
        return FakeElement()

    def row(self) -> FakeElement:
        return FakeElement()

    def label(self, text: str = "") -> FakeElement:
        element = FakeElement(text=text)
        if text in {"Run status", "Source kind", "Segments", "Events"}:
            self.label_values_by_text[text] = element
            self._next_value_field = {
                "Run status": "run_status",
                "Source kind": "source_kind",
                "Segments": "segment_count",
                "Events": "event_count",
            }[text]
        elif self._next_value_field is not None:
            self.value_labels[self._next_value_field] = element
            self._next_value_field = None
        return element

    def button(
        self,
        text: str,
        *,
        icon: str,
        on_click: Any,
    ) -> FakeElement:
        element = FakeElement(text=text, icon=icon, on_click=on_click)
        self.buttons[text] = element
        return element

    def click(self, text: str) -> None:
        on_click = self.buttons[text].on_click
        assert on_click is not None
        on_click()


class FakeElement:
    def __init__(
        self,
        text: str = "",
        *,
        icon: str | None = None,
        on_click: Any = None,
    ) -> None:
        self.text = text
        self.icon = icon
        self.on_click = on_click

    def __enter__(self) -> FakeElement:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def classes(self, value: str) -> FakeElement:
        assert value
        return self

    def set_text(self, value: str) -> None:
        self.text = value
