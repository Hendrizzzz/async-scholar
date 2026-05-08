from __future__ import annotations

import importlib
import json
import subprocess
import sys
import textwrap
from dataclasses import asdict


def _archive_module():
    return importlib.import_module("async_scholar.ui.archive_browser")


class FakeElement:
    def __init__(
        self,
        ui: FakeUI,
        kind: str,
        text: str | None = None,
        on_click=None,
    ) -> None:
        self.ui = ui
        self.kind = kind
        self.text = text
        self.on_click = on_click
        self.children: list[FakeElement] = []

    def __enter__(self) -> FakeElement:
        self.ui._stack.append(self)
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.ui._stack.pop()

    def classes(self, value: str) -> FakeElement:
        return self

    def props(self, value: str) -> FakeElement:
        return self

    def clear(self) -> None:
        self.children.clear()


class FakeUI:
    def __init__(self) -> None:
        self.roots: list[FakeElement] = []
        self._stack: list[FakeElement] = []

    def column(self) -> FakeElement:
        return self._element("column")

    def row(self) -> FakeElement:
        return self._element("row")

    def card(self) -> FakeElement:
        return self._element("card")

    def label(self, text: object) -> FakeElement:
        return self._element("label", str(text))

    def button(self, text: str, *, on_click=None) -> FakeElement:
        return self._element("button", text, on_click)

    @property
    def texts(self) -> list[str]:
        return [element.text for element in self._walk() if element.text is not None]

    @property
    def buttons(self) -> list[FakeElement]:
        return [element for element in self._walk() if element.kind == "button"]

    def _element(
        self,
        kind: str,
        text: str | None = None,
        on_click=None,
    ) -> FakeElement:
        element = FakeElement(self, kind, text, on_click)
        if self._stack:
            self._stack[-1].children.append(element)
        else:
            self.roots.append(element)
        return element

    def _walk(self) -> list[FakeElement]:
        elements: list[FakeElement] = []
        stack = list(reversed(self.roots))
        while stack:
            element = stack.pop()
            elements.append(element)
            stack.extend(reversed(element.children))
        return elements


class FakeSource:
    def __init__(self, batches: list[list[dict[str, object]]]) -> None:
        self._batches = batches
        self.calls = 0

    def items(self) -> list[dict[str, object]]:
        index = min(self.calls, len(self._batches) - 1)
        self.calls += 1
        return self._batches[index]


