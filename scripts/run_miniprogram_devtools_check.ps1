param(
  [string]$CliPath = $env:WECHAT_DEVTOOLS_CLI,
  [int]$AutoPort = 9420,
  [Parameter(Mandatory = $true)]
  [string]$ProjectPath
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$WebPath = Join-Path $Root "apps\web"
$ProjectPath = (Resolve-Path -LiteralPath $ProjectPath).Path
$ProjectConfig = Get-Content -LiteralPath (Join-Path $ProjectPath "project.config.json") -Raw | ConvertFrom-Json
if ($ProjectConfig.appid -ne "touristappid") {
  throw "Use an isolated synthetic UI copy with touristappid; do not run this mocked check against a live account project."
}

if (-not $CliPath) {
  $Candidates = @(
    (Get-ChildItem "C:\Program Files (x86)\Tencent" -Recurse -Filter "cli.bat" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName),
    (Get-ChildItem "C:\Program Files\Tencent" -Recurse -Filter "cli.bat" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName)
  )
  $CliPath = $Candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}

if (-not $CliPath -or -not (Test-Path -LiteralPath $CliPath)) {
  Write-Error "WeChat DevTools CLI was not found. Install DevTools and set WECHAT_DEVTOOLS_CLI to the full cli.bat path."
  exit 2
}

$env:WECHAT_DEVTOOLS_AUTO_PORT = "$AutoPort"
try {
  $LaunchOutput = & $CliPath auto --project $ProjectPath --auto-port $AutoPort --trust-project 2>&1
  $LaunchOutput | ForEach-Object { Write-Host $_ }
  if ($LASTEXITCODE -ne 0 -or ($LaunchOutput -join "`n") -match '\[error\]|EEXIST') {
    throw "WeChat DevTools automation failed to start; inspect the CLI error above."
  }
  Push-Location $WebPath
  try {
    node tests\miniprogram\devtools-smoke.cjs
    if ($LASTEXITCODE -ne 0) {
      throw "Mini-program automation smoke check failed. Exit code: $LASTEXITCODE"
    }
  } finally {
    Pop-Location
  }
} finally {
  & $CliPath close --project $ProjectPath 2>$null
}
