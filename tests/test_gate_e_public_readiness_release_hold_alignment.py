from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / "docs" / "public" / "release-hold-checklist.md"

AI_SOLVED_REVIEW_ITEMS = (
    "public_docs_boundary_review",
    "secret_and_private_data_review",
    "generated_artifact_review",
    "ignored_file_review",
    "push_merge_release_plan_review",
)
HUMAN_ONLY_MISSING_REVIEW_ITEM = "human_gate_e_approval"
HELD_ACTION_WARNINGS = (
    "public exposure",
    "push-to-main",
    "merge",
    "publishing",
    "release",
    "browser/server launch",
    "Playwright or in-app browser execution",
    "screenshots/traces/videos/downloads",
    "private data",
    "auth/profile/cookies/tokens",
    "hardware/audio",
    "live delivery",
    "scheduler/background execution",
    "deletion/export execution",
    "autonomous participation",
    "academic-answer behavior",
)
FALSE_APPROVAL_FLAGS = (
    "public_release_approved",
    "push_approved",
    "merge_approved",
)
FALSE_ACTION_FLAGS = (
    "publish_performed",
    "push_performed",
    "merge_performed",
    "browser_or_server_launched",
    "browser_automation_performed",
    "playwright_or_in_app_browser_performed",
    "screenshot_trace_video_download_performed",
    "auth_profile_accessed",
    "cookie_accessed",
    "private_data_read",
    "audio_capture_performed",
    "hardware_access_performed",
    "loopback_capture_performed",
    "live_delivery_performed",
    "scheduler_background_execution_performed",
    "deletion_or_export_performed",
    "autonomous_participation_performed",
    "academic_answer_behavior_performed",
)


def test_gate_e_cli_status_aligns_with_release_hold_checklist() -> None:
    checklist_text = CHECKLIST.read_text(encoding="utf-8")
    checklist_ai_solved_items = _checklist_review_items(
        checklist_text,
        heading="AI-Solved Gate E Prep Items",
    )
    checklist_human_only_items = _checklist_review_items(
        checklist_text,
        heading="Human-Only Remaining Item",
    )
    payload = _run_gate_e_public_readiness_dry_run()

    assert checklist_ai_solved_items == {
        review_item: "satisfactory" for review_item in AI_SOLVED_REVIEW_ITEMS
    }
    assert _payload_satisfactory_review_items(payload) == list(AI_SOLVED_REVIEW_ITEMS)
    for review_item in AI_SOLVED_REVIEW_ITEMS:
        assert (
            payload[f"{review_item}_status"] == checklist_ai_solved_items[review_item]
        )

    assert checklist_human_only_items == {HUMAN_ONLY_MISSING_REVIEW_ITEM: "missing"}
    assert payload["missing_review_items"] == [HUMAN_ONLY_MISSING_REVIEW_ITEM]
    assert payload["missing_review_item_count"] == 1
    assert payload["human_gate_e_approval_status"] == "missing"


def test_release_hold_status_stays_blocked_across_cli_and_checklist() -> None:
    checklist_text = CHECKLIST.read_text(encoding="utf-8")
    normalized_checklist = _normalize_whitespace(checklist_text)
    payload = _run_gate_e_public_readiness_dry_run()

    assert "Gate E is deferred and blocked on `human_gate_e_approval`" in (
        normalized_checklist
    )
    assert "Gate E is not approved" in normalized_checklist
    assert "fresh human approval is still required" in normalized_checklist
    assert "This checklist is not a release plan" in normalized_checklist

    assert payload["gate_e_status"] == "human_approval_required"
    assert payload["decision"] == "blocked"
    assert payload["reason"] == "human_gate_e_approval_required"
    assert payload["human_gate_e_approval_required"] is True
    assert payload["public_github_approval_claimed"] is False
    for flag in FALSE_APPROVAL_FLAGS:
        assert payload[flag] is False


def test_release_hold_checklist_warns_for_cli_false_action_flags() -> None:
    checklist_text = CHECKLIST.read_text(encoding="utf-8")
    payload = _run_gate_e_public_readiness_dry_run()

    for warning in HELD_ACTION_WARNINGS:
        assert warning in checklist_text
    for flag in FALSE_ACTION_FLAGS:
        assert payload[flag] is False


def _run_gate_e_public_readiness_dry_run() -> dict[str, object]:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "async_scholar",
            "gate-e-public-readiness",
            "--dry-run",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    return json.loads(result.stdout)


def _checklist_review_items(
    checklist_text: str,
    *,
    heading: str,
) -> dict[str, str]:
    section = _markdown_section(checklist_text, heading=heading)
    return dict(re.findall(r"^- `([^`]+)`: ([a-z_]+)$", section, flags=re.MULTILINE))


def _markdown_section(markdown: str, *, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\r?\n(?P<section>.*?)(?=^## |\Z)",
        markdown,
        flags=re.DOTALL | re.MULTILINE,
    )

    assert match is not None, f"missing checklist section: {heading}"
    return match.group("section")


def _payload_satisfactory_review_items(payload: dict[str, object]) -> list[str]:
    satisfactory_review_items = [
        review_item
        for review_item in AI_SOLVED_REVIEW_ITEMS
        if payload[f"{review_item}_status"] == "satisfactory"
    ]
    assert set(satisfactory_review_items) == {
        key.removesuffix("_status")
        for key, value in payload.items()
        if key.endswith("_status") and value == "satisfactory"
    }
    return satisfactory_review_items


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())
