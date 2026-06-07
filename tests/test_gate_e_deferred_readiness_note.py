from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTE = ROOT / "docs" / "public" / "gate-e-deferred-readiness-note.md"
README = ROOT / "README.md"


def test_gate_e_deferred_readiness_note_records_defer_without_approval() -> None:
    text = _read_note()
    normalized_text = _normalize_whitespace(text)

    required_fragments = (
        "Gate E judgment: deferred",
        "blocked on `human_gate_e_approval`",
        "AI-solvable Gate E public-readiness reviews are complete and satisfactory",
        "Gate E is not approved",
        "not permission to merge, push-to-main, publish, release, or expose "
        "the repository publicly",
    )
    for fragment in required_fragments:
        assert fragment in normalized_text


def test_gate_e_deferred_readiness_note_preserves_demo_scope_boundary() -> None:
    text = _read_note()
    normalized_text = _normalize_whitespace(text)

    required_fragments = (
        "human-recorded narrow local fixture-to-reviewer pass only",
        "local fixture input",
        "confirmation-required alert preview",
        "archive/reviewer metadata summary",
        "does not approve broader, live, private, browser, or audio behavior",
    )
    for fragment in required_fragments:
        assert fragment in normalized_text


def test_gate_e_deferred_readiness_note_lists_forbidden_next_actions() -> None:
    text = _read_note()

    forbidden_surface_warnings = (
        "real external service use",
        "private data",
        "auth/profile/cookies",
        "credentials",
        "hardware/audio permission",
        "browser/server launch",
        "Playwright or in-app browser execution",
        "screenshots/traces/videos/downloads",
        "live delivery",
        "scheduler/background execution",
        "real deletion",
        "autonomous participation",
        "academic-answer behavior",
    )
    for warning in forbidden_surface_warnings:
        assert warning in text


def test_gate_e_deferred_readiness_note_avoids_approval_language() -> None:
    text = _read_note()

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
        assert claim not in text


def test_readme_points_to_gate_e_deferred_readiness_note() -> None:
    text = README.read_text(encoding="utf-8")
    normalized_text = _normalize_whitespace(text)

    assert "docs/public/gate-e-deferred-readiness-note.md" in text
    assert "Gate E deferred readiness note" in normalized_text
    assert "blocked on `human_gate_e_approval`" in normalized_text
    assert "Gate E is not approved" in normalized_text


def _read_note() -> str:
    assert NOTE.is_file(), f"expected Gate E deferred readiness note at {NOTE}"
    return NOTE.read_text(encoding="utf-8")


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())
