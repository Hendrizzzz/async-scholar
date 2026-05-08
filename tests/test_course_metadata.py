from pathlib import Path

import pytest
from pydantic import ValidationError

from async_scholar import course_metadata
from async_scholar.course_metadata import TITLE_MAX_LENGTH, CourseMetadata


def test_course_metadata_valid_creation_and_immutability() -> None:
    metadata = CourseMetadata(
        course_id="cs101",
        title="Intro to Async Systems",
        instructor_name="Dr. Rivera",
        meeting_url="https://meet.example.edu/secret-class",
        meeting_label="Lecture room",
    )

    assert metadata.course_id == "cs101"
    assert metadata.title == "Intro to Async Systems"
    assert metadata.instructor_name == "Dr. Rivera"
    assert metadata.meeting_url == "https://meet.example.edu/secret-class"
    assert metadata.meeting_label == "Lecture room"

    with pytest.raises((TypeError, ValidationError)):
        metadata.title = "Changed"


def test_course_metadata_normalizes_whitespace() -> None:
    metadata = CourseMetadata(
        course_id=" CS_101 ",
        title="\tIntro to Async Systems\n",
        instructor_name=" Dr. Rivera ",
        meeting_url=" https://meet.example.edu/secret-class ",
        meeting_label=" Lecture room ",
    )

    assert metadata.course_id == "cs_101"
    assert metadata.title == "Intro to Async Systems"
    assert metadata.instructor_name == "Dr. Rivera"
    assert metadata.meeting_url == "https://meet.example.edu/secret-class"
    assert metadata.meeting_label == "Lecture room"

    blank_optional = CourseMetadata(
        course_id="math101",
        title="Math",
        instructor_name=" ",
        meeting_url=" ",
        meeting_label="\t",
    )

    assert blank_optional.instructor_name is None
    assert blank_optional.meeting_url is None
    assert blank_optional.meeting_label is None


@pytest.mark.parametrize(
    "course_id",
    ["", "   ", "bad id", "-bad", "bad!", "a" * 65],
)
def test_course_metadata_rejects_invalid_or_blank_course_ids(course_id: str) -> None:
    with pytest.raises(ValidationError):
        CourseMetadata(course_id=course_id, title="Intro")


@pytest.mark.parametrize("title", ["", "   ", "x" * (TITLE_MAX_LENGTH + 1)])
def test_course_metadata_rejects_invalid_or_blank_titles(title: str) -> None:
    with pytest.raises(ValidationError):
        CourseMetadata(course_id="cs101", title=title)


def test_course_metadata_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        CourseMetadata(course_id="cs101", title="Intro", starts_at="09:00")


@pytest.mark.parametrize(
    "meeting_url",
    [
        "ftp://meet.example.edu/secret-class",
        "javascript:alert(1)",
        "meet.example.edu/secret-class",
        "https:///secret-class",
        "https://meet.example.edu/secret class",
        "https://meet.example.edu/secret\nHeader: value",
        "https://meet.example.edu/secret\tclass",
    ],
)
def test_course_metadata_rejects_unsupported_meeting_url_schemes(
    meeting_url: str,
) -> None:
    with pytest.raises(ValidationError):
        CourseMetadata(course_id="cs101", title="Intro", meeting_url=meeting_url)


def test_course_metadata_does_not_echo_meeting_url_in_validation_error() -> None:
    sensitive_url = "ftp://meet.example.edu/secret-class?token=private"

    with pytest.raises(ValidationError) as exc_info:
        CourseMetadata(course_id="cs101", title="Intro", meeting_url=sensitive_url)

    error_text = str(exc_info.value)
    assert sensitive_url not in error_text
    assert "token=private" not in error_text


def test_course_metadata_redacts_meeting_url_from_repr_and_safe_summaries() -> None:
    sensitive_url = "https://meet.example.edu/secret-class?token=private"
    metadata = CourseMetadata(
        course_id="cs101",
        title="Intro",
        instructor_name="Dr. Rivera",
        meeting_url=sensitive_url,
        meeting_label="Lecture room",
    )

    model_repr = repr(metadata)
    safe_summary = metadata.to_safe_summary()
    safe_summary_alias = metadata.safe_summary()
    public_summary_text = f"{safe_summary} {safe_summary_alias}"

    assert sensitive_url not in model_repr
    assert sensitive_url not in public_summary_text
    assert "token=private" not in model_repr
    assert "token=private" not in public_summary_text
    assert "meeting_url" not in model_repr
    assert "meeting_url" not in safe_summary
    assert "meeting_url" not in str(safe_summary)
    assert safe_summary_alias == safe_summary


def test_course_metadata_safe_summary_contents() -> None:
    metadata = CourseMetadata(
        course_id="cs101",
        title="Intro",
        instructor_name="Dr. Rivera",
        meeting_url="https://meet.example.edu/secret-class",
        meeting_label="Lecture room",
    )

    assert metadata.to_safe_summary() == {
        "course_id": "cs101",
        "title": "Intro",
        "instructor_name": "Dr. Rivera",
        "meeting_label": "Lecture room",
    }


def test_course_metadata_module_has_no_persistence_scheduler_or_browser_behavior() -> (
    None
):
    source = Path(course_metadata.__file__).read_text(encoding="utf-8")

    forbidden_tokens = [
        "sqlite",
        "jsonl",
        "open(",
        "read_text",
        "write_text",
        "schedule",
        "browser",
        "playwright",
        "selenium",
        "nicegui",
        "requests",
        "httpx",
        "aiohttp",
        "fastapi",
        "asyncio",
        "threading",
        "subprocess",
    ]

    normalized_source = source.lower()
    for forbidden_token in forbidden_tokens:
        assert forbidden_token not in normalized_source
