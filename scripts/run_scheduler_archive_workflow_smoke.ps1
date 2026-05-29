param(
    [switch]$Help,
    [string]$WorkRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Show-SchedulerArchiveWorkflowSmokeHelp {
    @"
AsyncScholar local scheduler/archive workflow smoke runner

Required parameters:
  -WorkRoot <path>
      Explicit work root for all generated local metadata smoke artifacts.
      The script fails before creating directories or running AsyncScholar if
      this value is missing or blank.

Generated local metadata artifacts:
  scheduler\schedule.sqlite
  archive\ticket-193-smoke-session\runtime.jsonl
  recovery-reports\ticket-193-smoke-session\stored-session-window-recovery-report.md

Workflow scope:
  Uses existing AsyncScholar CLI commands only. The smoke saves and lists a
  local schedule, previews a due session window, records one-shot start and
  stop metadata, summarizes runtime metadata, renders and writes a recovery
  report, and prints local Gate D bundle and handoff progress.

Safety boundary:
  This runner creates only local metadata artifacts under the explicit work root.
  It does not claim Gate D readiness. It does not claim Product Promise Alpha
  readiness. The handoff remains blocked until a human provides the deferred
  product judgment.

Manual smoke shape:
  powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_scheduler_archive_workflow_smoke.ps1 -WorkRoot <explicit-local-work-root>
"@
}

function Invoke-AsyncScholarSmokeCommand {
    param(
        [string]$CommandName,
        [string[]]$CommandArgs
    )

    Write-Output ("Running: async_scholar {0}" -f $CommandName)
    $uvArgs = @(
        "run",
        "python",
        "-m",
        "async_scholar",
        $CommandName
    ) + $CommandArgs

    $commandOutput = & uv @uvArgs 2>&1
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        if ($commandOutput) {
            $commandOutput | ForEach-Object { [Console]::Error.WriteLine($_) }
        }
        $failureMessage = "Command async_scholar {0} failed with exit code {1}." -f $CommandName, $exitCode
        [Console]::Error.WriteLine($failureMessage)
        exit $exitCode
    }

    Write-Output ("Completed: async_scholar {0}" -f $CommandName)
}

if ($Help) {
    Show-SchedulerArchiveWorkflowSmokeHelp
    exit 0
}

if ([string]::IsNullOrWhiteSpace($WorkRoot)) {
    [Console]::Error.WriteLine("Missing required -WorkRoot.")
    [Console]::Error.WriteLine("Run with -Help for required parameters and scope.")
    exit 64
}

$resolvedWorkRoot = [System.IO.Path]::GetFullPath($WorkRoot)
$scheduleRoot = Join-Path $resolvedWorkRoot "scheduler"
$scheduleDbPath = Join-Path $scheduleRoot "schedule.sqlite"
$archiveRoot = Join-Path $resolvedWorkRoot "archive"
$recoveryReportsRoot = Join-Path $resolvedWorkRoot "recovery-reports"
$baseSessionId = "ticket-193-smoke-session"
$sessionId = $baseSessionId
$sessionOrdinal = 2
while (
    (Test-Path -LiteralPath (Join-Path (Join-Path $archiveRoot $sessionId) "runtime.jsonl")) -or
    (Test-Path -LiteralPath (Join-Path (Join-Path $recoveryReportsRoot $sessionId) "stored-session-window-recovery-report.md"))
) {
    $sessionId = "{0}-{1}" -f $baseSessionId, $sessionOrdinal
    $sessionOrdinal += 1
}
$courseId = "ticket-193-smoke-course"
$sourceKind = "file"
$clockDayOfWeek = "friday"
$clockLocalTime = "09:00"
$classTime = "friday,09:00,45,Asia/Manila,workflow smoke"
$sessionArchiveRoot = Join-Path $archiveRoot $sessionId
$recoveryReportRoot = Join-Path $recoveryReportsRoot $sessionId
$recoveryReportPath = Join-Path $recoveryReportRoot "stored-session-window-recovery-report.md"

New-Item -ItemType Directory -Path $scheduleRoot -Force | Out-Null
New-Item -ItemType Directory -Path $sessionArchiveRoot -Force | Out-Null
New-Item -ItemType Directory -Path $recoveryReportRoot -Force | Out-Null

Write-Output "Running scheduler/archive workflow smoke with explicit local work root."
Write-Output ("Work root: {0}" -f $resolvedWorkRoot)

Invoke-AsyncScholarSmokeCommand "course-schedule-save-local" @(
    "--db-path",
    $scheduleDbPath,
    "--course-id",
    $courseId,
    "--title",
    "Ticket 193 Smoke Course",
    "--meeting-label",
    "metadata-only local smoke",
    "--class-time",
    $classTime
)

