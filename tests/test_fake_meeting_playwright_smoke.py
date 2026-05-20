from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from async_scholar.alerts import build_alert_notification_payload
from async_scholar.artifacts import write_alert_log, write_reviewer_markdown
from async_scholar.fake_meeting import build_fake_meeting_fixture
from async_scholar.fake_meeting_session import (
    build_fake_meeting_session_awareness_event,
    build_fake_meeting_session_history_summary,
    inspect_fake_meeting_session_html,
)

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
    "C:" + "\\Users",
    "." + "env",
)


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


def _capture_synthetic_session_snapshot(
    page: Any,
):
    snapshot = inspect_fake_meeting_session_html(page.content())

    assert page.url == "about:blank"
    return snapshot


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


def test_local_synthetic_meeting_uses_only_tmp_user_data_dir(tmp_path) -> None:
    user_data_dir = tmp_path / "synthetic-user-data"
    resolved_tmp_path = tmp_path.resolve()
    resolved_user_data_dir = user_data_dir.resolve()
    assert resolved_user_data_dir.is_relative_to(resolved_tmp_path)
    assert resolved_user_data_dir != resolved_tmp_path

    fixture = build_fake_meeting_fixture(
        fixture_id="temp_profile_fixture",
        title="Synthetic Seminar",
        state="live",
        caption_status="ready",
        participants=("Synthetic Learner", "Synthetic Instructor"),
    )
    html = fixture.to_html_document()

    with sync_playwright() as playwright:
        executable_path = _managed_chromium_executable_path(playwright)
        try:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                executable_path=str(executable_path),
                headless=True,
            )
        except PlaywrightError:
            pytest.skip(_SKIP_REASON)

        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.set_content(html, wait_until="domcontentloaded")

            snapshot = _capture_synthetic_session_snapshot(page)
            assert snapshot.snapshot_kind == "synthetic_fake_meeting_session"
            assert snapshot.fixture_id == "temp_profile_fixture"
            assert snapshot.state == "live"
            assert snapshot.caption_status == "ready"
            assert snapshot.participant_count == 2
            assert snapshot.participants == (
                "Synthetic Instructor",
                "Synthetic Learner",
            )
            assert user_data_dir.exists()
            assert user_data_dir.resolve().is_relative_to(resolved_tmp_path)
        finally:
            context.close()


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

                snapshots = [_capture_synthetic_session_snapshot(page)]

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
                snapshots.append(_capture_synthetic_session_snapshot(page))

                _set_synthetic_session_state(
                    page,
                    state="ended",
                    caption_status="disabled",
                    participants=(
                        "Synthetic Instructor",
                        "Synthetic Learner",
                    ),
                )
                snapshots.append(_capture_synthetic_session_snapshot(page))

                summary = build_fake_meeting_session_history_summary(snapshots)
                assert (
                    summary["history_kind"] == "synthetic_fake_meeting_session_history"
                )
                assert summary["fixture_id"] == "history_fixture"
                assert summary["snapshot_count"] == 3
                assert summary["ordered_states"] == (
                    "waiting",
                    "live",
                    "ended",
                )
                assert summary["ordered_caption_statuses"] == (
                    "ready",
                    "active",
                    "disabled",
                )
                assert summary["ordered_participant_counts"] == (2, 3, 2)
                assert summary["final_state"] == "ended"
                assert summary["final_caption_status"] == "disabled"
                assert summary["max_participant_count"] == 3
                assert summary["participants"] == (
                    "Synthetic Guest",
                    "Synthetic Instructor",
                    "Synthetic Learner",
                )

                event = build_fake_meeting_session_awareness_event(snapshots)
                assert event.event_id == (
                    "synthetic-session-awareness-ended-disabled-2-3"
                )
                assert event.session_id == "synthetic-session-awareness"
                assert event.event_type == "synthetic_session_awareness"
                assert event.detected_at_seconds == 2.0
                assert event.source_segment_ids == (
                    "synthetic-session-awareness-source-ended-disabled-2-3",
                )
                assert event.message == (
                    "Synthetic session ended; captions disabled; "
                    "2 participants observed."
                )
                assert event.confidence == 0.75

                payload = build_alert_notification_payload(event.event_type)
                assert payload == {
                    "severity": "normal",
                    "title": "Lecture alert: Synthetic session awareness",
                    "body": (
                        "Review when available; "
                        "confirm before any participation action."
                    ),
                    "requires_confirmation": True,
                }

                serialized_payload = json.dumps(payload, sort_keys=True)
                for forbidden_fragment in _HISTORY_FORBIDDEN_FRAGMENTS:
                    assert forbidden_fragment.lower() not in serialized_payload.lower()
            finally:
                context.close()
        finally:
            browser.close()


