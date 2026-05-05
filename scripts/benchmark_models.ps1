param(
    [switch]$Help,
    [string]$AudioPath,
    [string]$ModelSizeOrPath,
    [string]$OutputRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($Help) {
    @"
Usage:
  powershell -ExecutionPolicy Bypass -File scripts\benchmark_models.ps1 `
    -AudioPath <path> `
    -ModelSizeOrPath <model-size-or-path> `
    -OutputRoot <path>

Runs:
  uv run python -m async_scholar.stt.benchmark `
    --audio-path <path> `
    --model-size-or-path <model-size-or-path> `
    --output-root <path>

All three benchmark inputs are required. This helper does not select a default
model or sample audio file.
"@
    exit 0
}

$missing = @()
if ([string]::IsNullOrWhiteSpace($AudioPath)) {
    $missing += "-AudioPath"
}
if ([string]::IsNullOrWhiteSpace($ModelSizeOrPath)) {
    $missing += "-ModelSizeOrPath"
}
if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $missing += "-OutputRoot"
}

if ($missing.Count -gt 0) {
    Write-Error "Missing required parameter(s): $($missing -join ', ')"
    exit 2
}

$arguments = @(
    "run",
    "python",
    "-m",
    "async_scholar.stt.benchmark",
    "--audio-path",
    $AudioPath,
    "--model-size-or-path",
    $ModelSizeOrPath,
    "--output-root",
    $OutputRoot
)

& uv @arguments
exit $LASTEXITCODE
