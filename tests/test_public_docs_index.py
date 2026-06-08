from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs" / "public" / "index.md"
README = ROOT / "README.md"


def test_public_docs_index_names_local_navigation_scope() -> None:
    text = _read_index()
    normalized_text = _normalize_whitespace(text)

    required_fragments = (
        "Local Public Docs Index",
        "local navigation hub",
        "public-readiness inspection without publishing",
        "Gate E is deferred and blocked on `human_gate_e_approval`",
        "Gate E is not approved",
    )
    for fragment in required_fragments:
        assert fragment in normalized_text


def test_public_docs_index_lists_only_internal_public_docs() -> None:
    text = _read_index()

    required_links = (
        "docs/public/project-status-snapshot.md",
        "docs/public/recruiter-readiness-faq.md",
        "docs/public/gate-e-human-review-packet.md",
        "docs/public/gate-e-deferred-readiness-note.md",
        "docs/public/gate-d-human-demo-inspection-runbook.md",
    )
    for link in required_links:
        assert link in text

    assert "README.md" in text
    assert "http://" not in text
    assert "https://" not in text
    assert "meet.google" not in text.lower()


def test_public_docs_index_explains_each_document_without_approval() -> None:
    text = _read_index()
    normalized_text = _normalize_whitespace(text)

    required_fragments = (
        "Project status snapshot: one-page local state summary",
        "Recruiter/public-readiness FAQ: non-technical local reader summary",
        "Human Gate E review packet: human-review aid only, not an approval record",
        "Gate E deferred readiness note: deferred Gate E boundary",
        "Gate D human demo inspection runbook: local fixture-to-reviewer",
        "human-recorded narrow local fixture-to-reviewer pass only",
        "AI-solvable preparation may continue inside the recorded boundaries",
    )
    for fragment in required_fragments:
        assert fragment in normalized_text


def test_public_docs_index_lists_forbidden_actions() -> None:
    text = _read_index()

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


def test_public_docs_index_avoids_commands_and_approval_language() -> None:
    text = _read_index()
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


def test_readme_points_to_public_docs_index_without_release_claim() -> None:
    text = README.read_text(encoding="utf-8")
    normalized_text = _normalize_whitespace(text)

    assert "docs/public/index.md" in text
    assert "local public docs index" in normalized_text.lower()
    assert "Gate E is not approved" in normalized_text
    assert "safe to publish" not in normalized_text
    assert "release ready" not in normalized_text


def _read_index() -> str:
    assert INDEX.is_file(), f"expected public docs index at {INDEX}"
    return INDEX.read_text(encoding="utf-8")


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def _powershell_code_blocks(markdown: str) -> list[str]:
    return re.findall(r"```powershell\r?\n(.*?)```", markdown, flags=re.DOTALL)
