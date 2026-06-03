#Requires -Version 5.1
<#
.SYNOPSIS
  构建 Windows 便携版与安装包。

.DESCRIPTION
  1. 安装/更新打包依赖 (requirements-build.txt)
  2. PyInstaller 生成 dist\TOPDFAnnotator\
  3. 若检测到 Inno Setup，生成 packaging\output\*.exe 安装程序

  安装包不包含 Python 源码，用户无需 pip install。
#>
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==> 项目目录: $Root"

Write-Host "==> 生成应用图标 (assets/branding/icon.ico)..."
python scripts/generate_app_icons.py
if (-not (Test-Path (Join-Path $Root "assets\branding\icon.ico"))) {
    throw "图标生成失败：请先运行 python scripts/generate_app_icons.py"
}

Write-Host "==> 安装打包依赖..."
python -m pip install -r requirements-build.txt -q

Write-Host "==> PyInstaller 构建..."
python -m PyInstaller --noconfirm --clean "packaging\TOPDFAnnotator.spec"

$AppDir = Join-Path $Root "dist\TOPDFAnnotator"
if (-not (Test-Path (Join-Path $AppDir "TOPDFAnnotator.exe"))) {
    throw "构建失败：未找到 TOPDFAnnotator.exe"
}

Write-Host "==> 便携版已生成: $AppDir"

$IsccCandidates = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$Iscc = $IsccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($Iscc) {
    Write-Host "==> Inno Setup 编译安装包..."
    & $Iscc "packaging\windows\installer.iss"
    Write-Host "==> 安装包: packaging\output\TOPDFAnnotator-Setup-1.0.0-win64.exe"
} else {
    Write-Host ""
    Write-Host "未检测到 Inno Setup 6，已跳过安装包生成。" -ForegroundColor Yellow
    Write-Host "便携版可直接分发 dist\TOPDFAnnotator 文件夹，或安装 Inno Setup 后重新运行本脚本。"
    Write-Host "下载: https://jrsoftware.org/isdl.php"
}

Write-Host ""
Write-Host "完成。" -ForegroundColor Green
