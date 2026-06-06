$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

function Invoke-Step {
  param(
    [string]$Name,
    [scriptblock]$Action
  )

  Write-Host "==> $Name"
  try {
    & $Action
    Write-Host "OK: $Name"
  } catch {
    Write-Error "FAILED: $Name"
    throw
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

Push-Location $Root
try {
  Invoke-Step "content validation" {
    Invoke-Native "python" @("backend\scripts\validate_content.py")
  }

  Invoke-Step "backend pytest" {
    Push-Location "backend"
    try {
      Invoke-Native "python" @("-m", "pytest", "tests", "-q")
    } finally {
      Pop-Location
    }
  }

  Invoke-Step "web build" {
    Push-Location "apps\web"
    try {
      Invoke-Native "npm" @("run", "build")
    } finally {
      Pop-Location
    }
  }

  Invoke-Step "miniprogram JS syntax" {
    Get-ChildItem -Path "apps\miniprogram" -Recurse -Filter "*.js" | ForEach-Object {
      Invoke-Native "node" @("--check", $_.FullName)
    }
  }

  Invoke-Step "miniprogram JSON parse" {
    Get-ChildItem -Path "apps\miniprogram" -Recurse -Filter "*.json" | ForEach-Object {
      Get-Content -Raw -LiteralPath $_.FullName | ConvertFrom-Json | Out-Null
    }
  }
} finally {
  Pop-Location
}

Write-Host "All checks passed."
