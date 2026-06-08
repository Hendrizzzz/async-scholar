# Gate D Human Demo Inspection Runbook

Gate D / Product Promise Alpha has a human-recorded narrow local pass for the
fixture-to-reviewer demo only. Gate E public readiness remains blocked, and
human Gate E approval is deferred.

This runbook is a local human demo inspection aid. Do not treat this runbook as
Gate E approval, public release approval, push approval, merge approval, or
permission for live/private/browser/audio behavior.

Do not treat this runbook as Gate E approval.

## Scope

Use this runbook only to inspect the local metadata evidence behind the already
recorded narrow Gate D pass. AI-solvable public-readiness preparation stops before Gate E approval,
merge, push-to-main, public release, repository visibility changes, or public
exposure.

This runbook does not require or approve real Google Meet, external meeting
platforms, auth/profile/cookies, private meeting data, browser automation,
loopback/system audio, live delivery, real deletion, push, merge, public
release, secrets, tokens, private transcripts, private recordings,
VAD/STT/model execution, microphone use, participation actions, or
academic-answer behavior.

## Automated Evidence

What the automated commands can show:

- The CLI is available.
- The current local alpha dry run records the narrow local Gate D pass.
- Historical Gate D bundle and handoff helpers still provide pre-pass context.
- The local scheduler/archive smoke can run in a temporary work root while
  staying metadata-only and local.

What only the user can decide:

- Whether to approve Gate E public readiness.
- Whether to merge, push-to-main, expose the repository publicly, or release.
- Whether broader/live/private/external-service product behavior should proceed.

For local metadata checks, inspect the CLI help, local alpha dashboard dry run,
Gate D evidence bundle, and Gate D handoff packet surfaces. The corresponding
local command references are `uv run python -m async_scholar --help`,
`uv run python -m async_scholar local-alpha-dashboard-demo --dry-run`,
`uv run python -m async_scholar gate-d-local-evidence-bundle`, and
`uv run python -m async_scholar gate-d-handoff-packet-local`.

For the local scheduler/archive workflow smoke, use the local PowerShell smoke
script reference `scripts\run_scheduler_archive_workflow_smoke.ps1` with an
explicit temporary `-WorkRoot` such as
`$env:TEMP\async-scholar-gate-d-human-demo-runbook-smoke`.

The smoke command may create local temp metadata artifacts under the selected
`-WorkRoot`. Do not commit those artifacts.

## One-Command Human Walkthrough

If the individual CLI commands still feel too internal, run the one-command
human walkthrough. It wraps the same local metadata checks, explains what each
step proves, treats the older Gate D bundle and handoff outputs as historical
pre-pass helper signals, and stops before Gate E approval.

The local command reference is
`powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_gate_d_human_walkthrough.ps1`.

To keep all temporary metadata artifacts under a chosen local root, use the same
local walkthrough script with an explicit `-WorkRoot` such as
`$env:TEMP\async-scholar-gate-d-human-walkthrough`.

Sample expected walkthrough readout:

```text
AsyncScholar Gate D narrow local pass walkthrough
Step 1 - CLI availability
What this proves: the local AsyncScholar CLI can be reached.
Step 2 - Current narrow Gate D status
Result: narrow local Gate D / Product Promise Alpha pass is recorded for the fixture-to-reviewer demo only.
Step 3 - Historical Gate D evidence bundle
Result: historical Gate D bundle still reports product_judgment_evidence as a pre-pass blocker.
Step 4 - Historical handoff packet
Result: historical handoff packet remains a pre-pass manual review aid.
Step 5 - Local scheduler/archive workflow smoke
Temporary artifact root: <local temp path>\scheduler-archive-smoke
Next human-only boundary: Gate E public-readiness approval, merge, push-to-main, and public release.
```

## Human Demo Inspection

Before using this evidence for Gate E:

- Confirm the command outputs are metadata-only and do not include private
  transcript text, audio contents, cookies, tokens, meeting URLs, or auth state.
- Confirm the local alpha dry run records the narrow local pass without starting
  a server, opening a browser, reading private data, or delivering live alerts.
- Treat older Gate D bundle and handoff `product_judgment_evidence` blocker
  output as historical pre-pass helper context, not current project status.
- Confirm the scheduler/archive smoke uses only the explicit temporary work
  root and does not start timers, daemons, background loops, browser automation,
  audio capture, live notifications, deletion, export, or participation actions.
- Inspect whether the local demo evidence remains useful context for Gate E
  review without treating it as Gate E approval.

## Manual Judgment To Record After Inspection

The next manual judgment is Gate E approval, not another Gate D pass/fail/defer
decision. Gate D already has a narrow local pass recorded for the
fixture-to-reviewer demo only.

## Manual Judgment Boundary

Gate E still needs fresh human approval. Until that approval is personally
provided, do not merge, push-to-main, publicly expose the repository, publish a
release, or claim public readiness passed.
