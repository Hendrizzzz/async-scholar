from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT_PATH = "docs/checkpoint.md"

BINARY_SUFFIXES = {
    ".bmp",
    ".db",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".pdf",
    ".png",
    ".pyc",
    ".sqlite",
    ".zip",
}
PRIVATE_PATH_SEGMENTS = {
    ".playwright-mcp",
    ".serena",
    "auth",
    "browser-profile",
    "browser-profiles",
    "browser_profile",
    "browser_profiles",
    "cookies",
    "debug",
    "debug-bundle",
    "debug-bundles",
    "downloads",
    "media",
    "profiles",
    "recordings",
    "screenshots",
    "session_state",
    "traces",
    "videos",
}
PRIVATE_FILENAMES = {
    ".env",
    "cookies.json",
    "cookiejar",
    "cookiejar.json",
    "local state",
    "login_state.json",
    "session_state.json",
    "state.json",
    "storage_state.json",
    "token.json",
    "tokens.json",
}
SECRET_MARKERS = (
    (
        "private-key-block",
        re.compile(
            r"-{5}BEGIN [A-Z0-9 ]*PRIVATE KEY-{5}[\s\S]+?-{5}END "
            r"[A-Z0-9 ]*PRIVATE KEY-{5}",
        ),
    ),
    ("aws-access-key-id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("openai-api-key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{30,}\b")),
    ("anthropic-api-key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{30,}\b")),
    ("github-token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}\b")),
    ("github-fine-grained-token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("gitlab-token", re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    (
        "stripe-secret-key",
        re.compile(r"\bsk_(?:live|test)_[0-9A-Za-z]{24,}\b"),
    ),
    (
        "sendgrid-api-key",
        re.compile(r"\bSG\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\b"),
    ),
    (
        "sensitive-env-value",
        re.compile(
            r"(?im)^\s*(?:OPENAI_API_KEY|ANTHROPIC_API_KEY|GITHUB_TOKEN|"
            r"SLACK_BOT_TOKEN|STRIPE_SECRET_KEY|SENDGRID_API_KEY|"
            r"AWS_SECRET_ACCESS_KEY|GOOGLE_API_KEY|CLIENT_SECRET|"
            r"PRIVATE_KEY|SESSION_SECRET)\s*=\s*(?!<|\$\{|REDACTED|"
            r"redacted|example|placeholder|dummy|test\b|fake\b|"
            r"\*{3,})(?:[\"']?[A-Za-z0-9_./+=:@-]{24,}[\"']?)\s*$",
        ),
    ),
    (
        "playwright-storage-state-json",
        re.compile(
            '"'
            + "cook"
            + "ies"
            + r'"\s*:\s*\[\s*\{[\s\S]{0,2000}?"'
            + "same"
            + "Site"
            + r'"\s*:[\s\S]{0,2000}?"'
            + "ori"
            + "gins"
            + r'"\s*:\s*\[',
        ),
    ),
    (
        "browser-local-state-json",
        re.compile(
            '"'
            + "os"
            + "_crypt"
            + r'"\s*:\s*\{[\s\S]{0,1000}?"'
            + "encrypted"
            + "_key"
            + r'"\s*:',
        ),
    ),
    (
        "netscape-cookie-jar",
        re.compile(
            r"(?im)^# Netscape HTTP Cookie File[\s\S]{0,2000}?\t(?:TRUE|FALSE)\t",
        ),
    ),
    (
        "mcp-server-config",
        re.compile(
            '"'
            + "mcp"
            + "Servers"
            + r'"\s*:\s*\{[\s\S]{0,1000}?"'
            + "command"
            + r'"\s*:',
        ),
    ),
)


@dataclass(frozen=True)
class TextFinding:
    path: str
    marker: str


def test_secret_marker_detector_rejects_high_confidence_examples() -> None:
    synthetic_markers = {
        "private-key-block": "\n".join(
            [
                "-----" + "BEGIN RSA PRIVATE KEY" + "-----",
                "MII" + ("A" * 64),
                "-----" + "END RSA PRIVATE KEY" + "-----",
            ]
        ),
        "openai-api-key": "OPENAI_API_KEY=" + _token("sk-", "a", 48),
        "aws-access-key-id": "AWS_ACCESS_KEY_ID=" + _token("AKIA", "A", 16),
        "playwright-storage-state-json": json.dumps(
            {
                _key("cook", "ies"): [
                    {
                        "name": "sid",
                        "value": _token("cookie-", "b", 32),
                        "domain": "example.invalid",
                        "path": "/",
                        _key("same", "Site"): "Lax",
                    }
                ],
                _key("ori", "gins"): [{"origin": "https://example.invalid"}],
            }
        ),
        "browser-local-state-json": json.dumps(
            {
                _key("os", "_crypt"): {
                    _key("encrypted", "_key"): _token("DPAPI", "C", 48)
                }
            }
        ),
        "netscape-cookie-jar": "\n".join(
            [
                "# " + "Netscape HTTP Cookie File",
                ".example.invalid\tTRUE\t/\tFALSE\t0\tsid\t" + _token("", "d", 32),
            ]
        ),
        "mcp-server-config": json.dumps(
            {_key("mcp", "Servers"): {"local": {_key("comm", "and"): "node"}}}
        ),
    }

    flagged_markers = {
        finding.marker
        for text in synthetic_markers.values()
        for finding in _secret_marker_findings("synthetic.txt", text)
    }

    assert flagged_markers >= set(synthetic_markers)


