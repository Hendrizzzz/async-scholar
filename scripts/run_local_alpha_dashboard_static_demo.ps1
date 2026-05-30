Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptError = "local alpha dashboard static demo script could not be built"

function Write-FixedErrorAndExit {
    [Console]::Error.WriteLine($ScriptError)
    exit 1
}

function Show-LocalAlphaDashboardStaticDemoHelp {
    @"
AsyncScholar local alpha dashboard static demo

Usage:
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_local_alpha_dashboard_static_demo.ps1 [-Output <path>]

Options:
  -Help     Show this help text without invoking uv.
  -Output   Optional explicit local HTML output path. Defaults to a new file under TEMP.

This is a one-command wrapper around:
  uv run python -m async_scholar local-alpha-dashboard-static-demo --output <path>

Gate D remains blocked on product_judgment_evidence. This script does not pass Gate D
or Product Promise Alpha, start a server, open a browser, access external meetings,
access private data, capture media, deliver live alerts, run schedulers, delete or
export files, participate autonomously, or answer academic questions.
"@
}

function New-DefaultOutputPath {
    $TempRoot = [System.IO.Path]::GetTempPath()
    $Suffix = [guid]::NewGuid().ToString("N")
    Join-Path -Path $TempRoot -ChildPath "async-scholar-local-alpha-dashboard-$Suffix.html"
}

function Test-SafeOutputPath {
    param([string]$PathText)

    if ([string]::IsNullOrWhiteSpace($PathText)) {
        return $false
    }
    if ($PathText -match "://") {
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

$RawArgs = @($args)
$OutputPath = ""
$UsedDefaultOutput = $false

if ($RawArgs.Count -eq 1 -and $RawArgs[0] -eq "-Help") {
    Show-LocalAlphaDashboardStaticDemoHelp
    exit 0
}

if ($RawArgs.Count -eq 0) {
    $OutputPath = New-DefaultOutputPath
    $UsedDefaultOutput = $true
}
elseif ($RawArgs.Count -eq 2 -and $RawArgs[0] -eq "-Output") {
    $OutputPath = $RawArgs[1]
}
else {
    Write-FixedErrorAndExit
}

if ([string]::IsNullOrWhiteSpace($OutputPath) -or $OutputPath.StartsWith("-")) {
    Write-FixedErrorAndExit
}

if (-not (Test-SafeOutputPath -PathText $OutputPath)) {
    Write-FixedErrorAndExit
}

$CliArgs = @(
    "run",
    "python",
    "-m",
    "async_scholar",
    "local-alpha-dashboard-static-demo",
    "--output",
    $OutputPath
)

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

if ($null -ne $CommandOutput) {
    foreach ($Line in $CommandOutput) {
        [Console]::Out.WriteLine($Line.ToString())
    }
}
if ($UsedDefaultOutput) {
    [Console]::Out.WriteLine("Default output: $OutputPath")
}
exit 0
