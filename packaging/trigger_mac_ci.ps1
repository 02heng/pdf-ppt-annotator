#Requires -Version 5.1
# 推送 CI 工作流并触发 macOS arm64 + Intel 构建
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> 检查 GitHub 连接..."
gh auth status | Out-Null

$scopes = (gh auth status 2>&1 | Out-String)
if ($scopes -notmatch "workflow") {
    Write-Host "需要 workflow 权限，请在浏览器完成授权：" -ForegroundColor Yellow
    gh auth refresh -h github.com -s workflow
}

Write-Host "==> 推送 master..."
git push origin master

Write-Host "==> 触发 GitHub Actions（仅 macOS arm64 + Intel）..."
gh workflow run "Build Installers" -f platforms=mac-only

Write-Host ""
Write-Host "已触发构建。查看进度：" -ForegroundColor Green
Write-Host "  https://github.com/02heng/pdf-ppt-annotator/actions"
Write-Host ""
Write-Host "完成后在 Artifacts 下载："
Write-Host "  - macos-arm64-installers"
Write-Host "  - macos-x64-installers"