def test_local_synthetic_meeting_history_writes_safe_artifacts(tmp_path) -> None:
    fixture = build_fake_meeting_fixture(
        fixture_id="artifact_smoke_fixture",
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

                snapshots = [_capture_synthetic_session_snapshot(page)]

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
                snapshots.append(_capture_synthetic_session_snapshot(page))

                _set_synthetic_session_state(
                    page,
                    state="ended",
                    caption_status="disabled",
                    participants=(
                        "Synthetic Instructor",
                        "Synthetic Learner",
                    ),
                )
                snapshots.append(_capture_synthetic_session_snapshot(page))

                summary = build_fake_meeting_session_history_summary(snapshots)
                assert summary["final_state"] == "ended"
                assert summary["final_caption_status"] == "disabled"

                event = build_fake_meeting_session_awareness_event(snapshots)
                alerts_path = write_alert_log([event], tmp_path)
                reviewer_path = write_reviewer_markdown([event], [], tmp_path)

                alert_text = alerts_path.read_text(encoding="utf-8")
                reviewer_text = reviewer_path.read_text(encoding="utf-8")
                alert_payload = json.loads(alert_text)
                assert alert_payload["event_type"] == "synthetic_session_awareness"
                assert alert_payload["message"] == (
                    "Synthetic session awareness recorded."
                )
                assert alert_payload["severity"] == "normal"
                assert alert_payload["status"] == "pending"
                assert alert_payload["requires_confirmation"] is True
                assert alert_payload["dispatch_results"] == [
                    {
                        "provider": "file",
                        "severity": "normal",
                        "status": "sent",
                        "requires_confirmation": True,
                    }
                ]
                assert alert_payload["retry_log_decisions"] == []
                assert "source_segment_ids" not in alert_payload

                assert "## Synthetic Session Awareness" in reviewer_text
                assert "- Event: Synthetic session awareness recorded." in reviewer_text
                assert "- Evidence: Synthetic session metadata only." in reviewer_text
                assert "Source segment IDs" not in reviewer_text
                assert "Source snippets" not in reviewer_text
                assert "Missing transcript segment" not in reviewer_text

                artifact_text = "\n".join((alert_text, reviewer_text))
                for forbidden_fragment in (
                    event.event_id,
                    event.session_id,
                    event.source_segment_ids[0],
                    event.message,
                    "artifact_smoke_fixture",
                    "Synthetic Guest",
                    "Synthetic Instructor",
                    "Synthetic Learner",
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
                    "C:/Users",
                    "C:" + "\\Users",
                    "." + "env",
                    "au" + "dio",
                    "mic",
                    "cam" + "era",
                    "loop" + "back",
                    "sched" + "uler",
                    "notifi" + "cation",
                    "archive" + "_export",
                    "archive" + "_delete",
                ):
                    assert forbidden_fragment.lower() not in artifact_text.lower()
            finally:
                context.close()
        finally:
            browser.close()


def test_tmp_profile_synthetic_meeting_writes_only_safe_artifacts(tmp_path) -> None:
    user_data_dir = tmp_path / "synthetic-user-data-artifacts"
    artifact_root = tmp_path / "synthetic-artifacts"
    artifact_root.mkdir()
    resolved_tmp_path = tmp_path.resolve()
    resolved_user_data_dir = user_data_dir.resolve()
    resolved_artifact_root = artifact_root.resolve()
    assert resolved_user_data_dir.is_relative_to(resolved_tmp_path)
    assert resolved_artifact_root.is_relative_to(resolved_tmp_path)
    assert not resolved_artifact_root.is_relative_to(resolved_user_data_dir)
    assert not resolved_user_data_dir.is_relative_to(resolved_artifact_root)

    fixture = build_fake_meeting_fixture(
        fixture_id="temp_profile_artifact_fixture",
        title="Synthetic Seminar",
        state="waiting",
        caption_status="ready",
        participants=("Synthetic Learner", "Synthetic Instructor"),
    )
    html = fixture.to_html_document()

    with sync_playwright() as playwright:
        executable_path = _managed_chromium_executable_path(playwright)
        try:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                executable_path=str(executable_path),
                headless=True,
            )
        except PlaywrightError:
            pytest.skip(_SKIP_REASON)

        try:
            page = context.pages[0] if context.pages else context.new_page()
            page.set_content(html, wait_until="domcontentloaded")

            snapshots = [_capture_synthetic_session_snapshot(page)]

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
            snapshots.append(_capture_synthetic_session_snapshot(page))

            _set_synthetic_session_state(
                page,
                state="ended",
                caption_status="disabled",
                participants=(
                    "Synthetic Instructor",
                    "Synthetic Learner",
                ),
            )
            snapshots.append(_capture_synthetic_session_snapshot(page))

            event = build_fake_meeting_session_awareness_event(snapshots)
            alerts_path = write_alert_log([event], artifact_root)
            reviewer_path = write_reviewer_markdown([event], [], artifact_root)
            assert alerts_path.parent.resolve() == resolved_artifact_root
            assert reviewer_path.parent.resolve() == resolved_artifact_root

            alert_text = alerts_path.read_text(encoding="utf-8")
            reviewer_text = reviewer_path.read_text(encoding="utf-8")
            alert_payload = json.loads(alert_text)
            assert alert_payload["event_type"] == "synthetic_session_awareness"
            assert alert_payload["message"] == "Synthetic session awareness recorded."
            assert alert_payload["severity"] == "normal"
            assert alert_payload["status"] == "pending"
            assert alert_payload["requires_confirmation"] is True
            assert alert_payload["dispatch_results"] == [
                {
                    "provider": "file",
                    "severity": "normal",
                    "status": "sent",
                    "requires_confirmation": True,
                }
            ]
            assert alert_payload["retry_log_decisions"] == []
            assert "source_segment_ids" not in alert_payload

            assert "## Synthetic Session Awareness" in reviewer_text
            assert "- Event: Synthetic session awareness recorded." in reviewer_text
            assert "- Evidence: Synthetic session metadata only." in reviewer_text
            assert "Source segment IDs" not in reviewer_text
            assert "Source snippets" not in reviewer_text
            assert "Missing transcript segment" not in reviewer_text

            artifact_text = "\n".join((alert_text, reviewer_text))
            for forbidden_fragment in (
                event.event_id,
                event.session_id,
                event.source_segment_ids[0],
                event.message,
                "temp_profile_artifact_fixture",
                "Synthetic Guest",
                "Synthetic Instructor",
                "Synthetic Learner",
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
                "C:/Users",
                "C:" + "\\Users",
                "." + "env",
                "au" + "dio",
                "mic",
                "cam" + "era",
                "loop" + "back",
                "sched" + "uler",
                "notifi" + "cation",
                "archive" + "_export",
                "archive" + "_delete",
            ):
                assert forbidden_fragment.lower() not in artifact_text.lower()
        finally:
            context.close()


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
