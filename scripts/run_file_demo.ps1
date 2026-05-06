param(
    [switch]$Help,
    [string]$AudioPath,
    [string]$ModelSizeOrPath,
    [string]$OutputRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Show-FileDemoHelp {
    @"
AsyncScholar 1-minute file STT smoke runner

Required parameters:
  -AudioPath <path>
      Path to a local user-supplied audio file. No sample audio is bundled or selected.

  -ModelSizeOrPath <name-or-path>
      Explicit faster-whisper model size/name or local model path. No default model is chosen.

  -OutputRoot <path>
      Directory for generated smoke artifacts.

Expected generated artifacts:
  transcript.jsonl
  transcript.md
  benchmark-report.json

Generated smoke artifacts should stay ignored local outputs, for example under:
  data\sessions\file-stt-demo

Privacy and safety:
  This runner does not print transcript text, full private transcript contents, auth state,
  secrets, or generated media contents. Inspect generated artifacts locally after the run.

Manual smoke shape:
  powershell -ExecutionPolicy Bypass -File scripts\run_file_demo.ps1 -AudioPath <local-one-minute-audio> -ModelSizeOrPath <explicit-model-or-local-model-path> -OutputRoot data\sessions\file-stt-demo
"@
}

if ($Help) {
    Show-FileDemoHelp
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
    [Console]::Error.WriteLine("Missing required parameter(s): {0}" -f ($missing -join ", "))
    [Console]::Error.WriteLine("Run with -Help for required parameters and manual smoke guidance.")
    exit 64
}

if (-not (Test-Path -LiteralPath $AudioPath -PathType Leaf)) {
    [Console]::Error.WriteLine("AudioPath does not exist or is not a file. Provide a local audio file explicitly.")
    exit 66
}

Write-Output "Running AsyncScholar file STT smoke via the existing benchmark module."
Write-Output "Generated artifacts, if successful, are written under the explicit output root."

$benchmarkArgs = @(
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

& uv @benchmarkArgs
$benchmarkExitCode = $LASTEXITCODE

if ($benchmarkExitCode -ne 0) {
    [Console]::Error.WriteLine("File STT smoke runner failed; benchmark module exit code {0}." -f $benchmarkExitCode)
    exit $benchmarkExitCode
}

Write-Output "File STT smoke runner completed. Inspect ignored artifacts in the output root."
Write-Output "Expected artifacts: transcript.jsonl, transcript.md, benchmark-report.json."
