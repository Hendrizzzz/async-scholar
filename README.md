# AsyncScholar

Local-first lecture monitoring, alerting, archiving, and study-review generation.

This repository starts with a small scaffold for the first implementation milestone:

```text
transcript fixture -> event detected -> fake alert -> reviewer.md
audio file -> transcript -> event detected -> reviewer
```

## Product Direction

AsyncScholar is designed to become a local-first app that monitors lectures, detects important moments, alerts the user, stores lecture artifacts, and generates study material.

The final product target includes silent online lecture monitoring, but the build order starts with safer, testable pieces:

```text
fixtures -> files -> VAD -> mic -> alerts -> UI -> scheduler -> online monitoring alpha
```

## Safety Boundary

This project supports lecture assistance: monitoring, transcription, alerts, study review, and user-confirmed participation assistance.

It does not implement secret attendance impersonation, fake excuses, unconfirmed participation messages, or autonomous answers to academic questions.

## Setup

Install/sync the development environment with `uv`:

```powershell
uv sync
```

## Usage

Show CLI help:

```powershell
uv run python -m async_scholar --help
```

Run the verification checks:

```powershell
uv run pytest
uv run ruff check .
uv run ruff format --check .
```
