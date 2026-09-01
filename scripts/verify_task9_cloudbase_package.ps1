param(
  [string]$PackagePath = "",
  [string]$PackageLabel = "SafeHome task 9 CloudBase package",
  [string]$ManifestFile = "TASK9_PACKAGE_MANIFEST.txt",
  [string]$LatestFile = "safehome-cloudbase-task9-latest.zip"
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$CodexTmp = Join-Path $Root ".codex_tmp"
. (Join-Path $PSScriptRoot "cloudbase_package_source.ps1")

function Get-ArchiveEntrySha256 {
  param([Parameter(Mandatory = $true)]$Entry)

  $stream = $Entry.Open()
  try {
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    try {
      return ([BitConverter]::ToString($sha256.ComputeHash($stream))).Replace("-", "")
    } finally {
      $sha256.Dispose()
    }
  } finally {
    $stream.Dispose()
  }
}

function Assert-PackageSourceMatchesCommit {
  param(
    [Parameter(Mandatory = $true)]$Archive,
    [Parameter(Mandatory = $true)][string]$Commit,
    [Parameter(Mandatory = $true)][string]$ManifestEntry
  )

  $referenceId = [Guid]::NewGuid().ToString("N")
  $referenceRoot = Join-Path $CodexTmp "task9-source-reference-$referenceId"
  $referenceArchive = Join-Path $CodexTmp "task9-source-reference-$referenceId.zip"
  try {
    & git -C $Root archive --format=zip "--output=$referenceArchive" $Commit Dockerfile .dockerignore backend content shared config/rc0810/database_profiles.json deploy/verify_rc0810_f03_images.py
    if ($LASTEXITCODE -ne 0) {
      throw "Unable to regenerate the recorded Git source archive."
    }
    Expand-Archive -LiteralPath $referenceArchive -DestinationPath $referenceRoot -Force
    Remove-CloudBasePackageArtifacts -SourceRoot $referenceRoot
    Rename-CloudBaseProfileModels -SourceRoot $referenceRoot

    $referencePrefix = [System.IO.Path]::GetFullPath($referenceRoot).TrimEnd("\", "/") + [System.IO.Path]::DirectorySeparatorChar
    $expected = @{}
    Get-ChildItem -LiteralPath $referenceRoot -Recurse -File -Force | ForEach-Object {
      $relative = $_.FullName.Substring($referencePrefix.Length).Replace("\", "/")
      $expected[$relative] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
    }

    $actual = @{}
    $Archive.Entries |
      Where-Object {
        $_.FullName -and
        -not $_.FullName.EndsWith("/") -and
        $_.FullName -ne $ManifestEntry -and
        $_.FullName -ne "backend/build_info.json"
      } |
      ForEach-Object {
        $actual[$_.FullName] = Get-ArchiveEntrySha256 -Entry $_
      }

    $expectedNames = @($expected.Keys | Sort-Object)
    $actualNames = @($actual.Keys | Sort-Object)
    if (
      (Compare-Object -ReferenceObject $expectedNames -DifferenceObject $actualNames) -or
      @($expectedNames | Where-Object { $expected[$_] -ne $actual[$_] }).Count -gt 0
    ) {
      throw "Source package content does not match the recorded Git commit."
    }
  } finally {
    if (Test-Path -LiteralPath $referenceArchive) {
      Remove-Item -LiteralPath $referenceArchive -Force
    }
    if (Test-Path -LiteralPath $referenceRoot) {
      Remove-Item -LiteralPath $referenceRoot -Recurse -Force
    }
  }
}

if ([string]::IsNullOrWhiteSpace($PackageLabel) -or $PackageLabel -match "[`r`n]") {
  throw "PackageLabel must be one non-empty line."
}
foreach ($leafName in @($ManifestFile, $LatestFile)) {
  if ([string]::IsNullOrWhiteSpace($leafName) -or [System.IO.Path]::GetFileName($leafName) -ne $leafName) {
    throw "ManifestFile and LatestFile must be leaf filenames."
  }
}

if (-not $PackagePath) {
  $stableLatest = Join-Path $CodexTmp $LatestFile
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
    "backend/build_info.json",
    "backend/requirements.txt",
    "content/training_cards.json",
    "content/feedback_rules.json",
    "content/risk_keywords.json",
    "shared/constants/api.ts",
    "shared/types/api.ts",
    "config/rc0810/database_profiles.json",
    "deploy/verify_rc0810_f03_images.py",
    $ManifestFile
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

  $manifest = $archive.GetEntry($ManifestFile)
  if (-not $manifest) {
    throw "Package missing $ManifestFile"
  }
  $stream = $manifest.Open()
  try {
    $reader = New-Object System.IO.StreamReader($stream)
    $manifestText = $reader.ReadToEnd()
  } finally {
    $stream.Dispose()
  }
  if ($manifestText -notmatch [regex]::Escape($PackageLabel)) {
    throw "Manifest does not identify the expected CloudBase package."
  }
  if ($manifestText -notmatch "Included=Dockerfile,.dockerignore,backend,content,shared,config/rc0810/database_profiles.json,deploy/verify_rc0810_f03_images.py") {
    throw "Manifest does not list the expected included paths."
  }
  if ($manifestText -notmatch "SourceMode=git_archive_head") {
    throw "Manifest source mode is not bound to Git HEAD."
  }
  $manifestHead = [regex]::Match($manifestText, "(?m)^Head=([a-f0-9]{40})\r?$").Groups[1].Value
  $manifestTree = [regex]::Match($manifestText, "(?m)^SourceTree=([a-f0-9]{40})\r?$").Groups[1].Value
  if (-not $manifestHead -or -not $manifestTree) {
    throw "Manifest is missing the source commit or source tree."
  }
  $resolvedTree = (& git -C $Root rev-parse "$manifestHead^{tree}" 2>$null)
  if ($LASTEXITCODE -ne 0 -or $resolvedTree -ne $manifestTree) {
    throw "Manifest source tree does not match the recorded Git commit."
  }
  Assert-PackageSourceMatchesCommit -Archive $archive -Commit $manifestHead -ManifestEntry $ManifestFile

  $buildInfoEntry = $archive.GetEntry("backend/build_info.json")
  if (-not $buildInfoEntry) {
    throw "Package missing backend/build_info.json"
  }
  $buildInfoStream = $buildInfoEntry.Open()
  try {
    $buildInfoReader = New-Object System.IO.StreamReader($buildInfoStream)
    $buildInfoText = $buildInfoReader.ReadToEnd()
  } finally {
    $buildInfoStream.Dispose()
  }
  $buildInfo = $buildInfoText | ConvertFrom-Json
  if ($buildInfo.schema -ne "safehome.build-fingerprint.v1") {
    throw "Build info schema is invalid."
  }
  if ($buildInfo.commit_sha -notmatch '^[a-f0-9]{40}$') {
    throw "Build info commit SHA is invalid."
  }
  if ($buildInfo.commit_sha -ne $manifestHead) {
    throw "Build info commit SHA does not match the archived source commit."
  }
  if ($buildInfo.api_contract_hash -notmatch '^[a-f0-9]{64}$') {
    throw "Build info API contract hash is invalid."
  }
  if ($buildInfo.content_manifest_hash -notmatch '^[a-f0-9]{64}$') {
    throw "Build info content manifest hash is invalid."
  }
  if ($buildInfoText -match '(?i)(appsecret|secret_key|authorization|password|auth_token)') {
    throw "Build info contains a forbidden secret-like key."
  }
  if ($buildInfoText -match '(?i)([A-Z]:\\|/Users/|/home/)') {
    throw "Build info contains an absolute local path."
  }
} finally {
  $archive.Dispose()
}

Write-Host "Task 9 CloudBase package verified:"
Write-Host $PackagePath
Write-Host "SizeBytes=$($package.Length)"
Write-Host "SHA256=$($hash.Hash)"
