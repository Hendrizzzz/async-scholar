from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
PACKET = ROOT / "docs" / "public" / "gate-e-human-review-packet.md"


def test_gate_e_human_review_packet_records_deferred_blocked_state() -> None:
    text = _read_packet()
    normalized_text = _normalize_whitespace(text)

    required_fragments = (
        "Human Gate E Review Packet",
        "human-review aid only",
        "not an approval record",
        "Gate E is deferred and blocked only on `human_gate_e_approval`",
        "Gate E is not approved",
        "`human_gate_e_approval`: missing",
    )
    for fragment in required_fragments:
        assert fragment in normalized_text


def test_gate_e_human_review_packet_sets_human_only_boundary() -> None:
    text = _read_packet()
    normalized_text = _normalize_whitespace(text)

    required_fragments = (
        "fresh human approval is required before public exposure",
        "repository visibility changes",
        "merge",
        "push-to-main",
        "publishing",
        "release",
        "public GitHub action",
        "No agent or automated check can replace `human_gate_e_approval`",
    )
    for fragment in required_fragments:
        assert fragment in normalized_text


def test_gate_e_human_review_packet_points_only_to_internal_evidence() -> None:
    text = _read_packet()
    normalized_text = _normalize_whitespace(text)

    required_references = (
        "README.md",
        "docs/public/index.md",
        "docs/public/project-status-snapshot.md",
        "docs/public/recruiter-readiness-faq.md",
        "docs/public/gate-e-deferred-readiness-note.md",
        "docs/public/gate-d-human-demo-inspection-runbook.md",
        "docs/public/release-hold-checklist.md",
        "uv run python -m async_scholar gate-e-public-readiness --dry-run",
        "report-only",
    )
    for reference in required_references:
        assert reference in normalized_text

    assert "http://" not in text
    assert "https://" not in text
    assert "meet.google" not in text.lower()


def test_gate_e_human_review_packet_lists_forbidden_action_holds() -> None:
    text = _read_packet()

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


def test_gate_e_human_review_packet_avoids_execution_and_approval_language() -> None:
    text = _read_packet()
    normalized_text = _normalize_whitespace(text)

    unsafe_claims = (
        "Gate E passed",
        "Gate E approved",
        "public readiness approved",
        "public release approved",
        "safe to publish",
        "safe to push",
        "permission granted",
        "release ready",
        "approved to push",
        "approved to merge",
        "online monitoring approved",
        "Product Promise Alpha passed",
    )
    for claim in unsafe_claims:
        assert claim not in normalized_text

    execution_plan_markers = (
        "## Release Steps",
        "## Deployment",
        "## Publishing",
        "run this command",
        "execute this command",
    )
    for marker in execution_plan_markers:
        assert marker not in normalized_text

    assert _markdown_code_blocks(text) == []


def test_readme_points_to_gate_e_human_review_packet_without_approval_claim() -> None:
    text = _read_readme()
    normalized_text = _normalize_whitespace(text)
    pointer = "docs/public/gate-e-human-review-packet.md"

    assert pointer in normalized_text

    pointer_window = _normalized_window_around(normalized_text, pointer, radius=220)
    required_fragments = (
        "human-review aid only",
        "not an approval record",
        "Gate E is not approved",
        "human_gate_e_approval",
    )
    for fragment in required_fragments:
        assert fragment in pointer_window

    unsafe_claims = (
        "Gate E passed",
        "Gate E approved",
        "public readiness approved",
        "public release approved",
        "safe to publish",
        "safe to push",
        "release ready",
        "push-ready",
        "ready to push",
        "approved to push",
        "approved to merge",
        "permission granted",
        "greenlit",
        "launch-ready",
    )
    for claim in unsafe_claims:
        assert claim not in normalized_text


def _read_readme() -> str:
    return README.read_text(encoding="utf-8")


def _read_packet() -> str:
    assert PACKET.is_file(), f"expected human review packet at {PACKET}"
    return PACKET.read_text(encoding="utf-8")


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def _normalized_window_around(text: str, needle: str, *, radius: int) -> str:
    start = text.index(needle)
    return text[max(0, start - radius) : start + len(needle) + radius]


def _markdown_code_blocks(markdown: str) -> list[str]:
    return re.findall(r"```\w*\r?\n(.*?)```", markdown, flags=re.DOTALL)