Invoke-AsyncScholarSmokeCommand "course-schedule-list-local" @(
    "--db-path",
    $scheduleDbPath
)

Invoke-AsyncScholarSmokeCommand "scheduled-start-due-list-from-store-local" @(
    "--db-path",
    $scheduleDbPath,
    "--source-kind",
    $sourceKind,
    "--clock-day-of-week",
    $clockDayOfWeek,
    "--clock-local-time",
    $clockLocalTime,
    $sessionId
)

Invoke-AsyncScholarSmokeCommand "session-window-readiness-preflight-from-store-local" @(
    "--db-path",
    $scheduleDbPath,
    "--archive-root",
    $archiveRoot,
    "--source-kind",
    $sourceKind,
    "--clock-day-of-week",
    $clockDayOfWeek,
    "--clock-local-time",
    $clockLocalTime,
    $sessionId
)

Invoke-AsyncScholarSmokeCommand "session-window-confirmation-preflight-from-store-local" @(
    "--db-path",
    $scheduleDbPath,
    "--archive-root",
    $archiveRoot,
    "--source-kind",
    $sourceKind,
    "--clock-day-of-week",
    $clockDayOfWeek,
    "--clock-local-time",
    $clockLocalTime,
    $sessionId
)

Invoke-AsyncScholarSmokeCommand "session-window-start-authorization-from-store-local" @(
    "--db-path",
    $scheduleDbPath,
    "--archive-root",
    $archiveRoot,
    "--source-kind",
    $sourceKind,
    "--clock-day-of-week",
    $clockDayOfWeek,
    "--clock-local-time",
    $clockLocalTime,
    "--confirmation-response",
    "confirmed",
    $sessionId
)

Invoke-AsyncScholarSmokeCommand "session-window-execution-preflight-from-store-local" @(
    "--db-path",
    $scheduleDbPath,
    "--archive-root",
    $archiveRoot,
    "--source-kind",
    $sourceKind,
    "--clock-day-of-week",
    $clockDayOfWeek,
    "--clock-local-time",
    $clockLocalTime,
    "--confirmation-response",
    "confirmed",
    $sessionId
)

Invoke-AsyncScholarSmokeCommand "session-window-execute-from-store-local" @(
    "--db-path",
    $scheduleDbPath,
    "--archive-root",
    $archiveRoot,
    "--source-kind",
    $sourceKind,
    "--clock-day-of-week",
    $clockDayOfWeek,
    "--clock-local-time",
    $clockLocalTime,
    "--confirmation-response",
    "confirmed",
    $sessionId
)

Invoke-AsyncScholarSmokeCommand "session-window-stop-execution-preflight-from-store-local" @(
    "--db-path",
    $scheduleDbPath,
    "--archive-root",
    $archiveRoot,
    "--course-id",
    $courseId,
    "--class-time-index",
    "0",
    "--source-kind",
    $sourceKind,
    $sessionId
)

Invoke-AsyncScholarSmokeCommand "session-window-stop-execute-from-store-local" @(
    "--db-path",
    $scheduleDbPath,
    "--archive-root",
    $archiveRoot,
    "--course-id",
    $courseId,
    "--class-time-index",
    "0",
    "--source-kind",
    $sourceKind,
    "--confirmation-response",
    "confirmed",
    $sessionId
)

Invoke-AsyncScholarSmokeCommand "session-window-runtime-summary-local" @(
    "--archive-root",
    $archiveRoot,
    $sessionId
)

Invoke-AsyncScholarSmokeCommand "session-window-recovery-report-local" @(
    "--archive-root",
    $archiveRoot,
    $sessionId
)

Invoke-AsyncScholarSmokeCommand "session-window-recovery-report-write-local" @(
    "--archive-root",
    $archiveRoot,
    "--output-root",
    $recoveryReportRoot,
    $sessionId
)

Invoke-AsyncScholarSmokeCommand "gate-d-local-evidence-bundle" @()
Invoke-AsyncScholarSmokeCommand "gate-d-handoff-packet-local" @()

Write-Output "Scheduler/archive workflow smoke completed."
Write-Output ("Schedule DB: {0}" -f $scheduleDbPath)
Write-Output ("Runtime metadata: {0}" -f (Join-Path $sessionArchiveRoot "runtime.jsonl"))
Write-Output ("Recovery report: {0}" -f $recoveryReportPath)
Write-Output "Gate D handoff remains blocked on product_judgment_evidence; human judgment is required."
exit 0
