param(
  [string]$OutputPath = "",
  [switch]$KeepStaging
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$CodexTmp = Join-Path $Root ".codex_tmp"
$StagingRoot = Join-Path $CodexTmp "task9-cloudbase-package"

if (-not $OutputPath) {
  $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $OutputPath = Join-Path $CodexTmp "safehome-cloudbase-task9-$stamp.zip"
}

$OutputPath = [System.IO.Path]::GetFullPath($OutputPath)
$OutputDir = Split-Path -Parent $OutputPath

function Assert-Exists {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    throw "Missing required path: $Path"
  }
}

function Copy-RequiredPath {
  param(
    [string]$RelativePath
  )

  $source = Join-Path $Root $RelativePath
  $target = Join-Path $StagingRoot $RelativePath
  Assert-Exists $source
  $targetParent = Split-Path -Parent $target
  if (-not (Test-Path -LiteralPath $targetParent)) {
    New-Item -ItemType Directory -Path $targetParent | Out-Null
  }
  Copy-Item -LiteralPath $source -Destination $target -Recurse -Force
}

function Remove-PackageArtifacts {
  $artifactPatterns = @(
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "*.pyc",
    "*.pyo",
    "*.sqlite3",
    "*.sqlite",
    "*.db",
    "*.log",
    ".env",
    ".env.*",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
    "backups",
    "exports"
  )

  foreach ($pattern in $artifactPatterns) {
    Get-ChildItem -LiteralPath $StagingRoot -Recurse -Force -ErrorAction SilentlyContinue |
      Where-Object { $_.Name -like $pattern } |
      Remove-Item -Recurse -Force
  }
}

function Rename-ProfileModelsForCloudBase {
  $profileDir = Join-Path $StagingRoot "content\profiles"
  if (-not (Test-Path -LiteralPath $profileDir)) {
    return
  }

  $index = 1
  Get-ChildItem -LiteralPath $profileDir -Filter "*.json" -File |
    Sort-Object Name |
    ForEach-Object {
      $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.Substring(0, 12).ToLowerInvariant()
      $targetName = "profile_{0:D3}_{1}.json" -f $index, $hash
      $targetPath = Join-Path $profileDir $targetName
      if ($_.FullName -ne $targetPath) {
        Move-Item -LiteralPath $_.FullName -Destination $targetPath -Force
      }
      $index += 1
    }
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

function New-ZipWithPortablePaths {
  param(
    [string]$SourceDir,
    [string]$ZipPath
  )

  Add-Type -AssemblyName System.IO.Compression
  Add-Type -AssemblyName System.IO.Compression.FileSystem

  $archive = [System.IO.Compression.ZipFile]::Open($ZipPath, [System.IO.Compression.ZipArchiveMode]::Create)
  try {
    $sourceFullPath = [System.IO.Path]::GetFullPath($SourceDir).TrimEnd("\", "/") + [System.IO.Path]::DirectorySeparatorChar
    $files = Get-ChildItem -LiteralPath $SourceDir -Recurse -File -Force
    foreach ($file in $files) {
      $relativePath = $file.FullName.Substring($sourceFullPath.Length)
      $zipPath = $relativePath.Replace("\", "/")
      [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
        $archive,
        $file.FullName,
        $zipPath,
        [System.IO.Compression.CompressionLevel]::Optimal
      ) | Out-Null
    }
  } finally {
    $archive.Dispose()
  }
}

New-Item -ItemType Directory -Path $CodexTmp -Force | Out-Null
if (Test-Path -LiteralPath $StagingRoot) {
  Remove-Item -LiteralPath $StagingRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $StagingRoot | Out-Null
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

Push-Location $Root
try {
  @(
    "Dockerfile",
    ".dockerignore",
    "backend",
    "content",
    "shared"
  ) | ForEach-Object { Copy-RequiredPath $_ }

  Remove-PackageArtifacts
  Rename-ProfileModelsForCloudBase

  $branch = (git branch --show-current 2>$null)
  $head = (git rev-parse HEAD 2>$null)
  $status = (git status --short 2>$null)
  $buildTime = (Get-Date).ToUniversalTime().ToString("o")
  Invoke-Native "python" @(
    "scripts\generate_build_fingerprint.py",
    "--root", $StagingRoot,
    "--output", (Join-Path $StagingRoot "backend\build_info.json"),
    "--commit-sha", $head,
    "--build-time", $buildTime
  )
  $manifest = @(
    "SafeHome task 9 CloudBase package",
    "GeneratedAt=$buildTime",
    "Branch=$branch",
    "Head=$head",
    "Included=Dockerfile,.dockerignore,backend,content,shared",
    "Excluded=env files, databases, logs, caches, virtualenvs, node build outputs, backups",
    "CloudBaseCompatibility=content/profiles JSON filenames are shortened in the package only; model_id inside each JSON is preserved.",
    "",
    "WorkingTreeStatus:",
    $status
  )
  Set-Content -LiteralPath (Join-Path $StagingRoot "TASK9_PACKAGE_MANIFEST.txt") -Value $manifest -Encoding UTF8

  if (Test-Path -LiteralPath $OutputPath) {
    Remove-Item -LiteralPath $OutputPath -Force
  }

  New-ZipWithPortablePaths -SourceDir $StagingRoot -ZipPath $OutputPath

  Invoke-Native "python" @("-c", "from pathlib import Path; [compile(Path(p).read_text(encoding='utf-8'), p, 'exec') for p in ['backend/app.py','backend/database.py','backend/config.py']]")

  $zipInfo = Get-Item -LiteralPath $OutputPath
  $latestPath = Join-Path $CodexTmp "safehome-cloudbase-task9-latest.zip"
  Copy-Item -LiteralPath $OutputPath -Destination $latestPath -Force

  $hash = Get-FileHash -LiteralPath $OutputPath -Algorithm SHA256
  $latestHash = Get-FileHash -LiteralPath $latestPath -Algorithm SHA256
  $hashLine = "$($hash.Hash)  $([System.IO.Path]::GetFileName($OutputPath))"
  $latestHashLine = "$($latestHash.Hash)  $([System.IO.Path]::GetFileName($latestPath))"
  Set-Content -LiteralPath "$OutputPath.sha256" -Value $hashLine -Encoding ASCII
  Set-Content -LiteralPath "$latestPath.sha256" -Value $latestHashLine -Encoding ASCII

  Write-Host "CloudBase package created:"
  Write-Host $zipInfo.FullName
  Write-Host "SizeBytes=$($zipInfo.Length)"
  Write-Host "SHA256=$($hash.Hash)"
  Write-Host "LatestPackage=$latestPath"
} finally {
  Pop-Location
  if (-not $KeepStaging -and (Test-Path -LiteralPath $StagingRoot)) {
    Remove-Item -LiteralPath $StagingRoot -Recurse -Force
  }
}
