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
    throw "FAILED: $Name`n$($_.Exception.Message)"
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

  Invoke-Step "web typecheck" {
    Push-Location "apps\web"
    try {
      Invoke-Native "npm" @("run", "typecheck")
    } finally {
      Pop-Location
    }
  }

  Invoke-Step "miniprogram structure audit" {
    Invoke-Native "python" @("backend\scripts\audit_miniprogram_frontend.py")
  }

  Invoke-Step "miniprogram JS and JSON assets" {
    Invoke-Native "python" @("backend\scripts\validate_miniprogram_assets.py")
  }
} finally {
  Pop-Location
}

Write-Host "All checks passed."
