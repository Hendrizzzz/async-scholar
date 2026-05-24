# Gate D Loopback / Playwright Spike Rollback Plan

## Status

This document is a prerequisite safety plan only. It does not approve Gate D,
Product Promise Alpha, browser automation, Playwright installation, loopback or
system audio capture, browser audio capture, real meeting access, live delivery,
public release, autonomous participation, or academic-answer behavior.

Any future loopback / Playwright spike requires a separate ticket, fresh Staff
Architect, Security & Privacy, Browser Specialist, and Audio/STT Specialist
reviews when applicable, explicit user approval for the exact execution scope,
and a new QA pass before any execution.

## Scope

The rollback boundary covers only a future, reviewed spike that may evaluate
synthetic browser behavior or loopback feasibility. Mocked and synthetic tests
must be labeled as synthetic evidence only. Synthetic evidence must not be used
as proof of real Google Meet behavior, real external meeting behavior, real
browser profile handling, real auth handling, real loopback capture, or Gate D
readiness.

The spike must not touch real Google Meet, real external meeting platforms,
real accounts, cookies, browser profiles, saved auth state, private class data,
microphone/camera permissions, system or browser audio capture, live
notification delivery, cloud upload, deletion/export execution, public release,
or push unless a later ticket explicitly approves that exact action.

## Rollback Triggers

Trigger rollback immediately if any of these occur:

- A dependency, browser binary, profile directory, auth state file, cookie file,
  or generated artifact appears outside the approved spike paths.
- Any code attempts to open a real meeting URL, account login, saved profile,
  auth state, cookie, private transcript, private recording, or private meeting
  metadata.
- Any prompt requests microphone, camera, loopback, system audio, monitor
  output, browser audio, or hardware access outside the approved ticket scope.
- Any behavior attempts live notification delivery, participation messaging,
  autonomous answers, cloud upload, public release, push, or real deletion.
- A test requires private data, real accounts, real meetings, or manual product
  judgment to pass.
- Browser automation becomes flaky in a way that could contact external sites,
  persist private state, or hide failure behind retries.
- The spike starts making Gate D / Product Promise Alpha pass claims instead of
  collecting bounded evidence for later review.

## Disable Strategy

A future spike must have one explicit off switch before it can run:

- Prefer a command-level disabled flag or explicit dry-run mode that performs
  no browser launch and no capture.
- Keep any spike command opt-in. Do not add background loops, timers, daemons,
  recurring jobs, or autonomous monitors.
- Default configs must remain non-executing. Any executing path must require a
  deliberate command invocation and the reviewed ticket's exact flags.
- If the off switch is missing, ambiguous, or bypassed by tests, stop the spike
  and revert the spike changes.

## Dependency Rollback

If a later reviewed ticket allows browser or loopback dependencies, rollback
must restore dependency files to the pre-spike state:

- Remove only dependencies introduced by that spike from `pyproject.toml` and
  `uv.lock`.
- Re-run the ticket's dependency and test verification commands after rollback.
- Do not keep unused Playwright, browser, loopback, audio, OCR, Tauri, FastAPI,
  or platform integration dependencies.
- Do not install system packages or browser binaries as an unreviewed fix.

## Browser Binary And Profile Cleanup

Future browser work must use disposable, synthetic-only state. Rollback cleanup
must inventory and remove only reviewed spike-owned browser artifacts:

- Playwright-managed browser cache entries created by the scoped spike.
- Temporary browser profiles created under the scoped ignored local root.
- Traces, screenshots, videos, HAR files, console logs, and debug logs created
  by the spike.
- Any accidental auth state, cookie, saved profile, or private browser data must
  be treated as a security incident: stop, do not commit it, do not copy it into
  checkpoint prose, and request the required human/security decision before any
  cleanup outside the approved temp or ignored roots.

Do not use a real user browser profile. Do not persist browser auth state. Do
not commit browser artifacts.

## Artifact Inventory And Cleanup

Before rollback, record a metadata-only inventory of spike-owned artifacts:

- Relative path under the approved ignored root.
- Artifact kind, such as trace, screenshot, log, temp profile, cache marker, or
  synthetic fixture.
- Size and count metadata when available.
- Whether the artifact is confirmed synthetic.

Do not record transcript text, audio contents, screenshots containing private
data, private URLs, tokens, cookies, or auth state in the checkpoint. Cleanup may
only remove spike-owned artifacts under approved temp or ignored roots unless a
later human-approved ticket explicitly authorizes broader cleanup.

## Secret, Auth, And Private-Data Handling

The rollback path must fail closed for secrets and private data:

- Never read, print, store, summarize, or commit `.env` values, tokens, cookies,
  saved auth state, browser profiles, private meeting links, private
  transcripts, private recordings, or generated media.
- If private data is detected, stop the spike, preserve only metadata needed for
  review, and do not continue with automated cleanup outside approved roots.
- Checkpoints may mention only privacy-safe scalar metadata and pass/fail
  status. They must not contain private contents.
- Public/open samples and synthetic fixtures must remain clearly identified as
  non-private evidence.

## Confirmation And Policy Gates

Participation-related behavior remains behind policy gates:

- No unconfirmed participation messages.
- No secret attendance impersonation.
- No fake excuses.
- No autonomous answers to academic questions.
- No live delivery without a later reviewed ticket and explicit user
  confirmation.

If any spike behavior approaches participation, attendance, academic answers, or
live delivery, stop and request a narrower reviewed ticket.

## Verification Commands

Rollback or rollback-plan changes should keep the baseline project checks green:

```powershell
uv run python -m async_scholar --help
uv run pytest tests/test_gate_d_readiness.py tests/test_cli.py -q
uv run pytest
uv run ruff check .
uv run ruff format --check .
git status --short
```

If a future spike changes dependencies, add the ticket-specific dependency
verification commands from that ticket.

## Manual Checks

Manual checks are only for a later approved spike. They must not be treated as
completed by this document. A later ticket must define objective checks for:

- Confirming no real browser profile, auth state, cookies, or private browser
  data were used.
- Confirming no real meeting or external class platform was contacted.
- Confirming no microphone, camera, loopback, system audio, or browser audio
  permission was requested unless that exact permission was approved.
- Confirming all generated artifacts are synthetic, ignored, and excluded from
  Git.
- Confirming Gate D / Product Promise Alpha remains not passed unless a
  dedicated gate decision ticket explicitly passes it.

## Stop Conditions

Stop and fail closed if the spike needs any of the following without a fresh,
explicit approval:

- Real Google Meet or any real external meeting/class platform.
- Real account login, cookies, saved browser profile, auth/profile state, or
  private browser data.
- Microphone, camera, loopback, system audio, browser audio, monitor output, or
  hardware access.
- Secrets, `.env`, tokens, credentials, private transcripts, private
  recordings, private meeting data, or generated media contents.
- Live notification delivery, cloud upload, public release, push, real deletion,
  export execution, autonomous participation, or academic-answer behavior.
- Manual product judgment about whether Gate D / Product Promise Alpha is good
  enough for demo.

These stop conditions are true human-only gates unless a later ticket has
already narrowed and explicitly approved the exact action.
