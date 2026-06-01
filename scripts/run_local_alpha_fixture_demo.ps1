Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptError = "local alpha fixture demo script could not be built"
$FixturePath = "tests\fixtures\transcripts\attendance_roll_call.jsonl"

function Write-FixedErrorAndExit {
    [Console]::Error.WriteLine($ScriptError)
    exit 1
}

function Show-LocalAlphaFixtureDemoHelp {
    @"
AsyncScholar local alpha fixture demo

Usage:
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_local_alpha_fixture_demo.ps1 [-OutputRoot <path>] [-DashboardOutput <path>] [-SummaryOutput <path>]

Options:
  -Help             Show this help text without invoking uv.
  -OutputRoot       Optional local fixture artifact output root. Defaults to a new folder under TEMP.
  -DashboardOutput  Optional local static dashboard HTML path. Defaults to a new file under TEMP.
  -SummaryOutput    Optional sanitized local JSON summary path. No summary is written by default.

This is a one-command wrapper around:
  uv run python -m async_scholar fixture-demo tests\fixtures\transcripts\attendance_roll_call.jsonl --output-root <local-output-root>
  uv run python -m async_scholar local-alpha-dashboard-static-demo --output <local-html-output>
  uv run python -m async_scholar gate-d-local-evidence-bundle
  uv run python -m async_scholar gate-d-handoff-packet-local

Gate D / Product Promise Alpha has a human-recorded narrow local pass for the
fixture-to-reviewer demo only. This script does not broaden that narrow pass,
does not approve Gate E, public release, push, or merge, and does not start a
server, open a browser, access external meetings, access private data, capture
media, deliver live alerts, run schedulers, delete or export files,
participate autonomously, record product judgment, or answer academic questions.
"@
}

function New-DefaultOutputRoot {
    param([string]$Suffix)

    $TempRoot = [System.IO.Path]::GetTempPath()
    Join-Path -Path $TempRoot -ChildPath "async-scholar-local-alpha-fixture-demo-$Suffix"
}

function New-DefaultDashboardOutput {
    param([string]$Suffix)

    $TempRoot = [System.IO.Path]::GetTempPath()
    Join-Path -Path $TempRoot -ChildPath "async-scholar-local-alpha-fixture-demo-dashboard-$Suffix.html"
}

function Test-SafeLocalPathText {
    param([string]$PathText)

    if ([string]::IsNullOrWhiteSpace($PathText)) {
        return $false
    }
    if ($PathText.StartsWith("-")) {
        return $false
    }
    if ($PathText -match "://") {
        return $false
    }
    if (($PathText -match '^[A-Za-z][A-Za-z0-9+.-]*:') -and ($PathText -notmatch '^[A-Za-z]:[\\/]')) {
        return $false
    }
    if ($PathText.StartsWith("\\") -or $PathText.StartsWith("//")) {
        return $false
    }
    $PathSegments = $PathText -split '[\\/]'
    if ($PathSegments -contains "..") {
        return $false
    }
    foreach ($Character in $PathText.ToCharArray()) {
        if ([int][char]$Character -lt 32) {
            return $false
        }
    }

    return $true
}

function Test-SafeOutputRoot {
    param([string]$PathText)

    if (-not (Test-SafeLocalPathText -PathText $PathText)) {
        return $false
    }

    try {
        $Parent = Split-Path -Path $PathText -Parent
        if ([string]::IsNullOrWhiteSpace($Parent)) {
            $Parent = "."
        }
        if (-not (Test-Path -LiteralPath $Parent -PathType Container)) {
            return $false
        }
        if (Test-Path -LiteralPath $PathText -PathType Leaf) {
            return $false
        }
    }
    catch {
        return $false
    }

    return $true
}

function Test-SafeDashboardOutput {
    param([string]$PathText)

    if (-not (Test-SafeLocalPathText -PathText $PathText)) {
        return $false
    }

    try {
        $Parent = Split-Path -Path $PathText -Parent
        if ([string]::IsNullOrWhiteSpace($Parent)) {
            $Parent = "."
        }
        if (-not (Test-Path -LiteralPath $Parent -PathType Container)) {
            return $false
        }
        if (Test-Path -LiteralPath $PathText) {
            return $false
        }
    }
    catch {
        return $false
    }

    return $true
}

function Test-SafeSummaryOutput {
    param([string]$PathText)

    if (-not (Test-SafeLocalPathText -PathText $PathText)) {
        return $false
    }

    try {
        $Parent = Split-Path -Path $PathText -Parent
        if ([string]::IsNullOrWhiteSpace($Parent)) {
            $Parent = "."
        }
        if (-not (Test-Path -LiteralPath $Parent -PathType Container)) {
            return $false
        }
        if (Test-Path -LiteralPath $PathText) {
            return $false
        }
    }
    catch {
        return $false
    }

    return $true
}

function Invoke-AsyncScholarCommand {
    param([string[]]$CliArgs)

    try {
        $CommandOutput = & uv @CliArgs 2>&1
        $CommandExitCode = $LASTEXITCODE
    }
    catch {
        Write-FixedErrorAndExit
    }

    if ($CommandExitCode -ne 0) {
        Write-FixedErrorAndExit
    }
}

