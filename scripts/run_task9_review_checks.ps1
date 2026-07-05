param(
  [switch]$SkipHeavyChecks
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

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

$DocsRoot = Join-Path $Root "docs"
$FactsDir = Resolve-SinglePath $DocsRoot "00_*"
$AcceptanceDir = Resolve-SinglePath $DocsRoot "02_*"
$PlanPath = Resolve-SinglePath $FactsDir "Claude*.md"
$RecordPath = Resolve-SinglePath $AcceptanceDir "Claude*20260702.md"
$FieldCheckPath = Resolve-SingleMarkdownByContent $AcceptanceDir "*20260702.md" "<!-- task9_database_field_check -->"

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
  Invoke-Step "task 9 plan has exactly 31 subtasks" {
    Assert-Exists $PlanPath
    $matches = Select-String -Path $PlanPath -Pattern '^## T9-[0-9]{2}'
    if ($matches.Count -ne 31) {
      throw "Expected 31 T9 subtasks in plan, found $($matches.Count)."
    }
    if (Select-String -Path $PlanPath -Pattern '^## T9-32' -Quiet) {
      throw "Unexpected T9-32 found in task 9 plan."
    }
  }

  Invoke-Step "task 9 execution record covers 31 subtasks" {
    Assert-Exists $RecordPath
    for ($i = 1; $i -le 31; $i++) {
      $taskId = "T9-{0:D2}" -f $i
      if (-not (Select-String -Path $RecordPath -Pattern $taskId -Quiet)) {
        throw "Execution record does not mention $taskId."
      }
    }
  }

  Invoke-Step "task 9 database field checklist exists" {
    Assert-Exists $FieldCheckPath
    $fieldCount = (Select-String -Path $FieldCheckPath -Pattern '^\| [a-zA-Z_][a-zA-Z0-9_]* \|').Count
    if ($fieldCount -lt 50) {
      throw "Database field checklist looks incomplete: only $fieldCount fields found."
    }
  }

  Invoke-Step "core project entry files exist" {
    @(
      "backend\app.py",
      "backend\database.py",
      "backend\config.py",
      "backend\models.py",
      "apps\miniprogram\app.json",
      "apps\miniprogram\services\api.js",
      "apps\miniprogram\services\cloudConfig.js",
      "apps\web\package.json",
      "shared\constants\api.ts",
      "shared\types\api.ts",
      "content\training_cards.json",
      "content\feedback_rules.json",
      "scripts\build_task9_cloudbase_package.ps1",
      "scripts\verify_task9_cloudbase_package.ps1",
      "scripts\audit_task9_completion.ps1",
      "scripts\verify_task9_external_evidence.ps1"
    ) | ForEach-Object { Assert-Exists (Join-Path $Root $_) }
  }

  Invoke-Step "miniprogram integration-test page is preserved" {
    Assert-Exists (Join-Path $Root "apps\miniprogram\pages\integration-test\index.js")
    Assert-Exists (Join-Path $Root "apps\miniprogram\pages\integration-test\index.wxml")
    Assert-Exists (Join-Path $Root "apps\miniprogram\pages\integration-test\index.json")
  }

  Invoke-Step "miniprogram app.json pages have core files" {
    $appJsonPath = Join-Path $Root "apps\miniprogram\app.json"
    $appJson = Get-Content -Raw -LiteralPath $appJsonPath | ConvertFrom-Json
    foreach ($page in $appJson.pages) {
      foreach ($ext in @(".js", ".wxml", ".json")) {
        Assert-Exists (Join-Path $Root "apps\miniprogram\$page$ext")
      }
    }
  }

  Invoke-Step "miniprogram request transport stays in service layer" {
    $jsFiles = Get-ChildItem -Path (Join-Path $Root "apps\miniprogram") -Recurse -Filter "*.js" |
      Where-Object { $_.FullName -notlike "*services\api.js" }
    $matches = @($jsFiles | Select-String -Pattern "wx\.request\s*\(|\.callContainer\s*\(")
    if ($matches.Count -gt 0) {
      $sample = ($matches | Select-Object -First 5 | ForEach-Object { "$($_.Path):$($_.LineNumber)" }) -join ", "
      throw "Request transport found outside services/api.js: $sample"
    }
  }

  Invoke-Step "frontend code does not reference backend secret env names" {
    $frontendFiles = @()
    if (Test-Path (Join-Path $Root "apps\miniprogram")) {
      $frontendFiles += Get-ChildItem -Path (Join-Path $Root "apps\miniprogram") -Recurse -Include "*.js","*.json","*.wxml"
    }
    if (Test-Path (Join-Path $Root "apps\web\src")) {
      $frontendFiles += Get-ChildItem -Path (Join-Path $Root "apps\web\src") -Recurse -Include "*.ts","*.tsx","*.js","*.jsx"
    }
    $secretMatches = @($frontendFiles | Select-String -Pattern "MYSQL_PASSWORD|WECHAT_SECRET|SECRET_KEY|ADMIN_EXPORT_TOKEN")
    if ($secretMatches.Count -gt 0) {
      $sample = ($secretMatches | Select-Object -First 5 | ForEach-Object { "$($_.Path):$($_.LineNumber)" }) -join ", "
      throw "Frontend references backend secret env names: $sample"
    }
  }

  Invoke-Step "no tracked local runtime artifacts" {
    $tracked = @(git ls-files | Select-String -Pattern "node_modules|(^|/)dist/|\.sqlite3$|\.db$|(^|/)\.venv/|__pycache__")
    if ($tracked.Count -gt 0) {
      $sample = ($tracked | Select-Object -First 5 | ForEach-Object { $_.Line }) -join ", "
      throw "Tracked local runtime artifacts found: $sample"
    }

    $statusArtifacts = @(git status --short | Select-String -Pattern "node_modules|(^|/)dist/|\.sqlite3$|\.db$|(^|/)\.venv/|__pycache__|safehome-deploy")
    if ($statusArtifacts.Count -gt 0) {
      Write-Warning "Working tree has local artifacts or package files to review before commit:"
      $statusArtifacts | ForEach-Object { Write-Warning $_.Line }
    }
  }

  Invoke-Step "task 9 key files syntax smoke check" {
    Invoke-Native "node" @("--check", "apps\miniprogram\services\api.js")
    Invoke-Native "node" @("--check", "apps\miniprogram\services\cloudConfig.js")
    Invoke-Native "python" @("-c", "from pathlib import Path; [compile(Path(p).read_text(encoding='utf-8'), p, 'exec') for p in ['backend/app.py','backend/database.py','backend/config.py']]")
    [void][scriptblock]::Create((Get-Content -Raw -LiteralPath (Join-Path $Root "scripts\build_task9_cloudbase_package.ps1")))
    [void][scriptblock]::Create((Get-Content -Raw -LiteralPath (Join-Path $Root "scripts\verify_task9_cloudbase_package.ps1")))
    [void][scriptblock]::Create((Get-Content -Raw -LiteralPath (Join-Path $Root "scripts\audit_task9_completion.ps1")))
    [void][scriptblock]::Create((Get-Content -Raw -LiteralPath (Join-Path $Root "scripts\verify_task9_external_evidence.ps1")))
  }

  Invoke-Step "task 9 CloudBase package validates if present" {
    $packages = @(Get-ChildItem -LiteralPath (Join-Path $Root ".codex_tmp") -Filter "safehome-cloudbase-task9-*.zip" -ErrorAction SilentlyContinue)
    if ($packages.Count -eq 0) {
      Write-Host "No task 9 CloudBase package found; skipping package validation."
    } else {
      Invoke-Native "powershell" @("-ExecutionPolicy", "Bypass", "-File", "scripts\verify_task9_cloudbase_package.ps1")
    }
  }

  if ($SkipHeavyChecks) {
    Write-Host "Heavy checks skipped."
  } else {
    Invoke-Step "content validation" {
      Invoke-Native "python" @("backend\scripts\validate_content.py")
    }

    Invoke-Step "backend tests" {
      Invoke-Native "python" @("-m", "pytest", "backend\tests", "-q")
    }

    Invoke-Step "web build" {
      Push-Location "apps\web"
      try {
        Invoke-Native "npm" @("run", "build")
      } finally {
        Pop-Location
      }
    }
  }
} finally {
  Pop-Location
}

Write-Host "Task 9 review checks completed."
