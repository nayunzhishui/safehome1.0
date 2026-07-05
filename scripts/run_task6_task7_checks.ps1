param(
  [switch]$SkipWebBuild
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "[1/5] Python syntax check"
python -m py_compile `
  backend\routes\auth.py `
  backend\routes\messages.py `
  backend\routes\profile.py `
  backend\routes\supervision.py `
  backend\routes\assessments.py `
  backend\routes\admin.py `
  backend\database.py `
  backend\models.py `
  backend\services\assessment_profile_service.py `
  backend\services\message_service.py

Write-Host "[2/5] Content validation"
python backend\scripts\validate_content.py

Write-Host "[3/5] Backend tests"
python -m pytest backend\tests -q

Write-Host "[4/5] Miniprogram static checks"
node -e "const fs=require('fs'); const path=require('path'); const root='apps/miniprogram'; function walk(d){for(const f of fs.readdirSync(d)){const p=path.join(d,f); const s=fs.statSync(p); if(s.isDirectory()) walk(p); else if(p.endsWith('.json')) JSON.parse(fs.readFileSync(p,'utf8'));}} walk(root); console.log('miniprogram json ok');"
node -e "const fs=require('fs'); const files=['apps/miniprogram/pages/home/index.js','apps/miniprogram/pages/profile/index.js','apps/miniprogram/pages/messages/index.js','apps/miniprogram/pages/message-detail/index.js','apps/miniprogram/pages/emergency-guide/index.js','apps/miniprogram/pages/emergency-resources/index.js','apps/miniprogram/services/api.js']; for (const f of files) { new Function(fs.readFileSync(f,'utf8')); } console.log('miniprogram js syntax ok');"

if (-not $SkipWebBuild) {
  Write-Host "[5/5] Web build"
  Push-Location apps\web
  npm run build
  Pop-Location
} else {
  Write-Host "[5/5] Web build skipped"
}

Write-Host "Task 6/7 checks completed."
