from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = ROOT / "docs" / "public" / "gate-d-human-demo-inspection-runbook.md"
README = ROOT / "README.md"


def test_runbook_names_human_only_gate_d_stop_point() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    required_fragments = (
        "Gate D / Product Promise Alpha has a human-recorded narrow local pass",
        "Gate E public readiness remains blocked",
        "human Gate E approval is deferred",
        "AI-solvable public-readiness preparation stops before Gate E approval",
        "Do not treat this runbook as Gate E approval",
    )
    for fragment in required_fragments:
        assert fragment in text


def test_runbook_separates_automated_evidence_from_manual_judgment() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    assert "Automated Evidence" in text
    assert "Human Demo Inspection" in text
    assert "Manual Judgment To Record After Inspection" in text
    assert "What the automated commands can show" in text
    assert "What only the user can decide" in text


def test_runbook_references_only_allowed_demo_commands() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    allowed_command_fragments = (
        "uv run python -m async_scholar --help",
        "uv run python -m async_scholar local-alpha-dashboard-demo --dry-run",
        "uv run python -m async_scholar gate-d-local-evidence-bundle",
        "uv run python -m async_scholar gate-d-handoff-packet-local",
        "scripts\\run_scheduler_archive_workflow_smoke.ps1",
    )
    for fragment in allowed_command_fragments:
        assert fragment in text

    assert _powershell_code_blocks(text) == []

    unsafe_command_fragments = (
        "meet.google.com",
        "playwright",
        "selenium",
        "mic-recording-diagnostic",
        "archive-delete",
        "archive-export-local",
        "git push",
        "start-sleep",
        "start-job",
        "register-scheduledjob",
    )
    lowered_text = text.lower()
    for fragment in unsafe_command_fragments:
        assert fragment not in lowered_text


def test_runbook_lists_forbidden_live_private_or_destructive_surfaces() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    forbidden_surface_warnings = (
        "real Google Meet",
        "auth/profile/cookies",
        "private meeting data",
        "browser automation",
        "loopback/system audio",
        "live delivery",
        "real deletion",
        "push",
        "public release",
    )
    for warning in forbidden_surface_warnings:
        assert warning in text


def test_readme_points_to_runbook_without_claiming_gate_pass() -> None:
    text = README.read_text(encoding="utf-8")

    assert "docs/public/gate-d-human-demo-inspection-runbook.md" in text
    assert "human demo inspection" in text.lower()
    assert "historical context" in text
    unsafe_claims = (
        "Gate D passed",
        "Product Promise Alpha passed",
        "product_judgment_evidence satisfied",
        "Gate E approved",
        "public release approved",
    )
    for claim in unsafe_claims:
        assert claim not in text


def _powershell_code_blocks(markdown: str) -> list[str]:
    return re.findall(r"```powershell\r?\n(.*?)```", markdown, flags=re.DOTALL)
