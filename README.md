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

Current Gate D / Product Promise Alpha status: human-recorded pass for the
narrow local fixture-to-reviewer alpha demo only. That scope covers local
fixture input, completed session status, detected demo events,
confirmation-required alert preview, archive/reviewer metadata summary, Gate D
safety status, and explicit safety boundaries. It does not approve real Google
Meet or external meeting behavior, auth/profile/cookies/tokens, private meeting
data, audio capture, loopback/system/browser audio, browser/server launch,
browser automation, Playwright or in-app browser execution,
screenshots/traces/videos/downloads, live delivery, scheduler/background
execution, deletion/export execution, public release, autonomous participation,
academic-answer behavior, push, merge, or real deletion.

Run the local alpha fixture-only demo wrapper:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_local_alpha_fixture_demo.ps1
```

The wrapper runs the fixture demo, writes a local static dashboard export, and
builds the local Gate D evidence bundle and handoff packet metadata. It accepts
optional `-OutputRoot <local-output-root>`, `-DashboardOutput
<local-html-output>`, and `-SummaryOutput <local-summary-json>` paths. The
optional summary export writes a sanitized JSON summary with fixed local
fixture-only metadata; it does not include raw command output, private paths, or
raw Gate D JSON. It remains local fixture-only: it does not start a server, open
a browser, use private meeting data, deliver live alerts, perform real deletion,
record product judgment, replace product judgment evidence, broaden the
human-recorded narrow Gate D / Product Promise Alpha pass, or approve live
behavior. The summary export is an inspection aid only: it does not satisfy `product_judgment_evidence`,
does not replace product judgment evidence, and
does not pass Gate D / Product Promise Alpha by itself.

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

## Local Scheduler And Archive Workflow

The scheduler/archive commands are local, explicit, and manual. Use safe local
paths such as `data\async-scholar-local.sqlite`, `data\sessions`, and
`data\recovery-reports`; do not place secrets, private meeting URLs, private
transcript or audio contents, generated media contents, auth profiles, cookies,
or tokens in README examples or committed artifacts.

Save a manually entered course schedule into an explicit local SQLite path:

```powershell
uv run python -m async_scholar course-schedule-save-local --db-path data\async-scholar-local.sqlite --course-id cs101 --title "CS 101" --class-time monday,09:00,75,Asia/Manila,lecture
```

List the stored local course schedule metadata:

```powershell
uv run python -m async_scholar course-schedule-list-local --db-path data\async-scholar-local.sqlite
```

Preview which stored schedules are due by providing an explicit local clock:

```powershell
uv run python -m async_scholar scheduled-start-due-list-from-store-local session-001 --db-path data\async-scholar-local.sqlite --source-kind file --clock-day-of-week monday --clock-local-time 09:00
```

Preflight a due session window against local archive readiness:

```powershell
uv run python -m async_scholar session-window-readiness-preflight-from-store-local session-001 --db-path data\async-scholar-local.sqlite --archive-root data\sessions --source-kind file --clock-day-of-week monday --clock-local-time 09:00
```

Preflight the same due session window for user confirmation:

```powershell
uv run python -m async_scholar session-window-confirmation-preflight-from-store-local session-001 --db-path data\async-scholar-local.sqlite --archive-root data\sessions --source-kind file --clock-day-of-week monday --clock-local-time 09:00
```

Build non-executing start authorization metadata from a fixed user response:

```powershell
uv run python -m async_scholar session-window-start-authorization-from-store-local session-001 --db-path data\async-scholar-local.sqlite --archive-root data\sessions --source-kind file --clock-day-of-week monday --clock-local-time 09:00 --confirmation-response confirmed
```

Preflight a one-shot session-window execution decision without running it:

```powershell
uv run python -m async_scholar session-window-execution-preflight-from-store-local session-001 --db-path data\async-scholar-local.sqlite --archive-root data\sessions --source-kind file --clock-day-of-week monday --clock-local-time 09:00 --confirmation-response confirmed
```

Preflight a stored session-window stop decision without writing a stop receipt:

```powershell
uv run python -m async_scholar session-window-stop-execution-preflight-from-store-local session-001 --db-path data\async-scholar-local.sqlite --archive-root data\sessions --course-id cs101 --class-time-index 0 --source-kind file
```

Render read-only recovery report metadata for explicit local sessions:

```powershell
uv run python -m async_scholar session-window-recovery-report-local session-001 --archive-root data\sessions
```

Write a local metadata recovery report file under an explicit output root:

```powershell
uv run python -m async_scholar session-window-recovery-report-write-local session-001 --archive-root data\sessions --output-root data\recovery-reports
```

The schedule save command writes only manually entered schedule metadata to the
explicit SQLite path, and the recovery report write command writes only a local
metadata report file under the explicit output root. The preview, list,
preflight, authorization, and read-only recovery commands do not start a
background scheduler loop, create timers, run daemons, perform real online
monitoring, automate a browser, access browser auth/profile/cookie data, capture
audio, capture loopback or system audio, deliver live notifications, perform
real deletion, participate autonomously, answer academic questions, record or
broaden the narrow Gate D / Product Promise Alpha pass, or approve live
behavior.

Build the current local Gate D evidence bundle metadata:

```powershell
uv run python -m async_scholar gate-d-local-evidence-bundle
```

Build the local Gate D human handoff packet for metadata-only human review:

```powershell
uv run python -m async_scholar gate-d-handoff-packet-local
```

The Gate D handoff packet is a metadata-only human-review aid. It does not
replace, record, or prove human product judgment, and it does not broaden the
already recorded narrow Gate D / Product Promise Alpha pass.

For personal Gate D human demo inspection, use
`docs/public/gate-d-human-demo-inspection-runbook.md`. The runbook remains useful
for inspecting the same local fixture-to-reviewer demo scope; it does not expand
the recorded narrow pass or approve live behavior. Before the 2026-06-01 narrow
pass judgment, this review path was blocked on `product_judgment_evidence`;
that blocker term is kept here as historical context for the runbook, not as
the current project status.

For the current Gate E public-readiness boundary, see the Gate E deferred
readiness note at `docs/public/gate-e-deferred-readiness-note.md`. The note
records that AI-solvable review preparation is complete, Gate E remains blocked
on `human_gate_e_approval`, and Gate E is not approved.

For a one-page local public status snapshot, see
`docs/public/project-status-snapshot.md`. It summarizes the narrow local demo
status and deferred Gate E boundary; Gate E is not approved.

For local navigation across the public-readiness docs, see the local public docs
index at `docs/public/index.md`. Gate E is not approved.

For a one-command human walkthrough of the same local metadata evidence, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_gate_d_human_walkthrough.ps1
```

