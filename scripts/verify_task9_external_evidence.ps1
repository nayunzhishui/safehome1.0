$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$DocsRoot = Join-Path $Root "docs"
$AcceptanceDir = Get-ChildItem -LiteralPath $DocsRoot -Directory -Filter "02_*" | Select-Object -First 1
if (-not $AcceptanceDir) {
  throw "Acceptance docs directory not found."
}

$evidenceFiles = @(
  Get-ChildItem -LiteralPath $AcceptanceDir.FullName -Filter "*.md" |
    Where-Object { Select-String -Path $_.FullName -Pattern "^<!-- task9_external_acceptance_evidence -->$" -Quiet }
)
if ($evidenceFiles.Count -ne 1) {
  throw "Expected one task 9 external evidence file, found $($evidenceFiles.Count)."
}

$path = $evidenceFiles[0].FullName
$content = Get-Content -LiteralPath $path
$raw = $content -join "`n"

$unchecked = @($content | Where-Object { $_ -match '^\| \[ \] \|' })
$checked = @($content | Where-Object { $_ -match '^\| \[[xX]\] \|' })

if ($unchecked.Count -gt 0) {
  throw "Task 9 external evidence is incomplete: $($unchecked.Count) unchecked rows remain in $path."
}

if ($checked.Count -lt 1) {
  throw "Task 9 external evidence has no checked rows in $path."
}

if ($raw -notmatch '(?m)^allow_complete:\s*yes\s*$') {
  throw "Task 9 external evidence does not allow completion. Set 'allow_complete: yes' only after all external checks pass."
}

Write-Host "Task 9 external evidence verified:"
Write-Host $path
Write-Host "CheckedRows=$($checked.Count)"
