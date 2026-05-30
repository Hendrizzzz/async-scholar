param(
    [switch]$Help,
    [string]$WorkRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Show-GateDHumanWalkthroughHelp {
    @"
AsyncScholar Gate D human walkthrough

Usage:
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_gate_d_human_walkthrough.ps1 [-WorkRoot <path>]

Optional parameters:
  -WorkRoot <path>
      Local work root for temporary metadata artifacts. When omitted, the
      script uses a safe default temp work root:
      <TEMP>\async-scholar-gate-d-human-walkthrough

What this walkthrough does:
  - Checks the local AsyncScholar CLI can be reached.
  - Reads the local Gate D metadata bundle.
  - Reads the local Gate D handoff packet.
  - Runs the existing local scheduler/archive workflow smoke under the work root.
  - Prints a human-facing explanation of what each step proves.

Safety boundary:
  This walkthrough is local and metadata-only. It does not claim Gate D. It
  does not claim Product Promise Alpha. It keeps product_judgment_evidence
  blocking until a human gives a pass/fail/defer decision.
"@
}

function Write-WalkthroughError {
    param([string]$Message)

    [Console]::Error.WriteLine($Message)
}

function Resolve-WalkthroughWorkRoot {
    param([string]$InputWorkRoot)

    if ([string]::IsNullOrWhiteSpace($InputWorkRoot)) {
        $tempRoot = $env:TEMP
        if ([string]::IsNullOrWhiteSpace($tempRoot)) {
            $tempRoot = [System.IO.Path]::GetTempPath()
        }
        return [System.IO.Path]::GetFullPath(
            (Join-Path $tempRoot "async-scholar-gate-d-human-walkthrough")
        )
    }

    return [System.IO.Path]::GetFullPath($InputWorkRoot)
}

function Invoke-CapturedCommand {
    param(
        [string]$Label,
        [string]$Executable,
        [string[]]$Arguments
    )

    $commandOutput = & $Executable @Arguments 2>&1
    $exitCode = $LASTEXITCODE
    $outputText = [string]::Join(
        [Environment]::NewLine,
        @($commandOutput | ForEach-Object { $_.ToString() })
    )
    if ($exitCode -ne 0) {
        if ($outputText) {
            Write-WalkthroughError $outputText
        }
        Write-WalkthroughError ("Walkthrough command '{0}' failed with exit code {1}." -f $Label, $exitCode)
        exit $exitCode
    }

    return $outputText
}

function Invoke-AsyncScholarCli {
    param(
        [string]$CommandName,
        [string[]]$CommandArgs = @()
    )

    $uvArgs = @("run", "python", "-m", "async_scholar", $CommandName) + $CommandArgs
    return Invoke-CapturedCommand -Label ("async_scholar {0}" -f $CommandName) -Executable "uv" -Arguments $uvArgs
}

function Convert-JsonObject {
    param(
        [string]$JsonText,
        [string]$Label
    )

    try {
        return $JsonText | ConvertFrom-Json
    } catch {
        Write-WalkthroughError ("Expected JSON output for {0}, but it could not be parsed." -f $Label)
        exit 65
    }
}

function Test-GateDBundleBlocker {
    param([object]$Bundle)

    if (-not ($Bundle.blocking_evidence -contains "product_judgment_evidence")) {
        Write-WalkthroughError "Expected Gate D bundle blocker product_judgment_evidence was not present."
        exit 65
    }
    if ($Bundle.product_judgment_evidence_status -ne "blocking") {
        Write-WalkthroughError "Expected Gate D product_judgment_evidence_status to be blocking."
        exit 65
    }
    if ($Bundle.gate_d_pass_claimed -ne $false) {
        Write-WalkthroughError "Expected Gate D pass claim flag to remain false."
        exit 65
    }
    if ($Bundle.product_promise_alpha_pass_claimed -ne $false) {
        Write-WalkthroughError "Expected Product Promise Alpha pass claim flag to remain false."
        exit 65
    }
}

function Test-HandoffPacketRequiresHumanJudgment {
    param([object]$Handoff)

    if ($Handoff.manual_product_judgment_required -ne $true) {
        Write-WalkthroughError "Expected manual product judgment to be required."
        exit 65
    }
    if ($Handoff.manual_product_judgment_recorded -ne $false) {
        Write-WalkthroughError "Expected manual product judgment to remain unrecorded."
        exit 65
    }
    if ($Handoff.review_can_be_completed_by_ai -ne $false) {
        Write-WalkthroughError "Expected review_can_be_completed_by_ai to remain false."
        exit 65
    }
    if ($Handoff.product_judgment_evidence_status -ne "blocking") {
        Write-WalkthroughError "Expected handoff product_judgment_evidence_status to be blocking."
        exit 65
    }
}

if ($Help) {
    Show-GateDHumanWalkthroughHelp
    exit 0
}

$resolvedWorkRoot = Resolve-WalkthroughWorkRoot -InputWorkRoot $WorkRoot
$schedulerSmokeWorkRoot = Join-Path $resolvedWorkRoot "scheduler-archive-smoke"
$schedulerSmokeScript = Join-Path $PSScriptRoot "run_scheduler_archive_workflow_smoke.ps1"

New-Item -ItemType Directory -Path $resolvedWorkRoot -Force | Out-Null

Write-Output "AsyncScholar Gate D Product Promise Alpha walkthrough"
Write-Output "Walkthrough work root: $resolvedWorkRoot"
Write-Output "Scheduler/archive smoke work root: $schedulerSmokeWorkRoot"
Write-Output ""
Write-Output "This is an AI-solvable clarity walkthrough. It stops before the human pass/fail/defer judgment."
Write-Output ""

Write-Output "Step 1 - CLI availability"
Write-Output "What this proves: the local AsyncScholar CLI can be reached."
Write-Output "Expected signal: the CLI help command exits successfully."
Invoke-AsyncScholarCli "--help" | Out-Null
Write-Output "Result: CLI help completed."
Write-Output ""

Write-Output "Step 2 - Gate D evidence bundle"
Write-Output "What this proves: the local metadata bundle is readable and still blocks on unresolved human product judgment."
Write-Output "Expected signal: product_judgment_evidence is blocking."
$bundleJson = Invoke-AsyncScholarCli "gate-d-local-evidence-bundle"
$bundle = Convert-JsonObject -JsonText $bundleJson -Label "Gate D local evidence bundle"
Test-GateDBundleBlocker -Bundle $bundle
Write-Output "Result: Gate D remains blocked on product_judgment_evidence."
Write-Output ""

Write-Output "Step 3 - Human handoff packet"
Write-Output "What this proves: the handoff packet is ready for manual review but does not record the decision."
Write-Output "Expected signal: manual product judgment is required and not recorded."
$handoffJson = Invoke-AsyncScholarCli "gate-d-handoff-packet-local"
$handoff = Convert-JsonObject -JsonText $handoffJson -Label "Gate D handoff packet"
Test-HandoffPacketRequiresHumanJudgment -Handoff $handoff
Write-Output "Result: manual product judgment is required and not recorded."
Write-Output ""

Write-Output "Step 4 - Local scheduler/archive workflow smoke"
Write-Output "What this proves: the local scheduler/archive metadata walkthrough can run under an explicit temp root."
Write-Output "Expected signal: the smoke finishes and reports local metadata artifact paths."
Invoke-CapturedCommand `
    -Label "scheduler/archive workflow smoke" `
    -Executable "powershell" `
    -Arguments @(
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        $schedulerSmokeScript,
        "-WorkRoot",
        $schedulerSmokeWorkRoot
    ) | Out-Null
Write-Output "Result: scheduler/archive smoke completed under the walkthrough work root."
Write-Output "Temporary artifact root: $schedulerSmokeWorkRoot"
Write-Output ""

Write-Output "Walkthrough complete."
Write-Output "Next human step: inspect this readout and choose pass/fail/defer."
