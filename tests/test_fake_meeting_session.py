from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from async_scholar import fake_meeting_session
from async_scholar.fake_meeting import build_fake_meeting_fixture
from async_scholar.fake_meeting_session import (
    FAKE_MEETING_SESSION_ERROR,
    SAFE_FAKE_MEETING_SESSION_FIELDS,
    FakeMeetingSessionSnapshot,
    fake_meeting_session_snapshot_safe_summary,
    fake_meeting_session_snapshot_to_json_ready,
    inspect_fake_meeting_session_html,
)


def _fixture_html() -> str:
    return build_fake_meeting_fixture(
        fixture_id="alpha_fixture",
        title="Synthetic Seminar",
        state="live",
        caption_status="ready",
        participants=("Synthetic Learner", "Synthetic Instructor"),
    ).to_html_document()


def test_inspect_fake_meeting_session_html_returns_safe_snapshot() -> None:
    snapshot = inspect_fake_meeting_session_html(_fixture_html())
    payload = fake_meeting_session_snapshot_to_json_ready(snapshot)
    expected = {
        "snapshot_kind": "synthetic_fake_meeting_session",
        "fixture_id": "alpha_fixture",
        "state": "live",
        "caption_status": "ready",
        "participant_count": 2,
        "participants": ("Synthetic Instructor", "Synthetic Learner"),
    }

    assert snapshot == FakeMeetingSessionSnapshot(**expected)
    assert tuple(payload) == SAFE_FAKE_MEETING_SESSION_FIELDS
    assert payload == expected
    assert snapshot.to_json_ready() == expected
    assert snapshot.to_safe_summary() == expected
    assert snapshot.safe_summary() == expected
    assert fake_meeting_session_snapshot_safe_summary(snapshot) == expected
    assert json.loads(json.dumps(payload, sort_keys=True)) == {
        **expected,
        "participants": list(expected["participants"]),
    }


def test_inspection_output_contains_no_provider_or_private_terms() -> None:
    snapshot = inspect_fake_meeting_session_html(_fixture_html())
    output_text = json.dumps(
        fake_meeting_session_snapshot_to_json_ready(snapshot),
        sort_keys=True,
    ).lower()

    for forbidden in (
        "google",
        "meet.google",
        "meeting_url",
        "http://",
        "https://",
        "cookie",
        "token",
        "credential",
        "password",
        "auth",
        "profile",
        ".env",
        "transcript",
        "recording",
        "microphone",
        "loopback",
        "playwright",
        "browser",
        "c:\\",
        "/home/",
        "<html",
        "data-async-scholar",
    ):
        assert forbidden not in output_text


@pytest.mark.parametrize(
    "html_text",
    [
        "",
        "<html></html>",
        _fixture_html().replace(
            "synthetic_fake_meeting",
            "synthetic_other_meeting",
        ),
        _fixture_html().replace(
            'data-async-scholar-state="live"',
            'data-async-scholar-state="joining"',
        ),
        _fixture_html().replace(
            'data-async-scholar-caption-status="ready"',
            'data-async-scholar-caption-status="streaming"',
        ),
        _fixture_html().replace(
            'data-async-scholar-participant-count="2"',
            'data-async-scholar-participant-count="3"',
        ),
        _fixture_html().replace(
            'data-async-scholar-participant="Synthetic Instructor"',
            'data-async-scholar-participant="Synthetic Learner"',
        ),
        _fixture_html().replace(
            'data-async-scholar-participant="Synthetic Learner"',
            'data-async-scholar-participant="C:/Users/student/token-secret-auth"',
        ),
        _fixture_html().replace(
            '<main id="synthetic-meeting-root">',
            '<script></script><main id="synthetic-meeting-root">',
        ),
        _fixture_html().replace(
            '<main id="synthetic-meeting-root">',
            '<main onload="x" id="synthetic-meeting-root">',
        ),
        _fixture_html().replace(
            '<main id="synthetic-meeting-root">',
            '<img src="https://example.test/pixel.png">'
            '<main id="synthetic-meeting-root">',
        ),
        "x" * 12_001,
    ],
)
def test_inspector_rejects_invalid_html_with_fixed_error(html_text: object) -> None:
    with pytest.raises(ValueError) as exc_info:
        inspect_fake_meeting_session_html(html_text)

    error_text = str(exc_info.value)
    assert error_text == FAKE_MEETING_SESSION_ERROR
    for forbidden in (
        "C:",
        "Users",
        "student",
        "token",
        "secret",
        "auth",
        "https://",
        "example.test",
        "<script",
        "onload",
    ):
        assert forbidden not in error_text


