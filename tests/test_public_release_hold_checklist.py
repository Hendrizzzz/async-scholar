from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / "docs" / "public" / "release-hold-checklist.md"
README = ROOT / "README.md"


def test_release_hold_checklist_records_hold_state() -> None:
    text = _read_checklist()
    normalized_text = _normalize_whitespace(text)

    required_fragments = (
        "Local Release Hold Checklist",
        "release hold",
        "Gate E is deferred and blocked on `human_gate_e_approval`",
        "Gate E is not approved",
        "fresh human approval is still required",
        "This checklist is not a release plan",
    )
    for fragment in required_fragments:
        assert fragment in normalized_text


def test_release_hold_checklist_lists_ai_solved_and_human_remaining_items() -> None:
    text = _read_checklist()
    normalized_text = _normalize_whitespace(text)

    solved_fragments = (
        "`public_docs_boundary_review`: satisfactory",
        "`secret_and_private_data_review`: satisfactory",
        "`generated_artifact_review`: satisfactory",
        "`ignored_file_review`: satisfactory",
        "`push_merge_release_plan_review`: satisfactory",
    )
    for fragment in solved_fragments:
        assert fragment in normalized_text

    assert "`human_gate_e_approval`: missing" in normalized_text
    assert "The only remaining Gate E item is human-only" in normalized_text


def test_release_hold_checklist_links_only_internal_public_docs() -> None:
    text = _read_checklist()

    required_links = (
        "README.md",
        "docs/public/index.md",
        "docs/public/project-status-snapshot.md",
        "docs/public/recruiter-readiness-faq.md",
        "docs/public/gate-e-deferred-readiness-note.md",
        "docs/public/gate-d-human-demo-inspection-runbook.md",
    )
    for link in required_links:
        assert link in text

    assert "http://" not in text
    assert "https://" not in text
    assert "meet.google" not in text.lower()


def test_release_hold_checklist_lists_forbidden_actions() -> None:
    text = _read_checklist()

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


def test_release_hold_checklist_avoids_commands_and_approval_language() -> None:
    text = _read_checklist()
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


def test_readme_points_to_release_hold_checklist_without_release_claim() -> None:
    text = README.read_text(encoding="utf-8")
    normalized_text = _normalize_whitespace(text)

    assert "docs/public/release-hold-checklist.md" in text
    assert "release hold checklist" in normalized_text.lower()
    assert "Gate E is not approved" in normalized_text
    assert "safe to publish" not in normalized_text
    assert "release ready" not in normalized_text


def _read_checklist() -> str:
    assert CHECKLIST.is_file(), f"expected release hold checklist at {CHECKLIST}"
    return CHECKLIST.read_text(encoding="utf-8")


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def _powershell_code_blocks(markdown: str) -> list[str]:
    return re.findall(r"```powershell\r?\n(.*?)```", markdown, flags=re.DOTALL)
