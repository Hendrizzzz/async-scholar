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

Run the transcript fixture demo:

```powershell
uv run python -m async_scholar fixture-demo tests\fixtures\transcripts\attendance_roll_call.jsonl --output-root data\sessions
```

The demo loads the fixture, runs deterministic event detection, and writes generated artifacts under:

```text
data/sessions/fixture_attendance_roll_call/events.jsonl
data/sessions/fixture_attendance_roll_call/alerts.log
data/sessions/fixture_attendance_roll_call/reviewer.md
```

Preview a scheduled start decision without starting a scheduler:

```powershell
uv run python -m async_scholar scheduled-start-preview-local session-001 --course-id cs101 --day-of-week monday --local-start-time 09:00 --duration-minutes 75 --source-kind file --clock-day-of-week monday --clock-local-time 09:00
```

This command uses only explicit CLI metadata and an explicit local clock, then
prints one metadata-only JSON preview. It does not read schedule files, infer the
current time, start timers or background workers, launch a scheduler, open a
browser, access audio, send notifications, read or write artifacts, or approve
Gate D / Product Promise Alpha behavior. Real scheduler execution and live
delivery remain blocked.

Show read-only crash recovery preflight metadata for one explicit local session root:

```powershell
uv run python -m async_scholar crash-recovery-preflight fixture_attendance_roll_call --sessions-root data\sessions
```

This command returns a metadata-only JSON summary for allowlisted session
artifacts. It does not repair, clean up, delete, copy, export, schedule, or
deliver anything, and it does not read artifact contents.

Show read-only archive export preflight metadata for one explicit local session
archive root:

```powershell
uv run python -m async_scholar archive-export-preflight fixture_attendance_roll_call --archive-root data\sessions
```

This command returns a metadata-only JSON summary for allowlisted session
artifacts. It does not copy, export, delete, schedule, deliver, monitor, or read
artifact contents.

Copy allowlisted archive artifacts for one explicit local session into an
explicit existing local export root:

```powershell
New-Item -ItemType Directory -Path data\archive-export-smoke
uv run python -m async_scholar archive-export-local fixture_attendance_roll_call --archive-root data\sessions --export-root data\archive-export-smoke
```

This command copies only allowlisted local archive artifacts into the selected
export root and prints a metadata-only JSON summary. It does not delete, move,
upload, schedule, notify, browse, monitor, or read or print artifact contents.

Verify one explicit local archive export using metadata only:

```powershell
uv run python -m async_scholar archive-export-verify-local fixture_attendance_roll_call --archive-root data\sessions --export-root data\archive-export-smoke
```

This command compares allowlisted artifact presence and sizes between the
archive root and export root, then prints a metadata-only JSON summary. It does
not copy, move, delete, upload, schedule, notify, browse, monitor, or read or
print artifact contents.

Preview a read-only local archive delete dry run for one explicit local session:

```powershell
uv run python -m async_scholar archive-delete-dry-run-local fixture_attendance_roll_call --archive-root data\sessions
```

This command inspects only allowlisted artifact presence and sizes, then prints
a content-free metadata JSON summary with `dry_run_only=true` and
`deletion_performed=false`. It does not delete, move, copy, clean, upload,
schedule, notify, browse, monitor, or read or print artifact contents; real
deletion remains blocked.

Show the bounded microphone recording diagnostic options:

```powershell
uv run python -m async_scholar mic-recording-diagnostic --help
```

This command is diagnostic-only. Help is lazy and does not open a microphone
stream or write files. Actual recording happens only when the diagnostic is
explicitly invoked; it writes bounded local ignored artifacts such as
`microphone.wav` and `diagnostic-report.json` under the selected output root.
Treat diagnostic audio as private local data and do not commit or share it.

Run the verification checks:

```powershell
uv run pytest
uv run ruff check .
uv run ruff format --check .
```