def test_inspector_rejects_non_string_input_with_fixed_error() -> None:
    with pytest.raises(ValueError) as exc_info:
        inspect_fake_meeting_session_html({"html": _fixture_html()})

    assert str(exc_info.value) == FAKE_MEETING_SESSION_ERROR


def test_snapshot_rejects_extra_fields_and_is_immutable() -> None:
    snapshot = inspect_fake_meeting_session_html(_fixture_html())

    with pytest.raises(ValidationError):
        FakeMeetingSessionSnapshot(
            **snapshot.to_json_ready(),
            raw_html=_fixture_html(),
        )
    with pytest.raises((TypeError, ValidationError)):
        snapshot.state = "ended"


def test_snapshot_rejects_inconsistent_count() -> None:
    with pytest.raises(ValueError):
        FakeMeetingSessionSnapshot(
            snapshot_kind="synthetic_fake_meeting_session",
            fixture_id="alpha_fixture",
            state="live",
            caption_status="ready",
            participant_count=3,
            participants=("Synthetic Instructor", "Synthetic Learner"),
        )


def test_snapshot_helpers_revalidate_constructed_snapshot_without_leakage() -> None:
    if not hasattr(FakeMeetingSessionSnapshot, "model_construct"):
        pytest.skip("Pydantic v2 model_construct is not available")

    unsafe_snapshot = FakeMeetingSessionSnapshot.model_construct(
        snapshot_kind="synthetic_fake_meeting_session",
        fixture_id="alpha_fixture",
        state="live",
        caption_status="ready",
        participant_count=1,
        participants=("C:/Users/student/token-secret-auth-profile",),
    )

    for helper in (
        unsafe_snapshot.to_json_ready,
        unsafe_snapshot.safe_summary,
        lambda: fake_meeting_session_snapshot_to_json_ready(unsafe_snapshot),
        lambda: fake_meeting_session_snapshot_safe_summary(unsafe_snapshot),
    ):
        with pytest.raises(ValueError) as exc_info:
            helper()

        error_text = str(exc_info.value)
        assert error_text == FAKE_MEETING_SESSION_ERROR
        for forbidden in ("C:", "Users", "student", "token", "secret", "auth"):
            assert forbidden not in error_text


def test_snapshot_helpers_reject_subclasses() -> None:
    class SnapshotSubclass(FakeMeetingSessionSnapshot):
        pass

    snapshot = SnapshotSubclass(
        snapshot_kind="synthetic_fake_meeting_session",
        fixture_id="alpha_fixture",
        state="live",
        caption_status="ready",
        participant_count=2,
        participants=("Synthetic Instructor", "Synthetic Learner"),
    )

    with pytest.raises(ValueError) as exc_info:
        fake_meeting_session_snapshot_to_json_ready(snapshot)

    assert str(exc_info.value) == FAKE_MEETING_SESSION_ERROR


def test_fake_meeting_session_module_has_no_execution_or_private_behavior() -> None:
    source = Path(fake_meeting_session.__file__).read_text(encoding="utf-8").lower()

    forbidden_tokens = [
        "playwright",
        "selenium",
        "webbrowser",
        "browser",
        "google",
        "meet.google",
        "meeting_url",
        "http://",
        "https://",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "server",
        "fastapi",
        "nicegui",
        "open(",
        "read_text",
        "write_text",
        "write_bytes",
        "path(",
        "sqlite",
        "os.environ",
        ".env",
        "cookie",
        "token",
        "credential",
        "password",
        "auth",
        "profile",
        "microphone",
        "loopback",
        "sounddevice",
        "subprocess",
        "threading",
        "asyncio",
        "timer",
        "sleep(",
        "archive_export",
        "archive_delete",
        "unlink",
        "remove",
        "rmtree",
        "notification",
        "notifier",
        "scheduler",
        "scheduled_start",
    ]

    for token in forbidden_tokens:
        assert token not in source
