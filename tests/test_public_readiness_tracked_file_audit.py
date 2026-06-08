from __future__ import annotations

import subprocess
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_EXTENSIONS = {
    ".aac",
    ".flac",
    ".m4a",
    ".mkv",
    ".mov",
    ".mp3",
    ".mp4",
    ".ogg",
    ".wav",
    ".webm",
}
FORBIDDEN_FILENAMES = {
    ".mcp.json",
    "claude.md",
    "cookies.json",
    "cookiejar",
    "cookiejar.json",
    "gemini.md",
    "local state",
    "login_state.json",
    "mcp.json",
    "session_state.json",
    "state.json",
    "storage_state.json",
    "token.json",
    "tokens.json",
}
FORBIDDEN_SEGMENTS = {
    ".cursor",
    ".mcp",
    ".playwright-mcp",
    ".serena",
    ".superpowers",
    "auth",
    "browser-profile",
    "browser-profiles",
    "browser_profile",
    "browser_profiles",
    "cookies",
    "cookiejar",
    "debug",
    "debug-bundle",
    "debug-bundles",
    "debug_bundle",
    "debug_bundles",
    "downloads",
    "media",
    "profiles",
    "recordings",
    "screenshots",
    "session_state",
    "traces",
    "videos",
}


def test_tracked_file_audit_rejects_public_readiness_hazards() -> None:
    synthetic_tracked_paths = [
        ".env",
        "config/local.env",
        "browser_profile/storage_state.json",
        "auth/cookies.json",
        "data/sessions/private-session/events.jsonl",
        "debug/session-dump.zip",
        "artifacts/recordings/class-audio.wav",
        ".mcp.json",
        ".cursor/rules/project.md",
        ".superpowers/skills/example/SKILL.md",
        "agent/skills/public-readiness/SKILL.md",
        "skills/public-readiness/SKILL.md",
        ".codex/skills/public-readiness/SKILL.md",
        "CLAUDE.md",
        "GEMINI.md",
    ]

    flagged_paths = _forbidden_tracked_paths(synthetic_tracked_paths)

    assert flagged_paths == synthetic_tracked_paths


def test_tracked_file_audit_allows_legitimate_project_paths() -> None:
    synthetic_tracked_paths = [
        "AGENTS.md",
        "docs/public/index.md",
        "src/async_scholar/telegram_notifier.py",
        "src/async_scholar/audio/file_source.py",
        "tests/test_secret_sanitization.py",
        "tests/test_cookie_sanitization.py",
        "tests/fixtures/transcripts/attendance_roll_call.jsonl",
    ]

    assert _forbidden_tracked_paths(synthetic_tracked_paths) == []


def test_current_tracked_files_exclude_public_readiness_hazards() -> None:
    tracked_paths = _git_tracked_paths()

    assert "docs/checkpoint.md" not in tracked_paths
    assert _forbidden_tracked_paths(tracked_paths) == []


def _git_tracked_paths() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        check=False,
        capture_output=True,
        cwd=ROOT,
        text=True,
    )

    assert result.returncode == 0
    assert result.stderr == ""
    return result.stdout.splitlines()


def _forbidden_tracked_paths(tracked_paths: list[str]) -> list[str]:
    return [path for path in tracked_paths if _is_forbidden_public_readiness_path(path)]


def _is_forbidden_public_readiness_path(path: str) -> bool:
    normalized_path = path.replace("\\", "/").lower()
    pure_path = PurePosixPath(normalized_path)
    parts = pure_path.parts
    filename = pure_path.name

    return (
        _is_env_file(filename)
        or filename in FORBIDDEN_FILENAMES
        or pure_path.suffix in FORBIDDEN_EXTENSIONS
        or _has_forbidden_segment(parts)
        or _is_generated_session_data(parts)
        or _is_repo_local_skill(parts)
        or _is_cursor_rules_file(parts)
    )


def _is_env_file(filename: str) -> bool:
    return (
        filename == ".env" or filename.startswith(".env.") or filename.endswith(".env")
    )


def _has_forbidden_segment(parts: tuple[str, ...]) -> bool:
    return any(part in FORBIDDEN_SEGMENTS for part in parts)


def _is_generated_session_data(parts: tuple[str, ...]) -> bool:
    return len(parts) >= 2 and parts[0] == "data" and parts[1] == "sessions"


def _is_repo_local_skill(parts: tuple[str, ...]) -> bool:
    return (len(parts) >= 1 and parts[0] == "skills") or (
        len(parts) >= 2 and parts[0] in {".codex", "agent"} and parts[1] == "skills"
    )


def _is_cursor_rules_file(parts: tuple[str, ...]) -> bool:
    return len(parts) >= 2 and parts[0] == ".cursor" and parts[1] == "rules"
