param(
  [string]$CloudBaseBaseUrl = "https://flask-gh3l-261352-9-1436233118.sh.run.tcloudbase.com",
  [int]$HealthTimeoutSec = 60,
  [int]$HealthRetryCount = 3,
  [int]$HealthRetryDelaySec = 5,
  [switch]$SkipCloudBase,
  [switch]$SkipSqliteBackupRestore
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

function Invoke-Step {
  param(
    [string]$Name,
    [scriptblock]$Action
  )

  Write-Host "==> $Name"
  & $Action
  Write-Host "OK: $Name"
}

function Test-CommandExists {
  param([string]$Name)
  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Test-EnvSet {
  param([string]$Name)
  return [bool][Environment]::GetEnvironmentVariable($Name)
}

function Invoke-HealthRequest {
  param(
    [string]$BaseUrl,
    [string]$Path,
    [int]$TimeoutSec,
    [int]$RetryCount,
    [int]$RetryDelaySec
  )

  $uri = "$BaseUrl$Path"
  $attempts = [Math]::Max(1, $RetryCount)
  $lastResult = $null
  for ($attempt = 1; $attempt -le $attempts; $attempt++) {
    $result = @{
      Path = $Path
      Ok = $false
      StatusCode = $null
      Error = ""
    }
    try {
      $response = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec $TimeoutSec
      $result.StatusCode = [int]$response.StatusCode
      $body = $response.Content
      if ($body.Length -gt 500) {
        $body = $body.Substring(0, 500)
      }
      Write-Host "$Path attempt=$attempt status=$($response.StatusCode) body=$body"
      if ($Path -eq "/readyz" -and $response.StatusCode -ne 200) {
        $result.Error = "/readyz did not return 200."
        $lastResult = $result
        if ($attempt -lt $attempts) {
          Start-Sleep -Seconds $RetryDelaySec
          continue
        }
        return $result
      }
      if ($Path -eq "/healthz" -and $response.StatusCode -ne 200) {
        $result.Error = "/healthz did not return 200."
        $lastResult = $result
        if ($attempt -lt $attempts) {
          Start-Sleep -Seconds $RetryDelaySec
          continue
        }
        return $result
      }
      if ($Path -eq "/healthz/deep" -and $response.StatusCode -ne 200) {
        $result.Error = "/healthz/deep did not return 200."
        $lastResult = $result
        if ($attempt -lt $attempts) {
          Start-Sleep -Seconds $RetryDelaySec
          continue
        }
        return $result
      }
      $result.Ok = $true
      return $result
    } catch {
      $statusCode = $null
      $body = ""
      if ($_.Exception.Response) {
        try {
          $statusCode = [int]$_.Exception.Response.StatusCode
          $stream = $_.Exception.Response.GetResponseStream()
          if ($stream) {
            $reader = New-Object System.IO.StreamReader($stream)
            $body = $reader.ReadToEnd()
            if ($body.Length -gt 500) {
              $body = $body.Substring(0, 500)
            }
          }
        } catch {
          $body = ""
        }
      }
      if ($statusCode) {
        $result.StatusCode = $statusCode
        Write-Host "$Path attempt=$attempt status=$statusCode body=$body"
      }
      Write-Host "$Path attempt=$attempt error=$($_.Exception.Message)"
      $result.Error = $_.Exception.Message
      $lastResult = $result
      if ($attempt -lt $attempts) {
        Start-Sleep -Seconds $RetryDelaySec
        continue
      }
      return $result
    }
  }
  return $lastResult
}

Push-Location $Root
try {
  Invoke-Step "CloudBase CLI availability" {
    foreach ($cmd in @("tcb", "cloudbase", "wxcloud")) {
      Write-Host "$cmd=$(if (Test-CommandExists $cmd) { 'found' } else { 'not-found' })"
    }
  }

  Invoke-Step "required external environment variables presence" {
    foreach ($name in @(
      "DB_PROVIDER",
      "MYSQL_HOST",
      "MYSQL_USER",
      "MYSQL_PASSWORD",
      "MYSQL_DATABASE",
      "ADMIN_EXPORT_TOKEN",
      "SECRET_KEY",
      "WECHAT_APPID",
      "WECHAT_SECRET"
    )) {
      Write-Host "$name=$(if (Test-EnvSet $name) { 'set' } else { 'missing' })"
    }
  }

  if (-not $SkipCloudBase) {
    Invoke-Step "CloudBase public health endpoints" {
      $results = @(
        Invoke-HealthRequest -BaseUrl $CloudBaseBaseUrl -Path "/healthz" -TimeoutSec $HealthTimeoutSec -RetryCount $HealthRetryCount -RetryDelaySec $HealthRetryDelaySec
        Invoke-HealthRequest -BaseUrl $CloudBaseBaseUrl -Path "/readyz" -TimeoutSec $HealthTimeoutSec -RetryCount $HealthRetryCount -RetryDelaySec $HealthRetryDelaySec
        Invoke-HealthRequest -BaseUrl $CloudBaseBaseUrl -Path "/healthz/deep" -TimeoutSec $HealthTimeoutSec -RetryCount $HealthRetryCount -RetryDelaySec $HealthRetryDelaySec
      )
      $failed = @($results | Where-Object { -not $_.Ok })
      if ($failed.Count -gt 0) {
        $summary = ($failed | ForEach-Object { "$($_.Path) status=$($_.StatusCode) error=$($_.Error)" }) -join "; "
        throw "CloudBase health endpoints failed: $summary"
      }
    }
  } else {
    Write-Host "CloudBase health checks skipped."
  }

  if (-not $SkipSqliteBackupRestore) {
    Invoke-Step "temporary SQLite backup and restore smoke test" {
      $tmp = Join-Path $env:TEMP ("safehome-task9-restore-" + [guid]::NewGuid().ToString("N"))
      New-Item -ItemType Directory -Path $tmp | Out-Null
      $db = Join-Path $tmp "safehome-test.sqlite3"
      $oldDatabasePath = [Environment]::GetEnvironmentVariable("DATABASE_PATH", "Process")
      $oldContentDir = [Environment]::GetEnvironmentVariable("CONTENT_DIR", "Process")
      try {
        $env:DATABASE_PATH = $db
        $env:CONTENT_DIR = (Resolve-Path "content").Path
        python -c "import sys; sys.path.insert(0, 'backend'); import database; database.init_db(); print('init_ok')"
        $before = Get-Date
        python backend/scripts/backup_sqlite.py
        $backup = Get-ChildItem -Path (Join-Path $Root "backups") -Filter "safehome_*.sqlite3" |
          Where-Object { $_.LastWriteTime -ge $before.AddSeconds(-2) } |
          Sort-Object LastWriteTime -Descending |
          Select-Object -First 1
        if (-not $backup) {
          throw "backup file not found"
        }
        python -c "import sqlite3, os; conn=sqlite3.connect(os.environ['DATABASE_PATH']); conn.execute('DELETE FROM goals'); conn.commit(); conn.close(); print('mutated_ok')"
        python backend/scripts/restore_sqlite.py $backup.FullName
        python -c "import sys; sys.path.insert(0, 'backend'); import database; print('health_ok=' + str(database.check_database_health()['ok']))"
        Remove-Item -LiteralPath $backup.FullName -Force
      } finally {
        if ($null -eq $oldDatabasePath) {
          Remove-Item Env:DATABASE_PATH -ErrorAction SilentlyContinue
        } else {
          $env:DATABASE_PATH = $oldDatabasePath
        }
        if ($null -eq $oldContentDir) {
          Remove-Item Env:CONTENT_DIR -ErrorAction SilentlyContinue
        } else {
          $env:CONTENT_DIR = $oldContentDir
        }
        if (Test-Path -LiteralPath $tmp) {
          Remove-Item -LiteralPath $tmp -Recurse -Force
        }
      }
    }
  } else {
    Write-Host "SQLite backup/restore smoke test skipped."
  }
} finally {
  Pop-Location
}

Write-Host "Task 9 external checks completed."
