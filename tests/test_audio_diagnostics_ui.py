from __future__ import annotations

import json
import subprocess
import sys

FORBIDDEN_IMPORT_CHECK = """
import importlib
import json
import sys

before = set(sys.modules)
{body}
loaded = set(sys.modules) - before
prefixes = (
    "fastapi.",
    "async_scholar.demo",
    "async_scholar.audio",
    "async_scholar.stt",
    "async_scholar.artifacts",
    "async_scholar.alert_dispatch",
    "async_scholar.desktop_notifier",
    "async_scholar.telegram_notifier",
    "async_scholar.scheduler",
    "async_scholar.browser",
)
forbidden = sorted(
    name for name in loaded if name == "fastapi" or name.startswith(prefixes)
)
print(json.dumps(forbidden))
raise SystemExit(bool(forbidden))
"""


class FakeLabel:
    def __init__(self, text: str) -> None:
        self.text = text

    def set_text(self, text: str) -> None:
        self.text = text


class FakeButton:
    def __init__(self, text: str, on_click: object | None) -> None:
        self.text = text
        self.on_click = on_click

    def click(self) -> object | None:
        if callable(self.on_click):
            return self.on_click()
        return None


class FakeUI:
    def __init__(self) -> None:
        self.labels: list[FakeLabel] = []
        self.buttons: list[FakeButton] = []

    def label(self, text: str) -> FakeLabel:
        label = FakeLabel(text)
        self.labels.append(label)
        return label

    def button(self, text: str, *, on_click: object | None = None) -> FakeButton:
        button = FakeButton(text, on_click)
        self.buttons.append(button)
        return button

    def rendered_text(self) -> str:
        labels = [label.text for label in self.labels]
        buttons = [button.text for button in self.buttons]
        return " ".join([*labels, *buttons])


class FakeDiagnosticsSource:
    def __init__(self, *snapshots: object | None) -> None:
        self._snapshots = list(snapshots)
        self.calls = 0

    def diagnostics(self) -> object | None:
        self.calls += 1
        if not self._snapshots:
            return None
        index = min(self.calls - 1, len(self._snapshots) - 1)
        return self._snapshots[index]


def test_audio_diagnostics_module_import_is_safe() -> None:
    result = _run_import_check(
        "importlib.import_module('async_scholar.ui.audio_diagnostics')"
    )

    assert result == []


def test_ui_lazy_export_import_is_safe() -> None:
    body = """
ui_module = importlib.import_module("async_scholar.ui")
assert "render_audio_diagnostics_view" in dir(ui_module)
getattr(ui_module, "render_audio_diagnostics_view")
"""
    result = _run_import_check(body)

    assert result == []


def test_source_based_normalization_and_formatting() -> None:
    from async_scholar.ui.audio_diagnostics import (
        diagnostics_to_audio_model,
        format_audio_diagnostics_model,
    )

    snapshot = {
        "status": "monitoring",
        "sample_rate_hz": 48_000,
        "channels": 2,
        "peak_level": 0.375,
        "rms_level": 0.125,
        "clipping": False,
        "silence": True,
        "chunk_count": 42,
        "elapsed_seconds": 3.25,
    }

    model = diagnostics_to_audio_model(snapshot)

    assert format_audio_diagnostics_model(model) == (
        "Status: Monitoring",
        "Sample rate: 48000 Hz",
        "Channels: 2",
        "Peak: 37.5%",
        "RMS: 12.5%",
        "Clipping: no",
        "Silence: yes",
        "Chunks: 42",
        "Elapsed: 3.2s",
    )


def test_private_fields_are_omitted_from_model_and_rendered_text() -> None:
    from async_scholar.ui.audio_diagnostics import (
        diagnostics_to_audio_model,
        format_audio_diagnostics_model,
        render_audio_diagnostics_view,
    )

    private_values = [
        "Blue Yeti Private",
        "device-id-123",
        "C:\\Users\\student\\class.wav",
        "secret-token",
        "private transcript text",
        "Traceback (most recent call last)",
        "model-cache-path",
        "browser-cookie",
    ]
    snapshot = {
        "status": "ready",
        "sample_rate_hz": 16_000,
        "channels": 1,
        "peak_level": 0.1,
        "rms_level": 0.05,
        "clipping": False,
        "silence": False,
        "chunk_count": 2,
        "elapsed_seconds": 1.0,
        "device_name": private_values[0],
        "device_id": private_values[1],
        "raw_audio_path": private_values[2],
        "token": private_values[3],
        "transcript_text": private_values[4],
        "traceback": private_values[5],
        "model_path": private_values[6],
        "cookie": private_values[7],
        "raw_pcm": b"not renderable",
        "provider_blob": {"path": private_values[2]},
    }

    model = diagnostics_to_audio_model(snapshot)
    rendered_model = " ".join(format_audio_diagnostics_model(model))
    ui = FakeUI()
    render_audio_diagnostics_view(FakeDiagnosticsSource(snapshot), ui=ui)
    rendered_ui = ui.rendered_text()

    for private_value in private_values:
        assert private_value not in rendered_model
        assert private_value not in rendered_ui


def test_unknown_and_untrusted_values_normalize_to_controlled_output() -> None:
    from async_scholar.ui.audio_diagnostics import (
        diagnostics_to_audio_model,
        format_audio_diagnostics_model,
    )

    snapshot = {
        "status": "C:\\Users\\student\\microphone",
        "sample_rate_hz": -48_000,
        "channels": "two",
        "peak_level": 5.0,
        "rms_level": "token-like",
        "clipping": "yes",
        "silence": object(),
        "chunk_count": -1,
        "elapsed_seconds": float("inf"),
    }

    model = diagnostics_to_audio_model(snapshot)

    assert format_audio_diagnostics_model(model) == (
        "Status: Unknown",
        "Sample rate: unknown",
        "Channels: unknown",
        "Peak: unknown",
        "RMS: unknown",
        "Clipping: unknown",
        "Silence: unknown",
        "Chunks: unknown",
        "Elapsed: unknown",
    )


def test_empty_diagnostics_render_safely() -> None:
    from async_scholar.ui.audio_diagnostics import render_audio_diagnostics_view

    ui = FakeUI()
    view = render_audio_diagnostics_view(FakeDiagnosticsSource({}), ui=ui)

    assert view.model.status_label == "Status: Unavailable"
    assert "Sample rate: unknown" in ui.rendered_text()
    assert "Channels: unknown" in ui.rendered_text()
    assert len(ui.buttons) == 1


def test_refresh_callback_uses_injected_source_only() -> None:
    from async_scholar.ui.audio_diagnostics import render_audio_diagnostics_view

    source = FakeDiagnosticsSource(
        {"status": "idle", "chunk_count": 1},
        {"status": "active", "chunk_count": 2},
    )
    ui = FakeUI()
    view = render_audio_diagnostics_view(source, ui=ui)

    assert source.calls == 1
    assert view.model.status_label == "Status: Idle"
    assert "Chunks: 1" in ui.rendered_text()

    ui.buttons[0].click()

    assert source.calls == 2
    assert view.model.status_label == "Status: Monitoring"
    assert "Chunks: 2" in ui.rendered_text()
    assert "Chunks: 1" not in ui.rendered_text()


def _run_import_check(body: str) -> list[str]:
    command = [sys.executable, "-c", FORBIDDEN_IMPORT_CHECK.format(body=body)]
    result = subprocess.run(command, capture_output=True, check=True, text=True)
    return json.loads(result.stdout)
