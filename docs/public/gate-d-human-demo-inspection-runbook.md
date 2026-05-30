# Gate D Human Demo Inspection Runbook

Gate D / Product Promise Alpha remains blocked on `product_judgment_evidence`
until the user personally gives a fresh pass/fail/defer judgment.

This runbook is a local human demo inspection aid. Do not treat this runbook as product judgment evidence, a Gate D pass, or a Product Promise Alpha pass.

## Scope

Use this runbook only to prepare and inspect local metadata evidence before the
human-only product judgment. AI-solvable preparation stops here: after the local
checks and human inspection notes are ready, the next step is the user's own
fresh pass/fail/defer judgment.

This runbook does not require or approve real Google Meet, external meeting
platforms, auth/profile/cookies, private meeting data, browser automation,
loopback/system audio, live delivery, real deletion, push, public release,
secrets, tokens, private transcripts, private recordings, VAD/STT/model
execution, microphone use, participation actions, or academic-answer behavior.

## Automated Evidence

What the automated commands can show:

- The CLI is available.
- The local Gate D metadata bundle is still blocked only on
  `product_judgment_evidence`.
- The local handoff packet is ready for manual review but does not record the
  product judgment.
- The local scheduler/archive smoke can run in a temporary work root while
  staying metadata-only and local.

What only the user can decide:

- Whether the demo experience is good enough for Product Promise Alpha.
- Whether the product promise is met, unmet, or still deferred.
- Whether the final judgment should be recorded as pass, fail, or defer.

Run the local metadata checks:

```powershell
uv run python -m async_scholar --help
uv run python -m async_scholar gate-d-local-evidence-bundle
uv run python -m async_scholar gate-d-handoff-packet-local
```

Run the local scheduler/archive workflow smoke in a temporary work root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_scheduler_archive_workflow_smoke.ps1 -WorkRoot "$env:TEMP\async-scholar-gate-d-human-demo-runbook-smoke"
```

The smoke command may create local temp metadata artifacts under the selected
`-WorkRoot`. Do not commit those artifacts.

## One-Command Human Walkthrough

If the individual CLI commands still feel too internal, run the one-command
human walkthrough. It wraps the same local metadata checks, explains what each
step proves, validates that `product_judgment_evidence` is still blocking, and
then stops before the human product judgment.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_gate_d_human_walkthrough.ps1
```

To keep all temporary metadata artifacts under a chosen local root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_gate_d_human_walkthrough.ps1 -WorkRoot "$env:TEMP\async-scholar-gate-d-human-walkthrough"
```

Sample expected walkthrough readout:

```text
AsyncScholar Gate D Product Promise Alpha walkthrough
Step 1 - CLI availability
What this proves: the local AsyncScholar CLI can be reached.
Expected signal: product_judgment_evidence is blocking.
Result: Gate D remains blocked on product_judgment_evidence.
Result: manual product judgment is required and not recorded.
Step 4 - Local scheduler/archive workflow smoke
Temporary artifact root: <local temp path>\scheduler-archive-smoke
Next human step: inspect this readout and choose pass/fail/defer.
```

## Human Demo Inspection

Before judging the product:

- Confirm the command outputs are metadata-only and do not include private
  transcript text, audio contents, cookies, tokens, meeting URLs, or auth state.
- Confirm the Gate D bundle reports `product_judgment_evidence` as blocking.
- Confirm the handoff packet says manual product judgment is required and not
  recorded.
- Confirm the scheduler/archive smoke uses only the explicit temporary work
  root and does not start timers, daemons, background loops, browser automation,
  audio capture, live notifications, deletion, export, or participation actions.
- Inspect whether the local demo evidence is enough for you to make a product
  judgment.

## Manual Judgment To Record After Inspection

After the human demo inspection, choose exactly one judgment:

- pass
- fail
- defer

Record the judgment only after personal inspection is complete. Until then, keep
Gate D / Product Promise Alpha blocked on `product_judgment_evidence`.
