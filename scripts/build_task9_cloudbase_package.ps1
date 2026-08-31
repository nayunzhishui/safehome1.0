param(
  [string]$OutputPath = "",
  [switch]$KeepStaging,
  [string]$PackageLabel = "SafeHome task 9 CloudBase package",
  [string]$ManifestFile = "TASK9_PACKAGE_MANIFEST.txt",
  [string]$LatestFile = "safehome-cloudbase-task9-latest.zip"
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$CodexTmp = Join-Path $Root ".codex_tmp"
$StagingRoot = Join-Path $CodexTmp "task9-cloudbase-package"
$SourceArchive = Join-Path $CodexTmp "task9-source-head.zip"
$FingerprintScript = Join-Path $Root "scripts/generate_build_fingerprint.py"
. (Join-Path $PSScriptRoot "cloudbase_package_source.ps1")

if ([string]::IsNullOrWhiteSpace($PackageLabel) -or $PackageLabel -match "[`r`n]") {
  throw "PackageLabel must be one non-empty line."
}
foreach ($leafName in @($ManifestFile, $LatestFile)) {
  if ([string]::IsNullOrWhiteSpace($leafName) -or [System.IO.Path]::GetFileName($leafName) -ne $leafName) {
    throw "ManifestFile and LatestFile must be leaf filenames."
  }
}

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
  $branch = (git branch --show-current 2>$null)
  $head = (git rev-parse HEAD 2>$null)
  $sourceTree = (git rev-parse "$head^{tree}" 2>$null)
  if ($head -notmatch "^[a-f0-9]{40}$" -or $sourceTree -notmatch "^[a-f0-9]{40}$") {
    throw "A valid Git HEAD and source tree are required for a release package."
  }
  $workingTreeDirty = [bool](git status --short 2>$null)
  if (Test-Path -LiteralPath $SourceArchive) {
    Remove-Item -LiteralPath $SourceArchive -Force
  }
  # git archive makes the package source exactly match the recorded commit.
  Invoke-Native "git" @(
    "archive",
    "--format=zip",
    "--output=$SourceArchive",
    $head,
    "Dockerfile",
    ".dockerignore",
    "backend",
    "content",
    "shared",
    "config/rc0810/database_profiles.json",
    "deploy/verify_rc0810_f03_images.py"
  )
  Expand-Archive -LiteralPath $SourceArchive -DestinationPath $StagingRoot -Force

  Remove-CloudBasePackageArtifacts -SourceRoot $StagingRoot
  Rename-CloudBaseProfileModels -SourceRoot $StagingRoot

  $buildTime = (Get-Date).ToUniversalTime().ToString("o")
  Assert-Exists $FingerprintScript
  Invoke-Native "python" @(
    $FingerprintScript,
    "--root", $StagingRoot,
    "--output", (Join-Path $StagingRoot "backend\build_info.json"),
    "--commit-sha", $head,
    "--build-time", $buildTime
  )
  $manifest = @(
    $PackageLabel,
    "GeneratedAt=$buildTime",
    "Branch=$branch",
    "Head=$head",
    "SourceMode=git_archive_head",
    "SourceTree=$sourceTree",
    "Included=Dockerfile,.dockerignore,backend,content,shared,config/rc0810/database_profiles.json,deploy/verify_rc0810_f03_images.py",
    "Excluded=env files, databases, logs, caches, virtualenvs, node build outputs, backups",
    "CloudBaseCompatibility=content/profiles JSON filenames are shortened in the package only; model_id inside each JSON is preserved.",
    "WorkingTreeDirty=$($workingTreeDirty.ToString().ToLowerInvariant())"
  )
  Set-Content -LiteralPath (Join-Path $StagingRoot $ManifestFile) -Value $manifest -Encoding UTF8

  if (Test-Path -LiteralPath $OutputPath) {
    Remove-Item -LiteralPath $OutputPath -Force
  }

  $compileTargets = @(
    (Join-Path $StagingRoot "backend\app.py"),
    (Join-Path $StagingRoot "backend\database.py"),
    (Join-Path $StagingRoot "backend\config.py")
  )
  $compileArguments = @(
    "-c",
    "from pathlib import Path; import sys; [compile(Path(p).read_text(encoding='utf-8'), p, 'exec') for p in sys.argv[1:]]"
  ) + $compileTargets
  Invoke-Native "python" $compileArguments

  New-ZipWithPortablePaths -SourceDir $StagingRoot -ZipPath $OutputPath

  $zipInfo = Get-Item -LiteralPath $OutputPath
  $latestPath = Join-Path $CodexTmp $LatestFile
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
  if (Test-Path -LiteralPath $SourceArchive) {
    Remove-Item -LiteralPath $SourceArchive -Force
  }
  if (-not $KeepStaging -and (Test-Path -LiteralPath $StagingRoot)) {
    Remove-Item -LiteralPath $StagingRoot -Recurse -Force
  }
}