function Write-SanitizedSummaryOutput {
    param([string]$PathText)

    $SummaryJson = '{"browser_server_launched":"no","fixture_artifacts_generated":"yes","gate_d_evidence_bundle_status":"historical_pre_pass_blocked","gate_d_handoff_packet_status":"historical_manual_review_aid","live_delivery_performed":"no","private_paths_included":"no","product_judgment_evidence_status":"human_recorded_narrow_pass","product_judgment_recorded":"yes","product_promise_alpha_status":"human_recorded_narrow_pass","product_review_cue_available":"yes","raw_command_output_included":"no","static_dashboard_generated":"yes","summary_kind":"local_alpha_fixture_demo_sanitized_summary"}'
    $FileStream = $null
    $Writer = $null

    try {
        $FileStream = [System.IO.File]::Open(
            $PathText,
            [System.IO.FileMode]::CreateNew,
            [System.IO.FileAccess]::Write,
            [System.IO.FileShare]::None
        )
        $Writer = [System.IO.StreamWriter]::new(
            $FileStream,
            [System.Text.UTF8Encoding]::new($false)
        )
        $FileStream = $null
        $Writer.Write($SummaryJson)
    }
    catch {
        Write-FixedErrorAndExit
    }
    finally {
        if ($null -ne $Writer) {
            $Writer.Dispose()
        }
        if ($null -ne $FileStream) {
            $FileStream.Dispose()
        }
    }
}

$RawArgs = @($args)
$Suffix = [guid]::NewGuid().ToString("N")
$OutputRoot = New-DefaultOutputRoot -Suffix $Suffix
$DashboardOutput = New-DefaultDashboardOutput -Suffix $Suffix
$SummaryOutput = $null
$SeenOutputRoot = $false
$SeenDashboardOutput = $false
$SeenSummaryOutput = $false

if ($RawArgs.Count -eq 1 -and $RawArgs[0] -eq "-Help") {
    Show-LocalAlphaFixtureDemoHelp
    exit 0
}

$Index = 0
while ($Index -lt $RawArgs.Count) {
    switch ($RawArgs[$Index]) {
        "-OutputRoot" {
            if ($SeenOutputRoot -or ($Index + 1) -ge $RawArgs.Count) {
                Write-FixedErrorAndExit
            }
            $OutputRoot = $RawArgs[$Index + 1]
            $SeenOutputRoot = $true
            $Index += 2
            continue
        }
        "-DashboardOutput" {
            if ($SeenDashboardOutput -or ($Index + 1) -ge $RawArgs.Count) {
                Write-FixedErrorAndExit
            }
            $DashboardOutput = $RawArgs[$Index + 1]
            $SeenDashboardOutput = $true
            $Index += 2
            continue
        }
        "-SummaryOutput" {
            if ($SeenSummaryOutput -or ($Index + 1) -ge $RawArgs.Count) {
                Write-FixedErrorAndExit
            }
            $SummaryOutput = $RawArgs[$Index + 1]
            $SeenSummaryOutput = $true
            $Index += 2
            continue
        }
        default {
            Write-FixedErrorAndExit
        }
    }
}

if (-not (Test-SafeOutputRoot -PathText $OutputRoot)) {
    Write-FixedErrorAndExit
}
if (-not (Test-SafeDashboardOutput -PathText $DashboardOutput)) {
    Write-FixedErrorAndExit
}
if ($null -ne $SummaryOutput -and -not (Test-SafeSummaryOutput -PathText $SummaryOutput)) {
    Write-FixedErrorAndExit
}

Invoke-AsyncScholarCommand -CliArgs @(
    "run",
    "python",
    "-m",
    "async_scholar",
    "fixture-demo",
    $FixturePath,
    "--output-root",
    $OutputRoot
)
Invoke-AsyncScholarCommand -CliArgs @(
    "run",
    "python",
    "-m",
    "async_scholar",
    "local-alpha-dashboard-static-demo",
    "--output",
    $DashboardOutput
)
Invoke-AsyncScholarCommand -CliArgs @(
    "run",
    "python",
    "-m",
    "async_scholar",
    "gate-d-local-evidence-bundle"
)
Invoke-AsyncScholarCommand -CliArgs @(
    "run",
    "python",
    "-m",
    "async_scholar",
    "gate-d-handoff-packet-local"
)

if ($null -ne $SummaryOutput) {
    Write-SanitizedSummaryOutput -PathText $SummaryOutput
}

[Console]::Out.WriteLine("fixture demo artifacts generated")
[Console]::Out.WriteLine("static dashboard generated")
[Console]::Out.WriteLine("Historical Gate D evidence bundle reviewed")
[Console]::Out.WriteLine("Historical Gate D handoff packet reviewed")
[Console]::Out.WriteLine("narrow local Gate D pass remains recorded")
[Console]::Out.WriteLine("product review cue available for manual inspection")
exit 0