def _fresh_process_import_check(module_name: str) -> list[str]:
    code = textwrap.dedent(
        f"""
        import importlib
        import json
        import sys

        before = set(sys.modules)
        importlib.import_module({module_name!r})
        loaded = set(sys.modules) - before
        prefixes = (
            "fastapi.",
            "nicegui.",
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
            name
            for name in loaded
            if name in {{"fastapi", "nicegui"}} or name.startswith(prefixes)
        )
        print(json.dumps(forbidden))
        raise SystemExit(bool(forbidden))
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return json.loads(completed.stdout)


def test_archive_browser_module_import_is_safe() -> None:
    assert _fresh_process_import_check("async_scholar.ui.archive_browser") == []


def test_ui_package_lazy_export_is_safe() -> None:
    code = textwrap.dedent(
        """
        import importlib
        import json
        import sys

        package = importlib.import_module("async_scholar.ui")
        assert "render_archive_browser_view" in package.__all__
        before = set(sys.modules)
        render = package.render_archive_browser_view
        loaded = set(sys.modules) - before
        prefixes = (
            "fastapi.",
            "nicegui.",
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
            name
            for name in loaded
            if name in {"fastapi", "nicegui"} or name.startswith(prefixes)
        )
        print(json.dumps({"callable": callable(render), "forbidden": forbidden}))
        raise SystemExit(bool(forbidden))
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads(completed.stdout) == {"callable": True, "forbidden": []}


def test_source_based_normalization_and_formatting() -> None:
    archive = _archive_module()

    [model] = archive.normalize_archive_browser_items(
        [
            {
                "title": "Week 4 participation review",
                "reviewer_summary": "Three useful participation moments are ready.",
                "reviewer_status": "available",
                "event_count": "3",
                "alert_count": 1,
                "updated_time_label": "Updated May 8, 2026 09:30",
                "artifact_path": r"C:\\private\\reviewer.md",
            }
        ]
    )

    assert model.title == "Week 4 participation review"
    assert model.reviewer_excerpt == "Three useful participation moments are ready."
    assert model.reviewer_status_label == "Reviewer available"
    assert model.event_count == 3
    assert model.alert_count == 1
    assert model.updated_time_label == "Updated May 8, 2026 09:30"
    assert archive.format_archive_browser_item(model) == (
        "Week 4 participation review | Reviewer available | Events: 3 | "
        "Alerts: 1 | Updated May 8, 2026 09:30 | "
        "Three useful participation moments are ready."
    )


def test_private_fields_are_omitted_from_model_and_rendered_text() -> None:
    archive = _archive_module()
    item = {
        "title": "Discrete Math review",
        "reviewer_excerpt": "Two flagged prompts need a look.",
        "reviewer_available": True,
        "event_count": 2,
        "alert_count": 1,
        "updated_time_label": "Updated recently",
        "artifact_path": r"C:\\Users\\student\\data\\sessions\\reviewer.md",
        "reviewer_path": "data/sessions/private/reviewer.md",
        "transcript_path": "data/sessions/private/transcript.jsonl",
        "audio_file": "debug/private/microphone.wav",
        "token": "secret-token",
        "cookies": "session-cookie",
        "traceback": "Traceback (most recent call last): private",
        "metadata": {"raw": "provider blob"},
    }

    [model] = archive.normalize_archive_browser_items([item])
    model_dict = asdict(model)
    rendered_ui = FakeUI()
    archive.render_archive_browser_view(FakeSource([[item]]), ui=rendered_ui)
    rendered_text = "\n".join(rendered_ui.texts)

    assert set(model_dict) == set(archive.SAFE_ARCHIVE_BROWSER_FIELDS)
    for private_value in (
        "C:",
        "data/sessions",
        "reviewer.md",
        "transcript.jsonl",
        "microphone.wav",
        "secret-token",
        "session-cookie",
        "Traceback",
        "provider blob",
    ):
        assert private_value not in str(model_dict)
        assert private_value not in rendered_text
    assert "Discrete Math review" in rendered_text
    assert "Two flagged prompts need a look." in rendered_text


def test_unknown_untrusted_values_normalize_to_safe_defaults() -> None:
    archive = _archive_module()

    models = archive.normalize_archive_browser_items(
        [
            {
                "title": r"\\\\server\\share\\session",
                "reviewer_excerpt": "/home/student/session/reviewer",
                "reviewer_status": "ship everything",
                "event_count": -7,
                "alert_count": "not a count",
                "updated_time_label": "sessions/private/reviewer",
            }
        ]
    )
    [model] = models

    assert model.title == "Untitled session"
    assert model.reviewer_excerpt == ""
    assert model.reviewer_status_label == "Reviewer unknown"
    assert model.event_count == 0
    assert model.alert_count == 0
    assert model.updated_time_label == "Updated unknown"


def test_provider_iteration_errors_fail_closed() -> None:
    archive = _archive_module()

    class ExplodingItems:
        def __iter__(self):
            raise RuntimeError(r"C:\\private\\reviewer.md")

    class ExplodingSource:
        def items(self):
            return ExplodingItems()

    rendered_ui = FakeUI()
    view = archive.render_archive_browser_view(ExplodingSource(), ui=rendered_ui)

    rendered_text = "\n".join(rendered_ui.texts)

    assert view.items == ()
    assert r"C:\\private\\reviewer.md" not in rendered_text
    assert "No archived sessions yet." in rendered_text


def test_empty_archive_rendering() -> None:
    archive = _archive_module()
    rendered_ui = FakeUI()

    view = archive.render_archive_browser_view(FakeSource([[]]), ui=rendered_ui)

    assert view.items == ()
    assert "No archived sessions yet." in rendered_ui.texts


def test_reviewer_excerpt_is_bounded() -> None:
    archive = _archive_module()
    excerpt = "summary " * 80

    [model] = archive.normalize_archive_browser_items(
        [
            {
                "title": "Long review",
                "reviewer_excerpt": excerpt,
                "reviewer_status": "ready",
            }
        ]
    )

    assert len(model.reviewer_excerpt) <= archive.REVIEWER_EXCERPT_MAX_CHARS
    assert model.reviewer_excerpt.endswith("...")
    assert (
        "summary summary summary summary summary summary summary summary"
        in model.reviewer_excerpt
    )
    assert excerpt.rstrip() not in model.reviewer_excerpt


def test_refresh_callback_uses_fake_source_and_ui() -> None:
    archive = _archive_module()
    rendered_ui = FakeUI()
    source = FakeSource(
        [
            [{"title": "First session", "reviewer_status": "missing"}],
            [
                {
                    "title": "Second session",
                    "reviewer_status": "available",
                    "event_count": 4,
                }
            ],
        ]
    )

    view = archive.render_archive_browser_view(source, ui=rendered_ui)
    assert source.calls == 1
    assert [item.title for item in view.items] == ["First session"]

    [refresh_button] = rendered_ui.buttons
    refresh_button.on_click()

    assert source.calls == 2
    assert [item.title for item in view.items] == ["Second session"]
    rendered_text = "\n".join(rendered_ui.texts)
    assert "Second session" in rendered_text
    assert "Events: 4" in rendered_text
    assert "First session" not in rendered_text
