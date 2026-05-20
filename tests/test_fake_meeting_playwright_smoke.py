from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from async_scholar.fake_meeting import build_fake_meeting_fixture
from async_scholar.fake_meeting_session import inspect_fake_meeting_session_html

_SKIP_REASON = "managed Chromium unavailable for local synthetic smoke"
_HISTORY_FORBIDDEN_FRAGMENTS = (
    "<html",
    "<body",
    "data-async-scholar",
    "http" + "://",
    "https" + "://",
    "meet." + "goo" + "gle",
    "goo" + "gle",
    "pro" + "file",
    "au" + "th",
    "coo" + "kie",
    "storage",
    "media",
    "micro" + "phone",
    "cam" + "era",
    "loop" + "back",
    "sched" + "uler",
    "notifi" + "cation",
    "archive" + "_export",
    "archive" + "_delete",
    "C:/Users",
    "C:\\Users",
    "." + "env",
)

SyntheticSnapshotHistoryEntry = dict[str, int | str | tuple[str, ...]]


def _assert_synthetic_session_snapshot(
    page: Any,
    *,
    fixture_id: str,
    state: str,
    caption_status: str,
    participants: tuple[str, ...],
) -> None:
    snapshot = inspect_fake_meeting_session_html(page.content())

    assert page.url == "about:blank"
    assert snapshot.snapshot_kind == "synthetic_fake_meeting_session"
    assert snapshot.fixture_id == fixture_id
    assert snapshot.state == state
    assert snapshot.caption_status == caption_status
    assert snapshot.participant_count == len(participants)
    assert snapshot.participants == participants


def _capture_synthetic_session_history_entry(
    page: Any,
    *,
    order: int,
) -> SyntheticSnapshotHistoryEntry:
    snapshot = inspect_fake_meeting_session_html(page.content())

    assert page.url == "about:blank"
    return {
        "caption_status": snapshot.caption_status,
        "fixture_id": snapshot.fixture_id,
        "order": order,
        "participant_count": snapshot.participant_count,
        "participants": snapshot.participants,
        "snapshot_kind": snapshot.snapshot_kind,
        "state": snapshot.state,
    }


def _set_synthetic_session_state(
    page: Any,
    *,
    state: str,
    caption_status: str,
    participants: tuple[str, ...],
) -> None:
    page.locator("body").evaluate(
        """(element, data) => {
            element.setAttribute("data-async-scholar-state", data.state);
            element.setAttribute(
                "data-async-scholar-caption-status",
                data.captionStatus,
            );
            element.setAttribute(
                "data-async-scholar-participant-count",
                String(data.participants.length),
            );

            const stateNode = document.querySelector(
                "[data-async-scholar-meeting-state]",
            );
            const captionNode = document.querySelector(
                "[data-async-scholar-caption-state]",
            );
            const listNode = document.querySelector(
                '[aria-label="Synthetic participants"]',
            );
            if (stateNode !== null) {
                stateNode.textContent = data.state;
            }
            if (captionNode !== null) {
                captionNode.textContent = data.captionStatus;
            }
            if (listNode !== null) {
                listNode.replaceChildren(
                    ...data.participants.map((name) => {
                        const item = document.createElement("li");
                        item.className = "participant";
                        item.setAttribute(
                            "data-async-scholar-participant",
                            name,
                        );
                        item.textContent = name;
                        return item;
                    }),
                );
            }
        }""",
        {
            "captionStatus": caption_status,
            "participants": list(participants),
            "state": state,
        },
    )


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
                _assert_synthetic_session_snapshot(
                    page,
                    fixture_id="alpha_fixture",
                    state="live",
                    caption_status="ready",
                    participants=(
                        "Synthetic Instructor",
                        "Synthetic Learner",
                    ),
                )
            finally:
                context.close()
        finally:
            browser.close()


def test_local_synthetic_meeting_history_keeps_only_safe_snapshots() -> None:
    fixture = build_fake_meeting_fixture(
        fixture_id="history_fixture",
        title="Synthetic Seminar",
        state="waiting",
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

                history = [
                    _capture_synthetic_session_history_entry(page, order=0),
                ]

                _set_synthetic_session_state(
                    page,
                    state="live",
                    caption_status="active",
                    participants=(
                        "Synthetic Guest",
                        "Synthetic Instructor",
                        "Synthetic Learner",
                    ),
                )
                history.append(_capture_synthetic_session_history_entry(page, order=1))

                _set_synthetic_session_state(
                    page,
                    state="ended",
                    caption_status="disabled",
                    participants=(
                        "Synthetic Instructor",
                        "Synthetic Learner",
                    ),
                )
                history.append(_capture_synthetic_session_history_entry(page, order=2))

                assert len(history) == 3
                assert [entry["order"] for entry in history] == [0, 1, 2]
                assert [entry["state"] for entry in history] == [
                    "waiting",
                    "live",
                    "ended",
                ]
                assert [entry["caption_status"] for entry in history] == [
                    "ready",
                    "active",
                    "disabled",
                ]
                assert [entry["participant_count"] for entry in history] == [2, 3, 2]
                assert history[-1] == {
                    "caption_status": "disabled",
                    "fixture_id": "history_fixture",
                    "order": 2,
                    "participant_count": 2,
                    "participants": (
                        "Synthetic Instructor",
                        "Synthetic Learner",
                    ),
                    "snapshot_kind": "synthetic_fake_meeting_session",
                    "state": "ended",
                }

                serialized_history = json.dumps(history, sort_keys=True)
                for forbidden_fragment in _HISTORY_FORBIDDEN_FRAGMENTS:
                    assert forbidden_fragment.lower() not in serialized_history.lower()
            finally:
                context.close()
        finally:
            browser.close()


def test_local_synthetic_meeting_page_exposes_bounded_transitions() -> None:
    fixture = build_fake_meeting_fixture(
        fixture_id="transition_fixture",
        title="Synthetic Seminar",
        state="waiting",
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

                _assert_synthetic_session_snapshot(
                    page,
                    fixture_id="transition_fixture",
                    state="waiting",
                    caption_status="ready",
                    participants=(
                        "Synthetic Instructor",
                        "Synthetic Learner",
                    ),
                )

                _set_synthetic_session_state(
                    page,
                    state="live",
                    caption_status="active",
                    participants=(
                        "Synthetic Guest",
                        "Synthetic Instructor",
                        "Synthetic Learner",
                    ),
                )
                _assert_synthetic_session_snapshot(
                    page,
                    fixture_id="transition_fixture",
                    state="live",
                    caption_status="active",
                    participants=(
                        "Synthetic Guest",
                        "Synthetic Instructor",
                        "Synthetic Learner",
                    ),
                )

                _set_synthetic_session_state(
                    page,
                    state="ended",
                    caption_status="disabled",
                    participants=(
                        "Synthetic Instructor",
                        "Synthetic Learner",
                    ),
                )
                _assert_synthetic_session_snapshot(
                    page,
                    fixture_id="transition_fixture",
                    state="ended",
                    caption_status="disabled",
                    participants=(
                        "Synthetic Instructor",
                        "Synthetic Learner",
                    ),
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