This one-command human walkthrough explains what each local step proves and
stops before Gate E approval, merge, push-to-main, and public release.

For a local human-facing alpha dashboard inspection surface, first dry-run the
launcher:

```powershell
uv run python -m async_scholar local-alpha-dashboard-inspection
uv run python -m async_scholar local-alpha-dashboard-static-demo --output "$env:TEMP\async-scholar-local-alpha-dashboard.html"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_local_alpha_dashboard_static_demo.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_local_alpha_dashboard_demo.ps1 -DryRun
uv run python -m async_scholar local-alpha-dashboard-demo --dry-run --host 127.0.0.1 --port 8086
```

The inspection command prints a no-server, no-browser plain-text summary of the
same fixed local demo story. The static HTML export writes a standalone local
file for browser inspection without starting a server or opening a browser; the
PowerShell wrapper creates a fresh temp HTML output path when `-Output` is not
provided. The dry run prints the loopback URL and a safety summary without
starting a server. Local loopback inspection is optional demo support and does
not broaden the recorded narrow pass. To inspect the dashboard locally, run the
same command without `--dry-run` and open the same loopback URL:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_local_alpha_dashboard_demo.ps1
uv run python -m async_scholar local-alpha-dashboard-demo --host 127.0.0.1 --port 8086
```

The dashboard uses fixed metadata-only demo sources for session status, detected
event summary, confirmation-required alert preview, archive/reviewer metadata,
and the Gate D safety panel. It is local inspection support only: it does not
read private transcripts, recordings, meeting links, auth profiles, cookies, or
tokens; it does not perform real online monitoring, browser automation, capture,
live delivery, deletion/export, autonomous participation, or academic-answer
behavior; and it does not replace product judgment evidence, broaden the
human-recorded narrow Gate D / Product Promise Alpha pass, or approve live
behavior. The dashboard support surfaces do not pass Gate D / Product Promise
Alpha by themselves.

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
