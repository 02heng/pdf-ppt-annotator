#Requires -Version 5.1
<#
.SYNOPSIS
  构建 Electron 版 Windows 安装包（开箱即用，内置 Python 后端）。

.DESCRIPTION
  1. 生成品牌图标 (scripts/generate_app_icons.py)
  2. PyInstaller 冻结 Flask 后端 → packaging/dist/topdf-backend/
  3. electron-builder 生成 NSIS 安装包 → packaging/output/

  用户安装后无需 Python / pip，图标均为 TO PDF 品牌 logo。
  参考 AI-writer-master 的 build-backend + after-pack + NSIS 方案。
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$AppVersion = (Get-Content -LiteralPath (Join-Path $Root "VERSION") -Raw).Trim()
if (-not $AppVersion) { $AppVersion = "0.2.0" }

Write-Host "==> 项目目录: $Root"
Write-Host "==> 版本: v$AppVersion"

Write-Host "==> 生成应用图标..."
python scripts/generate_app_icons.py
if (-not (Test-Path (Join-Path $Root "electron\assets\icon.ico"))) {
    throw "图标生成失败"
}

Write-Host "==> 安装 Python 打包依赖..."
python -m pip install -r requirements-build.txt -q

Write-Host "==> 安装 Electron 依赖..."
Push-Location (Join-Path $Root "electron")
if (-not (Test-Path "node_modules")) {
    npm install
}

Write-Host "==> 构建安装包 (icons + vendor + PyInstaller + electron-builder)..."
Push-Location (Join-Path $Root "electron")
$env:ELECTRON_MIRROR = "https://npmmirror.com/mirrors/electron/"
$env:ELECTRON_BUILDER_BINARIES_MIRROR = "https://npmmirror.com/mirrors/electron-builder-binaries/"
npm run dist
Pop-Location

$OutputDir = Join-Path $Root "packaging\output"
$Setups = Get-ChildItem -Path $OutputDir -Filter "*Setup*.exe" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending
if ($Setups.Count -eq 0) {
    Write-Host "未找到 NSIS Setup，请检查 packaging\output\" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "安装包已生成:" -ForegroundColor Green
    Write-Host "  $($Setups[0].FullName)"
}

Write-Host ""
Write-Host "Build finished." -ForegroundColor Green
