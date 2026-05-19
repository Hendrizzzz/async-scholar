from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from async_scholar import fake_meeting
from async_scholar.fake_meeting import (
    FAKE_MEETING_ERROR,
    SAFE_FAKE_MEETING_FIELDS,
    FakeMeetingFixture,
    build_fake_meeting_fixture,
    fake_meeting_fixture_safe_summary,
    fake_meeting_fixture_to_html,
    fake_meeting_fixture_to_json_ready,
)


def test_build_fake_meeting_fixture_is_deterministic_and_safe() -> None:
    fixture = build_fake_meeting_fixture(
        fixture_id="alpha_fixture",
        title="Synthetic Seminar",
        state="live",
        caption_status="ready",
        participants=("Synthetic Learner", "Synthetic Instructor"),
    )

    payload = fake_meeting_fixture_to_json_ready(fixture)
    expected = {
        "fixture_kind": "synthetic_fake_meeting",
        "fixture_id": "alpha_fixture",
        "title": "Synthetic Seminar",
        "state": "live",
        "caption_status": "ready",
        "participant_count": 2,
        "participants": ("Synthetic Instructor", "Synthetic Learner"),
    }

    assert fixture == FakeMeetingFixture(
        fixture_kind="synthetic_fake_meeting",
        fixture_id="alpha_fixture",
        title="Synthetic Seminar",
        state="live",
        caption_status="ready",
        participants=("Synthetic Instructor", "Synthetic Learner"),
    )
    assert tuple(payload) == SAFE_FAKE_MEETING_FIELDS
    assert payload == expected
    assert fixture.to_json_ready() == expected
    assert fixture.to_safe_summary() == expected
    assert fixture.safe_summary() == expected
    assert fake_meeting_fixture_safe_summary(fixture) == expected
    assert json.loads(json.dumps(payload, sort_keys=True)) == {
        **expected,
        "participants": list(expected["participants"]),
    }


def test_fake_meeting_html_is_inert_local_and_deterministic() -> None:
    fixture = build_fake_meeting_fixture(
        fixture_id="alpha_fixture",
        title="Synthetic Seminar",
        state="live",
        caption_status="ready",
        participants=("Synthetic Learner", "Synthetic Instructor"),
    )

    first_html = fake_meeting_fixture_to_html(fixture)
    second_html = fixture.to_html_document()

    assert first_html == second_html
    assert 'data-async-scholar-fixture-kind="synthetic_fake_meeting"' in first_html
    assert 'data-async-scholar-session-awareness="synthetic-local-only"' in first_html
    assert 'data-async-scholar-state="live"' in first_html
    assert 'data-async-scholar-caption-status="ready"' in first_html
    assert 'data-async-scholar-participant-count="2"' in first_html
    assert first_html.index("Synthetic Instructor") < first_html.index(
        "Synthetic Learner"
    )


def test_fake_meeting_output_contains_no_real_provider_or_private_terms() -> None:
    fixture = build_fake_meeting_fixture()
    output_text = (
        json.dumps(fake_meeting_fixture_to_json_ready(fixture), sort_keys=True)
        + fake_meeting_fixture_to_html(fixture)
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
    ):
        assert forbidden not in output_text


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("fixture_id", "alpha fixture"),
        ("fixture_id", "alpha/fixture"),
        ("fixture_id", "Alpha_fixture"),
        ("fixture_id", "alpha_fixture "),
        ("title", " Synthetic Seminar"),
        ("title", "Synthetic <script>"),
        ("title", "https://example.test"),
        ("state", "joining"),
        ("state", "Live"),
        ("caption_status", "streaming"),
        ("caption_status", "ready "),
        ("participants", []),
        ("participants", ["Synthetic Learner", "Synthetic Learner"]),
        ("participants", ["Synthetic Learner", "Google Account"]),
        ("participants", ["Synthetic/Learner"]),
    ],
)
def test_fake_meeting_rejects_unsafe_inputs_with_fixed_error(
    field_name: str,
    value: object,
) -> None:
    kwargs: dict[str, object] = {
        "fixture_id": "alpha_fixture",
        "title": "Synthetic Seminar",
        "state": "live",
        "caption_status": "ready",
        "participants": ("Synthetic Instructor", "Synthetic Learner"),
    }
    kwargs[field_name] = value

    with pytest.raises(ValueError) as exc_info:
        build_fake_meeting_fixture(**kwargs)

    assert str(exc_info.value) == FAKE_MEETING_ERROR
    assert str(value) not in str(exc_info.value)


def test_fake_meeting_rejects_extra_fields_and_is_immutable() -> None:
    fixture = build_fake_meeting_fixture()

    with pytest.raises(ValidationError):
        FakeMeetingFixture(
            **fixture.to_json_ready(),
            meeting_url="https://example.test",
        )
    with pytest.raises((TypeError, ValidationError)):
        fixture.title = "Changed"


def test_fake_meeting_helpers_revalidate_constructed_fixture_without_leakage() -> None:
    if not hasattr(FakeMeetingFixture, "model_construct"):
        pytest.skip("Pydantic v2 model_construct is not available")

    unsafe_fixture = FakeMeetingFixture.model_construct(
        fixture_kind="synthetic_fake_meeting",
        fixture_id="alpha_fixture",
        title="C:/Users/student/token-secret-auth-profile",
        state="live",
        caption_status="ready",
        participants=("Synthetic Instructor", "Synthetic Learner"),
    )

    for helper in (
        unsafe_fixture.to_json_ready,
        unsafe_fixture.safe_summary,
        unsafe_fixture.to_html_document,
        lambda: fake_meeting_fixture_to_json_ready(unsafe_fixture),
        lambda: fake_meeting_fixture_safe_summary(unsafe_fixture),
        lambda: fake_meeting_fixture_to_html(unsafe_fixture),
    ):
        with pytest.raises(ValueError) as exc_info:
            helper()

        error_text = str(exc_info.value)
        assert error_text == FAKE_MEETING_ERROR
        for forbidden in ("C:", "Users", "student", "token", "secret", "auth"):
            assert forbidden not in error_text


def test_fake_meeting_html_escapes_controlled_text() -> None:
    fixture = build_fake_meeting_fixture(
        title="Synthetic Seminar",
        participants=("Synthetic Instructor", "Synthetic Learner"),
    )

    html = fake_meeting_fixture_to_html(fixture)

    assert "<script" not in html.lower()
    assert "onload=" not in html.lower()
    assert "<form" not in html.lower()
    assert "<iframe" not in html.lower()
    assert "href=" not in html.lower()
    assert "src=" not in html.lower()
    assert "Synthetic Seminar" in html


def test_fake_meeting_module_has_no_execution_or_private_behavior() -> None:
    source = Path(fake_meeting.__file__).read_text(encoding="utf-8").lower()

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
