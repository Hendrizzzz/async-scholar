from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from async_scholar.fake_meeting import build_fake_meeting_fixture
from async_scholar.fake_meeting_session import inspect_fake_meeting_session_html

_SKIP_REASON = "managed Chromium unavailable for local synthetic smoke"


def _managed_chromium_executable_path(playwright: Any) -> Path:
    executable_path = Path(playwright.chromium.executable_path)
    if not executable_path.exists() or any(
        part.startswith("chromium_headless_shell") for part in executable_path.parts
    ):
        pytest.skip(_SKIP_REASON)
    return executable_path


def _launch_managed_chromium(playwright: Any) -> Any:
    executable_path = _managed_chromium_executable_path(playwright)

    try:
        return playwright.chromium.launch(
            executable_path=str(executable_path),
            headless=True,
        )
    except PlaywrightError:
        pytest.skip(_SKIP_REASON)


def test_local_synthetic_meeting_html_can_be_inspected_with_playwright() -> None:
    fixture = build_fake_meeting_fixture(
        fixture_id="alpha_fixture",
        title="Synthetic Seminar",
        state="live",
        caption_status="ready",
        participants=("Synthetic Learner", "Synthetic Instructor"),
    )
    html = fixture.to_html_document()

    with sync_playwright() as playwright:
        browser = _launch_managed_chromium(playwright)
        try:
            context = browser.new_context()
            try:
                page = context.new_page()
                page.set_content(html, wait_until="domcontentloaded")

                assert page.url == "about:blank"
                assert (
                    page.locator(
                        '[data-async-scholar-session-awareness="synthetic-local-only"]'
                    ).count()
                    == 1
                )
                assert (
                    page.locator("[data-async-scholar-meeting-state]").inner_text()
                    == "live"
                )
                assert (
                    page.locator("[data-async-scholar-caption-state]").inner_text()
                    == "ready"
                )
                assert (
                    page.locator("body").get_attribute("data-async-scholar-fixture-id")
                    == "alpha_fixture"
                )
                assert page.locator(
                    "[data-async-scholar-participant]"
                ).all_inner_texts() == [
                    "Synthetic Instructor",
                    "Synthetic Learner",
                ]
                snapshot = inspect_fake_meeting_session_html(page.content())
                assert snapshot.snapshot_kind == "synthetic_fake_meeting_session"
                assert snapshot.fixture_id == "alpha_fixture"
                assert snapshot.state == "live"
                assert snapshot.caption_status == "ready"
                assert snapshot.participant_count == 2
                assert snapshot.participants == (
                    "Synthetic Instructor",
                    "Synthetic Learner",
                )
            finally:
                context.close()
        finally:
            browser.close()
