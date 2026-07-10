param(
  [string]$CliPath = $env:WECHAT_DEVTOOLS_CLI,
  [int]$AutoPort = 9420
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$ProjectPath = Join-Path $Root "apps\miniprogram"
$WebPath = Join-Path $Root "apps\web"

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
  & $CliPath auto --project $ProjectPath --auto-port $AutoPort
  if ($LASTEXITCODE -ne 0) {
    throw "WeChat DevTools automation failed to start. Exit code: $LASTEXITCODE"
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
