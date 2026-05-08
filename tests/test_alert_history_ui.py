from __future__ import annotations

import importlib
import inspect
import json
import subprocess
import sys
from dataclasses import dataclass

FORBIDDEN_SOURCE_REFERENCES = (
    "async_scholar.demo",
    "run_fixture_demo",
    "alerts.log",
    "alert_dispatch",
    "desktop_notifier",
    "telegram_notifier",
    "artifacts",
    "audio",
    "stt",
    "vad",
    "scheduler",
    "browser",
    "fastapi",
)


def test_alert_history_module_import_is_safe() -> None:
    for module_name in tuple(sys.modules):
        if module_name == "async_scholar.ui" or module_name.startswith(
            "async_scholar.ui."
        ):
            sys.modules.pop(module_name)
    before_modules = set(sys.modules)

    module = importlib.import_module("async_scholar.ui.alert_history")
    ui_package = importlib.import_module("async_scholar.ui")

    loaded_modules = set(sys.modules) - before_modules
    forbidden_loaded = {
        name
        for name in loaded_modules
        if name == "fastapi"
        or name.startswith(
            (
                "fastapi.",
                "async_scholar.demo",
                "async_scholar.alert_dispatch",
                "async_scholar.desktop_notifier",
                "async_scholar.telegram_notifier",
                "async_scholar.artifacts",
                "async_scholar.audio",
                "async_scholar.stt",
            )
        )
    }
    assert forbidden_loaded == set()

    source = inspect.getsource(module).casefold()
    for forbidden in FORBIDDEN_SOURCE_REFERENCES:
        assert forbidden not in source

    package_source = inspect.getsource(ui_package).casefold()
    for forbidden in ("fastapi", "run_fixture_demo", "alerts.log"):
        assert forbidden not in package_source

    code = """
import importlib
import json
import sys

before_modules = set(sys.modules)
importlib.import_module("async_scholar.ui.alert_history")
loaded_modules = set(sys.modules) - before_modules
forbidden_loaded = sorted(
    name
    for name in loaded_modules
    if name == "fastapi"
    or name.startswith(
        (
            "fastapi.",
            "async_scholar.demo",
            "async_scholar.alert_dispatch",
            "async_scholar.desktop_notifier",
            "async_scholar.telegram_notifier",
            "async_scholar.artifacts",
            "async_scholar.audio",
            "async_scholar.stt",
        )
    )
)
print(json.dumps(forbidden_loaded))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(completed.stdout) == []


@dataclass(frozen=True)
class ObjectAlert:
    severity: str
    status: str
    confirmation_required: bool
    token: str = "secret-token"


def test_alert_history_normalization_and_formatting_uses_safe_fields() -> None:
    module = _alert_history_module()
    model = module.alert_to_history_model(
        {
            "severity": "urgent",
            "status": "pending",
            "confirmation_required": True,
            "title": "Raw title with token",
            "message": "Raw message with transcript",
        }
    )

    assert model == module.AlertHistoryAlertModel(
        title="Urgent alert",
        message="Review confirmation before acting.",
        severity_label="Severity: Urgent",
        status_label="Status: Pending",
        confirmation_required_label="Confirmation required",
    )
    assert module.format_alert_history_item(model) == (
        "Urgent alert | Review confirmation before acting. | Severity: Urgent | "
        "Status: Pending | Confirmation required"
    )

    object_model = module.normalize_alert_history_alerts(
        [ObjectAlert(severity="info", status="delivered", confirmation_required=False)]
    )
    assert object_model == (
        module.AlertHistoryAlertModel(
            title="Alert",
            message="No confirmation is required.",
            severity_label="Severity: Info",
            status_label="Status: Delivered",
            confirmation_required_label="No confirmation required",
        ),
    )


def test_private_fields_are_omitted_from_model_and_rendered_text() -> None:
    module = _alert_history_module()
    private_values = {
        "provider_result": "telegram bot token provider result",
        "retry_decisions": "retry with private path",
        "alert_id": "alert-123",
        "session_id": "session-123",
        "event_id": "event-123",
        "transcript_text": "student said the private attendance phrase",
        "private_path": r"C:\Users\person\class\lecture.mp4",
        "raw_audio_path": r"C:\audio\lecture.wav",
        "token": "secret-token",
        "cookie": "session-cookie",
        "auth_state": "browser-auth-state",
        "browser_profile": "profile-data",
        "model_path": r"C:\models\private-model.bin",
        "generated_media": r"C:\media\generated.png",
        "exception": "raw exception text",
        "traceback": "Traceback (most recent call last)",
        "request_url": "https://example.test/private",
        "stdout": "stdout secret",
        "stderr": "stderr secret",
        "metadata": {"unknown": "unknown metadata"},
        "title": "sensitive title",
        "message": "sensitive alert message",
    }
    alert = {
        "severity": "high",
        "status": "sent",
        "confirmation_required": False,
        **private_values,
    }

    model = module.alert_to_history_model(alert)
    model_text = " ".join(str(value) for value in vars(model).values())
    for private_value in private_values.values():
        assert str(private_value) not in model_text

    fake_ui = FakeNiceGui()
    module.render_alert_history_view(source=StaticAlertSource([alert]), ui=fake_ui)
    rendered_text = " ".join(fake_ui.labels)
    for private_value in private_values.values():
        assert str(private_value) not in rendered_text


def test_unknown_severity_and_status_are_normalized() -> None:
    module = _alert_history_module()
    model = module.alert_to_history_model(
        {
            "severity": "https://example.test/token",
            "status": "raw-provider-result-with-secret",
            "requires_confirmation": "unknown-secret-value",
        }
    )

    assert model.severity_label == "Severity: Unknown"
    assert model.status_label == "Status: Unknown"
    assert model.confirmation_required_label == "Confirmation status unknown"
    assert "https://example.test/token" not in module.format_alert_history_item(model)
    assert "raw-provider-result-with-secret" not in module.format_alert_history_item(
        model
    )


def test_empty_history_rendering() -> None:
    module = _alert_history_module()
    fake_ui = FakeNiceGui()

    view = module.render_alert_history_view(source=StaticAlertSource([]), ui=fake_ui)

    assert view.alerts == ()
    assert "No alerts yet" in fake_ui.labels


def test_refresh_callback_uses_fake_source_and_fake_nicegui() -> None:
    module = _alert_history_module()
    source = ChangingAlertSource(
        [
            [{"severity": "info", "status": "pending", "confirmation_required": False}],
            [
                {
                    "severity": "urgent",
                    "status": "confirmed",
                    "confirmation_required": True,
                }
            ],
        ]
    )
    fake_ui = FakeNiceGui()

    view = module.render_alert_history_view(source=source, ui=fake_ui)

    assert source.calls == 1
    assert view.alerts[0].severity_label == "Severity: Info"
    assert len(fake_ui.buttons) == 1

    fake_ui.buttons[0].on_click()

    assert source.calls == 2
    assert view.alerts[0].severity_label == "Severity: Urgent"
    assert view.alerts[0].status_label == "Status: Confirmed"


def _alert_history_module():
    return importlib.import_module("async_scholar.ui.alert_history")


class StaticAlertSource:
    def __init__(self, alerts: list[object]) -> None:
        self._alerts = alerts

    def alerts(self) -> list[object]:
        return self._alerts


class ChangingAlertSource:
    def __init__(self, alert_sets: list[list[object]]) -> None:
        self._alert_sets = alert_sets
        self.calls = 0

    def alerts(self) -> list[object]:
        index = min(self.calls, len(self._alert_sets) - 1)
        self.calls += 1
        return self._alert_sets[index]


class FakeElement:
    def __init__(self, ui: FakeNiceGui, *, on_click: object | None = None) -> None:
        self._ui = ui
        self.on_click = on_click
        self.clear_count = 0

    def __enter__(self) -> FakeElement:
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def classes(self, *_classes: str) -> FakeElement:
        return self

    def props(self, *_props: str) -> FakeElement:
        return self

    def clear(self) -> None:
        self.clear_count += 1
        self._ui.clear_count += 1


class FakeNiceGui:
    def __init__(self) -> None:
        self.labels: list[str] = []
        self.buttons: list[FakeElement] = []
        self.clear_count = 0

    def column(self) -> FakeElement:
        return FakeElement(self)

    def label(self, text: str) -> FakeElement:
        self.labels.append(text)
        return FakeElement(self)

    def button(self, **kwargs: object) -> FakeElement:
        element = FakeElement(self, on_click=kwargs.get("on_click"))
        self.buttons.append(element)
        return element
