from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README_PATH = "README.md"
PUBLIC_DOC_PREFIX = "docs/public/"
COMMAND_FENCE_LANGUAGES = frozenset(
    {"bash", "cmd", "console", "powershell", "ps1", "pwsh", "sh", "shell"}
)


@dataclass(frozen=True)
class PublicReadinessDoc:
    repo_path: str
    text: str


def test_public_readiness_docs_are_discovered_from_tracked_files_only() -> None:
    paths = _tracked_public_readiness_doc_paths()

    assert README_PATH in paths
    assert any(path.startswith(PUBLIC_DOC_PREFIX) for path in paths)
    assert "docs/checkpoint.md" not in paths
    assert all(
        path == README_PATH
        or (path.startswith(PUBLIC_DOC_PREFIX) and path.endswith(".md"))
        for path in paths
    )


def test_local_public_readiness_markdown_references_exist() -> None:
    paths = _tracked_public_readiness_doc_paths()
    docs = _read_public_readiness_docs(paths)

    missing_references: dict[str, list[str]] = {}
    for doc in docs:
        missing = _missing_local_public_doc_references(doc.text, paths)
        if missing:
            missing_references[doc.repo_path] = missing

    assert missing_references == {}


def test_public_docs_do_not_reference_external_urls() -> None:
    docs = _read_public_readiness_docs(_tracked_public_readiness_doc_paths())

    external_urls = {
        doc.repo_path: _external_urls(doc.text)
        for doc in docs
        if _is_public_doc(doc.repo_path) and _external_urls(doc.text)
    }

    assert external_urls == {}


def test_public_readiness_docs_do_not_reference_private_or_generated_paths() -> None:
    docs = _read_public_readiness_docs(_tracked_public_readiness_doc_paths())

    unsafe_references: dict[str, list[str]] = {}
    for doc in docs:
        unsafe = _unsafe_path_references(
            doc.text, include_generated_artifact_paths=_is_public_doc(doc.repo_path)
        )
        if unsafe:
            unsafe_references[doc.repo_path] = unsafe

    assert unsafe_references == {}


def test_public_docs_do_not_present_executable_command_fences() -> None:
    docs = _read_public_readiness_docs(_tracked_public_readiness_doc_paths())

    command_blocks = {
        doc.repo_path: _command_fenced_blocks(doc.text)
        for doc in docs
        if _is_public_doc(doc.repo_path) and _command_fenced_blocks(doc.text)
    }

    assert command_blocks == {}


def test_public_readiness_docs_do_not_claim_gate_e_or_release_approval() -> None:
    docs = _read_public_readiness_docs(_tracked_public_readiness_doc_paths())

    unsafe_claims_by_doc: dict[str, list[str]] = {}
    for doc in docs:
        unsafe_claims = _unsafe_approval_claims(doc.text)
        if unsafe_claims:
            unsafe_claims_by_doc[doc.repo_path] = unsafe_claims

    assert unsafe_claims_by_doc == {}


def test_reference_integrity_detectors_reject_synthetic_unsafe_examples() -> None:
    tracked_paths = (README_PATH, f"{PUBLIC_DOC_PREFIX}index.md")

    assert _missing_local_public_doc_references(
        "See docs/public/missing-public-note.md for details.", tracked_paths
    ) == ["docs/public/missing-public-note.md"]
    assert _external_urls("See https://example.invalid/status") == [
        "https://example.invalid/status"
    ]
    assert _command_fenced_blocks("```powershell\nuv run pytest\n```") == ["powershell"]

    unsafe_text = "\n".join(
        (
            r"`C:\Users\person\AsyncScholar\.env`",
            "`~/async-scholar/auth/profile/storage-state.json`",
            r"`\\server\share\cookies.json`",
            "`debug/private-trace.zip`",
            "`screenshots/private-demo.png`",
            "`browser/profile/Default/Local State`",
            "`data/sessions/private-class/recording.wav`",
            "`secrets/client_secret.json`",
        )
    )
    unsafe_references = _unsafe_path_references(unsafe_text)

    assert len(unsafe_references) == 8


def _tracked_public_readiness_doc_paths() -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "ls-files", "--", README_PATH, f"{PUBLIC_DOC_PREFIX}*.md"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(
        sorted(line.strip().replace("\\", "/") for line in result.stdout.splitlines())
    )


def _read_public_readiness_docs(
    repo_paths: tuple[str, ...],
) -> tuple[PublicReadinessDoc, ...]:
    return tuple(
        PublicReadinessDoc(repo_path, (ROOT / repo_path).read_text(encoding="utf-8"))
        for repo_path in repo_paths
    )


def _missing_local_public_doc_references(
    markdown: str, tracked_paths: tuple[str, ...]
) -> list[str]:
    tracked = set(tracked_paths)
    references = sorted(set(_local_public_doc_references(markdown)))
    return [reference for reference in references if reference not in tracked]


def _local_public_doc_references(markdown: str) -> list[str]:
    return re.findall(
        r"(?<![\w/.-])(?:README\.md|docs/public/[A-Za-z0-9][A-Za-z0-9_.-]*\.md)"
        r"(?![\w/.-])",
        markdown,
    )


