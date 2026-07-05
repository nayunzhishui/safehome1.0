param(
  [switch]$RunHeavyLocalChecks,
  [switch]$SkipCloudBase
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$DocsRoot = Join-Path $Root "docs"
$FactsDir = Get-ChildItem -LiteralPath $DocsRoot -Directory -Filter "00_*" | Select-Object -First 1
$AcceptanceDir = Get-ChildItem -LiteralPath $DocsRoot -Directory -Filter "02_*" | Select-Object -First 1

if (-not $FactsDir -or -not $AcceptanceDir) {
  throw "Required docs directories not found."
}

function Resolve-SinglePath {
  param(
    [string]$Base,
    [string]$Filter
  )

  $matches = @(Get-ChildItem -LiteralPath $Base -Filter $Filter)
  if ($matches.Count -ne 1) {
    throw "Expected one path under $Base matching $Filter, found $($matches.Count)."
  }
  return $matches[0].FullName
}

function Resolve-SingleMarkdownByContent {
  param(
    [string]$Base,
    [string]$Filter,
    [string]$Pattern
  )

  $matches = @(
    Get-ChildItem -LiteralPath $Base -Filter $Filter |
      Where-Object { Select-String -Path $_.FullName -Pattern $Pattern -Quiet }
  )
  if ($matches.Count -ne 1) {
    throw "Expected one markdown file under $Base matching $Filter and content $Pattern, found $($matches.Count)."
  }
  return $matches[0].FullName
}

$PlanPath = Resolve-SinglePath $FactsDir.FullName "Claude*.md"
$RecordPath = Resolve-SingleMarkdownByContent $AcceptanceDir.FullName "*20260702.md" "T9-31"
$FieldCheckPath = Resolve-SingleMarkdownByContent $AcceptanceDir.FullName "*20260702.md" "<!-- task9_database_field_check -->"
$ReleaseChecklistPath = Resolve-SingleMarkdownByContent $AcceptanceDir.FullName "*20260702.md" "-HealthTimeoutSec 90"
$ExternalEvidencePath = Resolve-SingleMarkdownByContent $AcceptanceDir.FullName "*.md" "^<!-- task9_external_acceptance_evidence -->$"

function Invoke-Step {
  param(
    [string]$Name,
    [scriptblock]$Action
  )
  Write-Host "==> $Name"
  & $Action
  Write-Host "OK: $Name"
}

function Invoke-Native {
  param(
    [string]$FilePath,
    [string[]]$Arguments
  )
  & $FilePath @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "$FilePath $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
  }
}

function Assert-Exists {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    throw "Missing required path: $Path"
  }
}

Push-Location $Root
try {
  Invoke-Step "strict task 9 artifacts exist" {
    @(
      $PlanPath,
      $RecordPath,
      $FieldCheckPath,
      $ReleaseChecklistPath,
      $ExternalEvidencePath,
      "scripts\run_task9_review_checks.ps1",
      "scripts\run_task9_external_checks.ps1",
      "scripts\build_task9_cloudbase_package.ps1",
      "scripts\verify_task9_cloudbase_package.ps1",
      "scripts\write_task9_audit_snapshot.ps1",
      "scripts\verify_task9_external_evidence.ps1"
    ) | ForEach-Object { Assert-Exists $_ }
  }

  Invoke-Step "strict task 9 plan and record coverage" {
    $planTaskCount = (Select-String -Path $PlanPath -Pattern '^## T9-[0-9]{2}').Count
    if ($planTaskCount -ne 31) {
      throw "Expected 31 task 9 subtasks, found $planTaskCount."
    }
    for ($i = 1; $i -le 31; $i++) {
      $taskId = "T9-{0:D2}" -f $i
      if (-not (Select-String -Path $RecordPath -Pattern $taskId -Quiet)) {
        throw "Task 9 execution record does not cover $taskId."
      }
    }
  }

  Invoke-Step "strict local task 9 review checks" {
    if ($RunHeavyLocalChecks) {
      Invoke-Native "powershell" @("-ExecutionPolicy", "Bypass", "-File", "scripts\run_task9_review_checks.ps1")
    } else {
      Invoke-Native "powershell" @("-ExecutionPolicy", "Bypass", "-File", "scripts\run_task9_review_checks.ps1", "-SkipHeavyChecks")
    }
  }

  Invoke-Step "strict CloudBase package verification" {
    Invoke-Native "powershell" @("-ExecutionPolicy", "Bypass", "-File", "scripts\verify_task9_cloudbase_package.ps1")
  }

  if ($SkipCloudBase) {
    Write-Host "CloudBase strict completion check skipped by caller."
    throw "Task 9 completion remains unproven because CloudBase verification was skipped."
  }

  Invoke-Step "strict external CloudBase readiness" {
    Invoke-Native "powershell" @("-ExecutionPolicy", "Bypass", "-File", "scripts\run_task9_external_checks.ps1", "-SkipSqliteBackupRestore")
  }

  Invoke-Step "strict external manual evidence" {
    Invoke-Native "powershell" @("-ExecutionPolicy", "Bypass", "-File", "scripts\verify_task9_external_evidence.ps1")
  }

  Write-Host "Task 9 strict completion audit passed."
} finally {
  Pop-Location
}