def test_secret_marker_detector_allows_safe_boundary_examples() -> None:
    safe_examples = [
        "AGENTS.md says tokens, cookies, auth state, and .env files are forbidden.",
        "OPENAI_API_KEY=<redacted>",
        "GITHUB_TOKEN=${GITHUB_TOKEN}",
        "CLIENT_SECRET=placeholder-client-secret",
        "SESSION_SECRET=***",
        json.dumps({_key("cook", "ies"): [], _key("ori", "gins"): []}),
        json.dumps({_key("mcp", "Servers"): {}}),
    ]

    assert [
        finding
        for example in safe_examples
        for finding in _secret_marker_findings("safe.txt", example)
    ] == []


def test_tracked_text_candidates_use_git_inventory_and_skip_private_paths() -> None:
    tracked_paths = [
        "AGENTS.md",
        CHECKPOINT_PATH,
        "src/async_scholar/__main__.py",
        "data/sessions/local/events.jsonl",
        "browser_profile/storage_state.json",
        "tests/test_public_readiness_tracked_text_audit.py",
    ]

    assert _tracked_text_candidate_paths(tracked_paths) == [
        "AGENTS.md",
        "src/async_scholar/__main__.py",
        "tests/test_public_readiness_tracked_text_audit.py",
    ]


def test_audit_file_does_not_self_trigger() -> None:
    audit_path = Path(__file__).resolve()

    audit_text = _read_tracked_text_file(audit_path)

    assert audit_text is not None
    assert _secret_marker_findings(_relative_posix_path(audit_path), audit_text) == []


def test_tracked_symlink_candidates_are_skipped_before_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    symlink_candidate = ROOT / "src" / "async_scholar" / "__main__.py"
    resolved_target = ROOT / "README.md"
    original_is_symlink = Path.is_symlink
    original_resolve = Path.resolve

    def fake_is_symlink(path: Path) -> bool:
        if path == symlink_candidate:
            return True
        return original_is_symlink(path)

    def fake_resolve(path: Path) -> Path:
        if path == symlink_candidate:
            return resolved_target
        return original_resolve(path)

    def fail_if_read(path: Path) -> bytes:
        if path == resolved_target:
            raise AssertionError("symlink candidate was read")
        return b""

    monkeypatch.setattr(Path, "is_symlink", fake_is_symlink)
    monkeypatch.setattr(Path, "resolve", fake_resolve)
    monkeypatch.setattr(Path, "read_bytes", fail_if_read)

    assert _secret_marker_findings_for_paths(["src/async_scholar/__main__.py"]) == []


def test_current_tracked_text_files_exclude_secret_markers() -> None:
    tracked_paths = _git_tracked_paths()
    candidate_paths = _tracked_text_candidate_paths(tracked_paths)

    assert CHECKPOINT_PATH not in candidate_paths
    assert _secret_marker_findings_for_paths(candidate_paths) == []


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


def _tracked_text_candidate_paths(tracked_paths: list[str]) -> list[str]:
    return [
        path
        for path in tracked_paths
        if path != CHECKPOINT_PATH and not _is_private_or_binary_path(path)
    ]


def _secret_marker_findings_for_paths(paths: list[str]) -> list[TextFinding]:
    findings: list[TextFinding] = []
    for path in paths:
        tracked_path = ROOT / path
        if tracked_path.is_symlink():
            continue
        absolute_path = tracked_path.resolve()
        if not _is_inside_repo(absolute_path) or absolute_path.is_symlink():
            continue
        text = _read_tracked_text_file(absolute_path)
        if text is None:
            continue
        findings.extend(_secret_marker_findings(path, text))
    return findings


def _secret_marker_findings(path: str, text: str) -> list[TextFinding]:
    return [
        TextFinding(path=path, marker=marker)
        for marker, pattern in SECRET_MARKERS
        if pattern.search(text) is not None
    ]


def _read_tracked_text_file(path: Path) -> str | None:
    data = path.read_bytes()
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _is_private_or_binary_path(path: str) -> bool:
    normalized_path = path.replace("\\", "/").lower()
    pure_path = PurePosixPath(normalized_path)
    parts = pure_path.parts
    filename = pure_path.name

    return (
        pure_path.suffix in BINARY_SUFFIXES
        or _is_env_file(filename)
        or filename in PRIVATE_FILENAMES
        or _has_private_segment(parts)
        or _is_generated_session_data(parts)
    )


def _is_env_file(filename: str) -> bool:
    return (
        filename == ".env" or filename.startswith(".env.") or filename.endswith(".env")
    )


def _has_private_segment(parts: tuple[str, ...]) -> bool:
    return any(part in PRIVATE_PATH_SEGMENTS for part in parts)


def _is_generated_session_data(parts: tuple[str, ...]) -> bool:
    return len(parts) >= 2 and parts[0] == "data" and parts[1] == "sessions"


def _is_inside_repo(path: Path) -> bool:
    try:
        path.relative_to(ROOT)
    except ValueError:
        return False
    return True


def _relative_posix_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _token(prefix: str, repeated: str, count: int) -> str:
    return prefix + (repeated * count)


def _key(*fragments: str) -> str:
    return "".join(fragments)