def _external_urls(markdown: str) -> list[str]:
    return re.findall(r"https?://[^\s)>\]]+", markdown)


def _unsafe_path_references(
    markdown: str, *, include_generated_artifact_paths: bool = True
) -> list[str]:
    candidates = _path_like_reference_candidates(markdown)
    return [
        candidate
        for candidate in candidates
        if _unsafe_path_reference_reason(
            candidate,
            include_generated_artifact_paths=include_generated_artifact_paths,
        )
        is not None
    ]


def _path_like_reference_candidates(markdown: str) -> list[str]:
    candidates: list[str] = []

    for target in re.findall(r"\[[^\]]+\]\(([^)\s]+)", markdown):
        if not _is_external_reference(target):
            candidates.append(target)

    for inline_code in re.findall(r"`([^`\r\n]+)`", markdown):
        if _looks_path_like(inline_code):
            candidates.append(inline_code)

    candidates.extend(_local_public_doc_references(markdown))

    concrete_absolute_paths = re.findall(
        r"(?:[A-Za-z]:[\\/][^\s`'\"<>)]*|\\\\[^\s`'\"<>)]*)", markdown
    )
    candidates.extend(concrete_absolute_paths)

    return sorted(
        set(_strip_reference_punctuation(candidate) for candidate in candidates)
    )


def _looks_path_like(candidate: str) -> bool:
    normalized = candidate.replace("\\", "/")
    return (
        "/" in normalized
        or normalized in {README_PATH, ".env"}
        or normalized.endswith(".md")
        or normalized.endswith(".json")
        or normalized.endswith(".sqlite")
        or normalized.endswith(".wav")
        or normalized.endswith(".mp3")
        or normalized.endswith(".mp4")
        or normalized.endswith(".zip")
        or normalized.endswith(".pem")
        or normalized.endswith(".key")
    )


def _unsafe_path_reference_reason(
    candidate: str, *, include_generated_artifact_paths: bool
) -> str | None:
    normalized = _strip_reference_punctuation(candidate).replace("\\", "/")
    lower = normalized.lower()

    if re.match(r"^[a-z]:/", lower):
        return "absolute Windows path"
    if lower.startswith("//"):
        return "UNC path"
    if lower.startswith(("~/", "$home/", "%userprofile%/")):
        return "home directory path"
    if lower == ".env" or "/.env" in lower or lower.endswith(".env"):
        return ".env path"
    private_artifact_prefixes = (
        "auth/",
        "browser/",
        "cookies/",
        "profiles/",
        "secrets/",
    )
    generated_artifact_prefixes = (
        "data/sessions/",
        "debug/",
        "downloads/",
        "media/",
        "recordings/",
        "screenshots/",
        "traces/",
        "videos/",
    )
    if any(lower.startswith(prefix) for prefix in private_artifact_prefixes):
        return "private local path"
    if include_generated_artifact_paths and any(
        lower.startswith(prefix) for prefix in generated_artifact_prefixes
    ):
        return "generated artifact path"
    if any(marker in lower for marker in ("/auth/", "/browser/", "/cookies/")):
        return "auth/browser/cookie path"
    if any(
        secret_name in lower
        for secret_name in (
            "client_secret",
            "credentials.json",
            "cookies.json",
            "local state",
            "storage-state",
            "storage_state",
            "token.json",
        )
    ):
        return "secret-like local path"
    if re.search(r"\.(key|p12|pem)(?:$|[/?#])", lower):
        return "secret key path"
    if include_generated_artifact_paths and re.search(
        r"\.(aac|flac|m4a|mov|mp3|mp4|ogg|wav|webm)(?:$|[/?#])", lower
    ):
        return "media artifact path"

    return None


def _command_fenced_blocks(markdown: str) -> list[str]:
    blocks: list[str] = []
    for match in re.finditer(
        r"```(?P<language>[A-Za-z0-9_-]*)[ \t]*\r?\n(?P<body>.*?)```",
        markdown,
        flags=re.DOTALL,
    ):
        language = match.group("language").lower()
        body = match.group("body")
        if language in COMMAND_FENCE_LANGUAGES or _body_looks_executable(body):
            blocks.append(language or "<unlabeled>")
    return blocks


def _body_looks_executable(body: str) -> bool:
    executable_prefixes = (
        "New-Item ",
        "powershell ",
        "python -m ",
        "uv run ",
    )
    return any(
        line.strip().startswith(executable_prefixes)
        for line in body.splitlines()
        if line.strip()
    )


def _unsafe_approval_claims(markdown: str) -> list[str]:
    normalized = " ".join(markdown.split())
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
        "push-ready",
        "ready to push",
        "greenlit",
        "launch-ready",
    )
    return [claim for claim in unsafe_claims if claim in normalized]


def _is_public_doc(repo_path: str) -> bool:
    return repo_path.startswith(PUBLIC_DOC_PREFIX)


def _is_external_reference(target: str) -> bool:
    return bool(re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", target))


def _strip_reference_punctuation(candidate: str) -> str:
    return candidate.strip().strip(".,;:)]}\"'")
