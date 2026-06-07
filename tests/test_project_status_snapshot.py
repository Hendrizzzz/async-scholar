from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "docs" / "public" / "project-status-snapshot.md"
README = ROOT / "README.md"


def test_project_status_snapshot_records_current_gate_state() -> None:
    text = _read_snapshot()
    normalized_text = _normalize_whitespace(text)

    required_fragments = (
        "Local inspection status snapshot",
        "Gate D / Product Promise Alpha: human-recorded narrow local "
        "fixture-to-reviewer pass only",
        "Gate E: deferred and blocked on `human_gate_e_approval`",
        "AI-solvable public-readiness reviews: complete and satisfactory as "
        "preparation work",
        "Gate E is not approved",
    )
    for fragment in required_fragments:
        assert fragment in normalized_text


def test_project_status_snapshot_points_to_internal_status_docs() -> None:
    text = _read_snapshot()

    required_links = (
        "docs/public/gate-d-human-demo-inspection-runbook.md",
        "docs/public/gate-e-deferred-readiness-note.md",
    )
    for link in required_links:
        assert link in text

    assert "README.md" in text
    assert "http://" not in text
    assert "https://" not in text
    assert "meet.google" not in text.lower()


def test_project_status_snapshot_preserves_allowed_demo_scope() -> None:
    text = _read_snapshot()
    normalized_text = _normalize_whitespace(text)

    required_fragments = (
        "local fixture input",
        "completed session status",
        "detected demo events",
        "confirmation-required alert preview",
        "archive/reviewer metadata summary",
        "explicit safety boundaries",
        "local inspection aid only",
    )
    for fragment in required_fragments:
        assert fragment in normalized_text


def test_project_status_snapshot_lists_forbidden_surfaces() -> None:
    text = _read_snapshot()

    forbidden_surface_warnings = (
        "public exposure",
        "merge",
        "push-to-main",
        "publishing",
        "release",
        "real external service use",
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


def test_project_status_snapshot_avoids_approval_and_execution_language() -> None:
    text = _read_snapshot()
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


def test_readme_points_to_project_status_snapshot_without_approval() -> None:
    text = README.read_text(encoding="utf-8")
    normalized_text = _normalize_whitespace(text)

    assert "docs/public/project-status-snapshot.md" in text
    assert "public status snapshot" in normalized_text
    assert "Gate E is not approved" in normalized_text
    assert "release ready" not in normalized_text
    assert "safe to publish" not in normalized_text


def _read_snapshot() -> str:
    assert SNAPSHOT.is_file(), f"expected project status snapshot at {SNAPSHOT}"
    return SNAPSHOT.read_text(encoding="utf-8")


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def _powershell_code_blocks(markdown: str) -> list[str]:
    return re.findall(r"```powershell\r?\n(.*?)```", markdown, flags=re.DOTALL)
