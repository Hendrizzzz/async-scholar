from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from async_scholar.fake_meeting import build_fake_meeting_fixture

_SKIP_REASON = "managed Chromium unavailable for local synthetic smoke"


def _launch_managed_chromium(playwright: Any) -> Any:
    executable_path = Path(playwright.chromium.executable_path)
    if not executable_path.exists():
        pytest.skip(_SKIP_REASON)

    try:
        return playwright.chromium.launch(headless=True)
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
            finally:
                context.close()
        finally:
            browser.close()
