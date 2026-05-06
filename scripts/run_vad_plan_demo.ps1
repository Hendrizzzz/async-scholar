param(
    [switch]$Help,
    [string]$AudioPath,
    [string]$OutputRoot,
    [Nullable[double]]$OldestPendingAgeSeconds,
    [double]$ObservedAtSeconds = 0.0
)

function Show-Help {
    @"
Run the AsyncScholar file VAD planning demo.

Required:
  -AudioPath <path>    Existing local audio file to analyze.
  -OutputRoot <path>   Directory that receives vad-plan-report.json.

Optional:
  -OldestPendingAgeSeconds <seconds>   Include backlog diagnostic metadata.
  -ObservedAtSeconds <seconds>         Stable observation timestamp for metadata.
  -Help                                Show this help.

Output:
  vad-plan-report.json under the explicit output root. The report contains
  timing and count metadata only.
"@
}

if ($Help) {
    Show-Help
    exit 0
}

if ([string]::IsNullOrWhiteSpace($AudioPath)) {
    [Console]::Error.WriteLine("Missing required -AudioPath.")
    Show-Help
    exit 64
}

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    [Console]::Error.WriteLine("Missing required -OutputRoot.")
    Show-Help
    exit 64
}

if (-not (Test-Path -LiteralPath $AudioPath -PathType Leaf)) {
    [Console]::Error.WriteLine("AudioPath does not exist or is not a file.")
    exit 66
}

$ModuleArgs = @(
    "run",
    "python",
    "-m",
    "async_scholar.audio.vad_plan_demo",
    "--audio-path",
    $AudioPath,
    "--output-root",
    $OutputRoot
)

if ($null -ne $OldestPendingAgeSeconds) {
    $ModuleArgs += @("--oldest-pending-age-seconds", $OldestPendingAgeSeconds.ToString([Globalization.CultureInfo]::InvariantCulture))
    $ModuleArgs += @("--observed-at-seconds", $ObservedAtSeconds.ToString([Globalization.CultureInfo]::InvariantCulture))
}

& uv @ModuleArgs
exit $LASTEXITCODE
