param(
  [string]$OutputDirectory = ""
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$TmpRoot = Join-Path $Root ".codex_tmp"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
if (-not $OutputDirectory) {
  $OutputDirectory = Join-Path $TmpRoot "all-interfaces-deployment-$Stamp"
}
$OutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)
$StagingRoot = Join-Path $TmpRoot ("all-interfaces-staging-" + [Guid]::NewGuid().ToString("N"))
$CloudStage = Join-Path $StagingRoot "cloudbase"
$MiniStage = Join-Path $StagingRoot "miniprogram"
$CloudZip = Join-Path $OutputDirectory "safehome-cloudbase-all-interfaces-$Stamp.zip"
$MiniZip = Join-Path $OutputDirectory "safehome-miniprogram-upload-$Stamp.zip"

. (Join-Path $PSScriptRoot "cloudbase_package_source.ps1")

function Assert-ChildPath {
  param([string]$Parent, [string]$Child)
  $parentFull = [System.IO.Path]::GetFullPath($Parent).TrimEnd("\", "/") + [System.IO.Path]::DirectorySeparatorChar
  $childFull = [System.IO.Path]::GetFullPath($Child)
  if (-not $childFull.StartsWith($parentFull, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe staging path: $childFull"
  }
}

function Copy-Required {
  param([string]$RelativePath, [string]$DestinationRoot)
  $source = Join-Path $Root $RelativePath
  if (-not (Test-Path -LiteralPath $source)) {
    throw "Missing required source: $RelativePath"
  }
  $target = Join-Path $DestinationRoot $RelativePath
  $parent = Split-Path -Parent $target
  New-Item -ItemType Directory -Force -Path $parent | Out-Null
  Copy-Item -LiteralPath $source -Destination $target -Recurse -Force
}

function New-PortableZip {
  param([string]$SourceDirectory, [string]$ZipPath)
  Add-Type -AssemblyName System.IO.Compression
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $archive = [System.IO.Compression.ZipFile]::Open($ZipPath, [System.IO.Compression.ZipArchiveMode]::Create)
  try {
    $prefix = [System.IO.Path]::GetFullPath($SourceDirectory).TrimEnd("\", "/") + [System.IO.Path]::DirectorySeparatorChar
    Get-ChildItem -LiteralPath $SourceDirectory -Recurse -File -Force | Sort-Object FullName | ForEach-Object {
      $relative = $_.FullName.Substring($prefix.Length).Replace("\", "/")
      [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
        $archive,
        $_.FullName,
        $relative,
        [System.IO.Compression.CompressionLevel]::Optimal
      ) | Out-Null
    }
  } finally {
    $archive.Dispose()
  }
}

function Get-TreeFingerprint {
  param([string]$SourceDirectory, [string[]]$ExcludedRelativePaths = @())
  $prefix = [System.IO.Path]::GetFullPath($SourceDirectory).TrimEnd("\", "/") + [System.IO.Path]::DirectorySeparatorChar
  $lines = Get-ChildItem -LiteralPath $SourceDirectory -Recurse -File -Force | ForEach-Object {
    $relative = $_.FullName.Substring($prefix.Length).Replace("\", "/")
    if ($ExcludedRelativePaths -notcontains $relative) {
      "$relative=$((Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash)"
    }
  } | Sort-Object
  $bytes = [System.Text.Encoding]::UTF8.GetBytes(($lines -join "`n"))
  $sha = [System.Security.Cryptography.SHA256]::Create()
  try {
    return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace("-", "").ToLowerInvariant()
  } finally {
    $sha.Dispose()
  }
}

function Write-HashSidecar {
  param([string]$Path)
  $hash = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
  Set-Content -LiteralPath "$Path.sha256" -Value "$hash  $([System.IO.Path]::GetFileName($Path))" -Encoding ASCII
  return $hash
}

Assert-ChildPath -Parent $TmpRoot -Child $StagingRoot
New-Item -ItemType Directory -Force -Path $OutputDirectory, $CloudStage, $MiniStage | Out-Null

try {
  $head = (git -C $Root rev-parse HEAD).Trim()
  $branch = (git -C $Root branch --show-current).Trim()
  $dirty = [bool](git -C $Root status --short)
  $generatedAt = (Get-Date).ToUniversalTime().ToString("o")

  foreach ($path in @("Dockerfile", ".dockerignore", "backend", "content", "shared")) {
    Copy-Required -RelativePath $path -DestinationRoot $CloudStage
  }
  Remove-CloudBasePackageArtifacts -SourceRoot $CloudStage
  Rename-CloudBaseProfileModels -SourceRoot $CloudStage
  $backendTests = Join-Path $CloudStage "backend\tests"
  if (Test-Path -LiteralPath $backendTests) {
    Remove-Item -LiteralPath $backendTests -Recurse -Force
  }
  Copy-Item -LiteralPath (Join-Path $Root "config\production_features.enabled.example.env") `
    -Destination (Join-Path $CloudStage "CLOUDBASE_ENVIRONMENT_VARIABLES.txt") -Force

  & python (Join-Path $Root "scripts\generate_build_fingerprint.py") `
    --root $CloudStage `
    --output (Join-Path $CloudStage "backend\build_info.json") `
    --commit-sha $head `
    --build-time $generatedAt
  if ($LASTEXITCODE -ne 0) { throw "Build fingerprint generation failed." }

  $cloudTree = Get-TreeFingerprint -SourceDirectory $CloudStage -ExcludedRelativePaths @("ALL_INTERFACES_PACKAGE_MANIFEST.txt")
  @(
    "SafeHome CloudBase all-interface validation package",
    "GeneratedAt=$generatedAt",
    "Branch=$branch",
    "Head=$head",
    "SourceMode=working_tree_snapshot",
    "WorkingTreeDirty=$($dirty.ToString().ToLowerInvariant())",
    "SourceFingerprint=$cloudTree",
    "CloudEnvId=prod-d3gl35otiaa7c8d24",
    "CloudService=flask-gh3l",
    "AuthenticationAndAuthorization=enforced",
    "FaultInjection=disabled",
    "AutomaticExternalIngestAndModelReplacement=disabled",
    "ExternalSecrets=must_be_configured_in_cloudbase"
  ) | Set-Content -LiteralPath (Join-Path $CloudStage "ALL_INTERFACES_PACKAGE_MANIFEST.txt") -Encoding UTF8

  $compileTargets = @(
    (Join-Path $CloudStage "backend\app.py"),
    (Join-Path $CloudStage "backend\config.py"),
    (Join-Path $CloudStage "backend\database.py")
  )
  & python -c "from pathlib import Path; import sys; [compile(Path(p).read_text(encoding='utf-8'), p, 'exec') for p in sys.argv[1:]]" @compileTargets
  if ($LASTEXITCODE -ne 0) { throw "CloudBase staged Python compile failed." }

  Get-ChildItem -LiteralPath (Join-Path $Root "apps\miniprogram") -Force | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $MiniStage -Recurse -Force
  }
  foreach ($relative in @("project.private.config.json", "services\api-contract.generated.js")) {
    $target = Join-Path $MiniStage $relative
    if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Force }
  }
  Remove-CloudBasePackageArtifacts -SourceRoot $MiniStage

  $appConfig = Get-Content -LiteralPath (Join-Path $MiniStage "app.json") -Raw -Encoding UTF8 | ConvertFrom-Json
  $projectConfig = Get-Content -LiteralPath (Join-Path $MiniStage "project.config.json") -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($appConfig.pages -notcontains "pages/support-assistant/index") {
    throw "Mini Program package does not expose the support assistant page."
  }
  if ($projectConfig.appid -ne "wxd548597e78862269" -or -not $projectConfig.setting.urlCheck) {
    throw "Mini Program production project configuration is invalid."
  }
  $cloudConfigText = Get-Content -LiteralPath (Join-Path $MiniStage "services\cloudConfig.js") -Raw -Encoding UTF8
  foreach ($required in @("prod-d3gl35otiaa7c8d24", "flask-gh3l", "useLocalHttp: false")) {
    if ($cloudConfigText -notmatch [regex]::Escape($required)) {
      throw "Mini Program CloudBase configuration is missing: $required"
    }
  }
  $miniBytes = (Get-ChildItem -LiteralPath $MiniStage -Recurse -File | Measure-Object Length -Sum).Sum
  if ($miniBytes -gt 2MB) {
    throw "Mini Program source exceeds the 2 MiB main-package budget: $miniBytes bytes"
  }
  $miniTree = Get-TreeFingerprint -SourceDirectory $MiniStage -ExcludedRelativePaths @("MINIPROGRAM_UPLOAD_MANIFEST.txt")
  @(
    "SafeHome WeChat Mini Program upload package",
    "GeneratedAt=$generatedAt",
    "Branch=$branch",
    "Head=$head",
    "SourceMode=working_tree_snapshot",
    "WorkingTreeDirty=$($dirty.ToString().ToLowerInvariant())",
    "SourceFingerprint=$miniTree",
    "AppId=wxd548597e78862269",
    "CloudEnvId=prod-d3gl35otiaa7c8d24",
    "CloudService=flask-gh3l",
    "Excluded=project.private.config.json,services/api-contract.generated.js,node_modules,dist,caches"
  ) | Set-Content -LiteralPath (Join-Path $MiniStage "MINIPROGRAM_UPLOAD_MANIFEST.txt") -Encoding UTF8

  New-PortableZip -SourceDirectory $CloudStage -ZipPath $CloudZip
  New-PortableZip -SourceDirectory $MiniStage -ZipPath $MiniZip
  $cloudHash = Write-HashSidecar -Path $CloudZip
  $miniHash = Write-HashSidecar -Path $MiniZip

  $summary = [ordered]@{
    schema = "safehome.all-interfaces-deployment.v1"
    generated_at = $generatedAt
    branch = $branch
    head = $head
    working_tree_dirty = $dirty
    cloudbase = [ordered]@{
      path = $CloudZip
      sha256 = $cloudHash
      source_fingerprint = $cloudTree
      env_id = "prod-d3gl35otiaa7c8d24"
      service = "flask-gh3l"
    }
    miniprogram = [ordered]@{
      path = $MiniZip
      sha256 = $miniHash
      source_fingerprint = $miniTree
      source_bytes = $miniBytes
      appid = "wxd548597e78862269"
    }
  }
  $summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OutputDirectory "deployment-summary.json") -Encoding UTF8
  @(
    "SafeHome 全接口联调部署包使用说明",
    "",
    "1. 后端云托管：在 CloudBase 环境 prod-d3gl35otiaa7c8d24 的服务 flask-gh3l 新建版本，上传 safehome-cloudbase-all-interfaces-*.zip。",
    "2. 云端变量：参考后端包根目录 CLOUDBASE_ENVIRONMENT_VARIABLES.txt，把占位符替换为 CloudBase 密钥管理中的真实值；不要把 Secret 写进 ZIP。",
    "3. 必需既有变量：DB_PROVIDER/MySQL 连接、SECRET_KEY、ADMIN_EXPORT_TOKEN。缺少时生产容器会拒绝启动。",
    "4. DeepSeek：参与者与研究者 AI 接口已开启；未配置 DEEPSEEK_API_KEY 时接口会安全降级，不会泄露密钥。",
    "5. 微信订阅发送：必须同时配置 AppSecret、模板 ID、字段映射和调度令牌；否则不要在云端设置 WECHAT_SUBSCRIBE_SEND_ENABLED=1。",
    "6. 小程序：解压 safehome-miniprogram-upload-*.zip，在微信开发者工具中导入解压目录，编译后点击上传按钮；微信开发者工具不能直接把 ZIP 当作代码版本提交。",
    "7. 发布顺序：先发布后端并验证 /healthz、/readyz，再上传小程序；不要颠倒。",
    "8. 安全边界：包未关闭身份认证、角色能力和对象范围校验；生产故障注入、自动外部数据摄取和模型自动替换仍关闭。",
    "9. 完整性：上传前核对同目录 .sha256 和 deployment-summary.json。"
  ) | Set-Content -LiteralPath (Join-Path $OutputDirectory "UPLOAD_INSTRUCTIONS.txt") -Encoding UTF8
  $summary | ConvertTo-Json -Depth 6
} finally {
  if (Test-Path -LiteralPath $StagingRoot) {
    Assert-ChildPath -Parent $TmpRoot -Child $StagingRoot
    Remove-Item -LiteralPath $StagingRoot -Recurse -Force
  }
}
