function Remove-CloudBasePackageArtifacts {
  param([Parameter(Mandatory = $true)][string]$SourceRoot)

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
    Get-ChildItem -LiteralPath $SourceRoot -Recurse -Force -ErrorAction SilentlyContinue |
      Where-Object { $_.Name -like $pattern } |
      Remove-Item -Recurse -Force
  }
}

function Rename-CloudBaseProfileModels {
  param([Parameter(Mandatory = $true)][string]$SourceRoot)

  $profileDir = Join-Path $SourceRoot "content\profiles"
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
