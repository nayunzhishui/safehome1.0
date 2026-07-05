param(
  [string]$PackagePath = ""
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$CodexTmp = Join-Path $Root ".codex_tmp"

if (-not $PackagePath) {
  $stableLatest = Join-Path $CodexTmp "safehome-cloudbase-task9-latest.zip"
  if (Test-Path -LiteralPath $stableLatest) {
    $latestPackage = Get-Item -LiteralPath $stableLatest
  } else {
    $latestPackage = Get-ChildItem -LiteralPath $CodexTmp -Filter "safehome-cloudbase-task9-*.zip" -ErrorAction SilentlyContinue |
      Sort-Object LastWriteTime -Descending |
      Select-Object -First 1
  }
  if (-not $latestPackage) {
    throw "No task 9 CloudBase package found under $CodexTmp."
  }
  $PackagePath = $latestPackage.FullName
}

$PackagePath = [System.IO.Path]::GetFullPath($PackagePath)
if (-not (Test-Path -LiteralPath $PackagePath)) {
  throw "Package not found: $PackagePath"
}

$package = Get-Item -LiteralPath $PackagePath
if ($package.Length -lt 100000) {
  throw "Package is unexpectedly small: $($package.Length) bytes"
}

$hash = Get-FileHash -LiteralPath $PackagePath -Algorithm SHA256
$sidecarPath = "$PackagePath.sha256"
if (Test-Path -LiteralPath $sidecarPath) {
  $sidecar = (Get-Content -LiteralPath $sidecarPath -TotalCount 1).Trim()
  $expectedHash = ($sidecar -split "\s+")[0]
  if ($expectedHash -and $expectedHash -ne $hash.Hash) {
    throw "Package SHA256 sidecar mismatch. expected=$expectedHash actual=$($hash.Hash)"
  }
}

Add-Type -AssemblyName System.IO.Compression.FileSystem

$archive = [System.IO.Compression.ZipFile]::OpenRead($PackagePath)
try {
  $entries = @($archive.Entries | ForEach-Object { $_.FullName })

  $requiredEntries = @(
    "Dockerfile",
    ".dockerignore",
    "backend/app.py",
    "backend/database.py",
    "backend/config.py",
    "backend/requirements.txt",
    "content/training_cards.json",
    "content/feedback_rules.json",
    "content/risk_keywords.json",
    "shared/constants/api.ts",
    "shared/types/api.ts",
    "TASK9_PACKAGE_MANIFEST.txt"
  )

  foreach ($entry in $requiredEntries) {
    if ($entries -notcontains $entry) {
      throw "Package missing required entry: $entry"
    }
  }

  $badSeparators = @($entries | Where-Object { $_ -match "\\" })
  if ($badSeparators.Count -gt 0) {
    throw "Package contains Windows path separators: $($badSeparators[0])"
  }

  foreach ($entry in $entries) {
    foreach ($segment in ($entry -split "/")) {
      if ([System.Text.Encoding]::UTF8.GetByteCount($segment) -gt 240) {
        throw "Package contains a path segment too long for CloudBase unzip: $entry"
      }
    }
  }

  $longProfileNames = @(
    $entries |
      Where-Object { $_ -match '^content/profiles/.+\.json$' -and $_ -notmatch '^content/profiles/profile_[0-9]{3}_[a-f0-9]{12}\.json$' }
  )
  if ($longProfileNames.Count -gt 0) {
    throw "Package contains non-portable profile model filename: $($longProfileNames[0])"
  }

  $forbiddenPatterns = @(
    '(^|/)\.env($|\.)',
    '(^|/)node_modules/',
    '(^|/)dist/',
    '(^|/)build/',
    '(^|/)__pycache__/',
    '(^|/)\.pytest_cache/',
    '(^|/)\.mypy_cache/',
    '(^|/)\.venv/',
    '(^|/)venv/',
    '(^|/)backups/',
    '(^|/)exports/',
    '\.sqlite3$',
    '\.sqlite$',
    '\.db$',
    '\.log$',
    '\.pyc$',
    '\.pyo$'
  )

  foreach ($pattern in $forbiddenPatterns) {
    $match = @($entries | Where-Object { $_ -match $pattern } | Select-Object -First 1)
    if ($match.Count -gt 0) {
      throw "Package contains forbidden artifact matching ${pattern}: $($match[0])"
    }
  }

  $manifest = $archive.GetEntry("TASK9_PACKAGE_MANIFEST.txt")
  if (-not $manifest) {
    throw "Package missing TASK9_PACKAGE_MANIFEST.txt"
  }
  $stream = $manifest.Open()
  try {
    $reader = New-Object System.IO.StreamReader($stream)
    $manifestText = $reader.ReadToEnd()
  } finally {
    $stream.Dispose()
  }
  if ($manifestText -notmatch "SafeHome task 9 CloudBase package") {
    throw "Manifest does not identify the task 9 CloudBase package."
  }
  if ($manifestText -notmatch "Included=Dockerfile,.dockerignore,backend,content,shared") {
    throw "Manifest does not list the expected included paths."
  }
} finally {
  $archive.Dispose()
}

Write-Host "Task 9 CloudBase package verified:"
Write-Host $PackagePath
Write-Host "SizeBytes=$($package.Length)"
Write-Host "SHA256=$($hash.Hash)"
