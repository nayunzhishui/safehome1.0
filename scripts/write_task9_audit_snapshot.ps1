param(
  [string]$CloudBaseBaseUrl = "https://flask-gh3l-261352-9-1436233118.sh.run.tcloudbase.com",
  [int]$TimeoutSec = 60
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$DocsRoot = Join-Path $Root "docs"
$FactsDir = Get-ChildItem -LiteralPath $DocsRoot -Directory -Filter "00_*" | Select-Object -First 1
$AcceptanceDir = Get-ChildItem -LiteralPath $DocsRoot -Directory -Filter "02_*" | Select-Object -First 1
if (-not $FactsDir -or -not $AcceptanceDir) {
  throw "Required docs directories not found."
}

$PlanPath = Get-ChildItem -LiteralPath $FactsDir.FullName -Filter "Claude*.md" | Select-Object -First 1
$RecordPath = Get-ChildItem -LiteralPath $AcceptanceDir.FullName -Filter "*20260702.md" |
  Where-Object { Select-String -Path $_.FullName -Pattern "T9-31" -Quiet } |
  Select-Object -First 1
$PackagePath = Join-Path $Root ".codex_tmp\safehome-cloudbase-task9-latest.zip"

function Invoke-EndpointSnapshot {
  param([string]$Path)

  $result = [ordered]@{
    path = $Path
    ok = $false
    statusCode = $null
    error = $null
    bodyPreview = $null
  }
  try {
    $response = Invoke-WebRequest -Uri "$CloudBaseBaseUrl$Path" -UseBasicParsing -TimeoutSec $TimeoutSec
    $result.statusCode = [int]$response.StatusCode
    $result.ok = $response.StatusCode -eq 200
    $body = [string]$response.Content
    if ($body.Length -gt 300) {
      $body = $body.Substring(0, 300)
    }
    $result.bodyPreview = $body
  } catch {
    if ($_.Exception.Response) {
      try {
        $result.statusCode = [int]$_.Exception.Response.StatusCode
      } catch {
        $result.statusCode = $null
      }
    }
    $result.error = $_.Exception.Message
  }
  return $result
}

$packageInfo = $null
if (Test-Path -LiteralPath $PackagePath) {
  $pkg = Get-Item -LiteralPath $PackagePath
  $hash = Get-FileHash -LiteralPath $PackagePath -Algorithm SHA256
  $packageInfo = [ordered]@{
    path = ".codex_tmp/safehome-cloudbase-task9-latest.zip"
    sizeBytes = $pkg.Length
    sha256 = $hash.Hash
  }
}

$planTaskCount = 0
if ($PlanPath) {
  $planTaskCount = (Select-String -Path $PlanPath.FullName -Pattern '^## T9-[0-9]{2}').Count
}
$recordTaskCount = 0
if ($RecordPath) {
  for ($i = 1; $i -le 31; $i++) {
    $taskId = "T9-{0:D2}" -f $i
    if (Select-String -Path $RecordPath.FullName -Pattern $taskId -Quiet) {
      $recordTaskCount += 1
    }
  }
}

$endpoints = @(
  Invoke-EndpointSnapshot -Path "/healthz"
  Invoke-EndpointSnapshot -Path "/readyz"
  Invoke-EndpointSnapshot -Path "/healthz/deep"
)
$readyz = $endpoints | Where-Object { $_.path -eq "/readyz" } | Select-Object -First 1
$completionStatus = if ($readyz.ok) { "ready_for_manual_miniprogram_acceptance" } else { "blocked_cloudbase_readyz" }
$remainingRequiredActions = if ($readyz.ok) {
  @(
    "Complete WeChat DevTools miniprogram acceptance.",
    "Complete real-device miniprogram acceptance.",
    "Fill docs/02_专项进度与验收/任务九外部人工验收证据表_20260703.md and set allow_complete: yes only after all external checks pass.",
    "Run scripts/audit_task9_completion.ps1 again."
  )
} else {
  @(
    "Publish .codex_tmp/safehome-cloudbase-task9-latest.zip to CloudBase service flask-gh3l.",
    "Run scripts/run_task9_external_checks.ps1 -SkipSqliteBackupRestore.",
    "Run scripts/audit_task9_completion.ps1.",
    "Complete WeChat DevTools and real-device miniprogram acceptance."
  )
}

$snapshot = [ordered]@{
  generatedAt = (Get-Date).ToString("o")
  branch = (git branch --show-current 2>$null)
  completionStatus = $completionStatus
  planTaskCount = $planTaskCount
  recordTaskCount = $recordTaskCount
  package = $packageInfo
  cloudBase = [ordered]@{
    baseUrl = $CloudBaseBaseUrl
    endpoints = $endpoints
  }
  remainingRequiredActions = $remainingRequiredActions
}

$jsonPath = Join-Path $AcceptanceDir.FullName "task9_completion_audit_snapshot_20260703.json"
$mdPath = Join-Path $AcceptanceDir.FullName "task9_completion_audit_snapshot_20260703.md"
$snapshot | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

$endpointLines = $endpoints | ForEach-Object {
  "- $($_.path): status=$($_.statusCode), ok=$($_.ok), error=$($_.error)"
}
$markdown = @(
  "# Task 9 Completion Audit Snapshot",
  "",
  "Generated: $($snapshot.generatedAt)",
  "",
  "Status: $completionStatus",
  "",
  "Plan task count: $planTaskCount",
  "Record task count: $recordTaskCount",
  "",
  "Package: $($packageInfo.path)",
  "SHA256: $($packageInfo.sha256)",
  "",
  "CloudBase endpoints:",
  $endpointLines,
  "",
  "Remaining required actions:",
  ($remainingRequiredActions | ForEach-Object { "- $_" })
)
$markdown | Set-Content -LiteralPath $mdPath -Encoding UTF8

Write-Host "Task 9 audit snapshot written:"
Write-Host $jsonPath
Write-Host $mdPath
Write-Host "Status=$completionStatus"
