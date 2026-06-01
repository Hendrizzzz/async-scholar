param(
    [switch]$Help,
    [switch]$DryRun,
    [string]$HostName = "127.0.0.1",
    [string]$Port = "8086"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptError = "local alpha dashboard demo script could not be built"
$AllowedHosts = @("127.0.0.1", "localhost", "::1")

function Write-FixedErrorAndExit {
    [Console]::Error.WriteLine($ScriptError)
    exit 1
}

function Show-LocalAlphaDashboardDemoHelp {
    @"
AsyncScholar local alpha dashboard demo

Usage:
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_local_alpha_dashboard_demo.ps1 [-DryRun] [-HostName 127.0.0.1] [-Port 8086]

Options:
  -Help       Show this help text without invoking uv or starting the server.
  -DryRun     Print the loopback URL and safety summary without starting the server.
  -HostName   Loopback host only: 127.0.0.1, localhost, or ::1. Default: 127.0.0.1.
  -Port       Local TCP port from 1 through 65535. Default: 8086.

This is a local metadata-only alpha demo wrapper around:
  uv run python -m async_scholar local-alpha-dashboard-demo

Gate D / Product Promise Alpha has a human-recorded narrow local pass for the
fixture-to-reviewer demo only. This script does not broaden that narrow pass,
does not approve Gate E, public release, push, or merge, and does not open a
browser, access external meetings, access private data, capture media, deliver
live alerts, run schedulers, delete or export files, participate autonomously,
or answer academic questions.
"@
}

if ($Help) {
    Show-LocalAlphaDashboardDemoHelp
    exit 0
}

if ($args.Count -gt 0) {
    Write-FixedErrorAndExit
}

if ($AllowedHosts -notcontains $HostName) {
    Write-FixedErrorAndExit
}

$ParsedPort = 0
if (-not [int]::TryParse($Port, [ref]$ParsedPort)) {
    Write-FixedErrorAndExit
}
if ($ParsedPort -lt 1 -or $ParsedPort -gt 65535) {
    Write-FixedErrorAndExit
}

$PortText = $ParsedPort.ToString([System.Globalization.CultureInfo]::InvariantCulture)
$CliArgs = @(
    "run",
    "python",
    "-m",
    "async_scholar",
    "local-alpha-dashboard-demo",
    "--host",
    $HostName,
    "--port",
    $PortText
)

if ($DryRun) {
    $CliArgs += "--dry-run"
}

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
exit 0
