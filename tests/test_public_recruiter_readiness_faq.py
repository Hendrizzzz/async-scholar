from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAQ = ROOT / "docs" / "public" / "recruiter-readiness-faq.md"
README = ROOT / "README.md"


def test_recruiter_readiness_faq_explains_product_without_overclaiming() -> None:
    text = _read_faq()
    normalized_text = _normalize_whitespace(text)

    required_fragments = (
        "Local Recruiter/Public-Readiness FAQ",
        "local-first lecture monitoring app",
        "transcription, event detection, alerts, archives, and study-review generation",
        "fixture-to-reviewer demo",
        "non-technical inspection aid only",
        "does not publish, release, expose, merge, or push the repository",
    )
    for fragment in required_fragments:
        assert fragment in normalized_text


def test_recruiter_readiness_faq_records_gate_status_boundaries() -> None:
    text = _read_faq()
    normalized_text = _normalize_whitespace(text)

    required_fragments = (
        "Gate D / Product Promise Alpha: human-recorded narrow local "
        "fixture-to-reviewer pass only",
        "Gate E: deferred and blocked on `human_gate_e_approval`",
        "AI-solvable Gate E public-readiness reviews are complete and "
        "satisfactory as preparation work",
        "Gate E is not approved",
        "fresh human approval is still required",
    )
    for fragment in required_fragments:
        assert fragment in normalized_text


def test_recruiter_readiness_faq_answers_what_can_be_inferred() -> None:
    text = _read_faq()
    normalized_text = _normalize_whitespace(text)

    required_fragments = (
        "The local demo can show the fixture-to-reviewer loop",
        "local fixture input",
        "detected demo events",
        "confirmation-required alert preview",
        "archive/reviewer metadata summary",
        "It cannot be used as proof of live online monitoring",
        "real class or meeting behavior",
    )
    for fragment in required_fragments:
        assert fragment in normalized_text


def test_recruiter_readiness_faq_links_only_internal_context_docs() -> None:
    text = _read_faq()

    required_links = (
        "README.md",
        "docs/public/index.md",
        "docs/public/project-status-snapshot.md",
        "docs/public/gate-e-deferred-readiness-note.md",
        "docs/public/gate-d-human-demo-inspection-runbook.md",
    )
    for link in required_links:
        assert link in text

    assert "http://" not in text
    assert "https://" not in text
    assert "meet.google" not in text.lower()


def test_recruiter_readiness_faq_lists_forbidden_surfaces() -> None:
    text = _read_faq()

    forbidden_surface_warnings = (
        "public exposure",
        "repository visibility change",
        "merge",
        "push-to-main",
        "publishing",
        "release",
        "external services",
        "private data",
        "auth/profile/cookies/tokens",
        "credentials",
        "hardware/audio",
        "browser/server launch",
        "Playwright or in-app browser execution",
        "screenshots/traces/videos/downloads",
        "live delivery",
        "scheduler/background execution",
        "deletion/export execution",
        "real deletion",
        "autonomous participation",
        "academic-answer behavior",
    )
    for warning in forbidden_surface_warnings:
        assert warning in text


def test_recruiter_readiness_faq_avoids_commands_and_approval_language() -> None:
    text = _read_faq()
    normalized_text = _normalize_whitespace(text)

    unsafe_claims = (
        "Gate E passed",
        "Gate E approved",
        "public readiness approved",
        "public release approved",
        "safe to publish",
        "release ready",
        "approved to push",
        "approved to merge",
        "online monitoring approved",
        "Product Promise Alpha passed",
    )
    for claim in unsafe_claims:
        assert claim not in normalized_text

    assert _powershell_code_blocks(text) == []


def test_readme_points_to_recruiter_readiness_faq_without_release_claim() -> None:
    text = README.read_text(encoding="utf-8")
    normalized_text = _normalize_whitespace(text)

    assert "docs/public/recruiter-readiness-faq.md" in text
    assert "recruiter/public-readiness FAQ" in normalized_text
    assert "Gate E is not approved" in normalized_text
    assert "safe to publish" not in normalized_text
    assert "release ready" not in normalized_text


def _read_faq() -> str:
    assert FAQ.is_file(), f"expected recruiter readiness FAQ at {FAQ}"
    return FAQ.read_text(encoding="utf-8")


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def _powershell_code_blocks(markdown: str) -> list[str]:
    return re.findall(r"```powershell\r?\n(.*?)```", markdown, flags=re.DOTALL)
