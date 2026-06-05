# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 规格：Windows / macOS 共用。在项目根目录执行 build 脚本。"""
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH).resolve().parent
_version_file = ROOT / "VERSION"
APP_VERSION = (
    _version_file.read_text(encoding="utf-8").strip()
    if _version_file.is_file()
    else "0.1.0"
)

import platform

block_cipher = None

# macOS 构建目标架构：
# universal2 需要所有依赖均为 fat binary（PIL/PyMuPDF 等 C 扩展通常只有单架构，无法满足）
# 因此默认构建 x86_64 版本：
#   - Intel Mac 原生运行
#   - Apple Silicon Mac 通过 Rosetta 2 自动兼容（macOS 会提示安装 Rosetta）
# 如需原生 arm64 版本，可在 Apple Silicon 机器上取消注释下一行
# _mac_arch = "arm64"
_mac_arch = None

_brand = ROOT / "assets" / "branding"
_icon_ico = _brand / "icon.ico"
_icon_png = _brand / "icon.png"
_toolbar_png = _brand / "toolbar-logo.png"

datas = [
    (str(ROOT / "config" / "default.yaml"), "config"),
    (str(ROOT / "src" / "web"), "web"),
]
if _brand.is_dir():
    datas.append((str(_brand), "assets/branding"))
datas += collect_data_files("customtkinter")

hiddenimports = [
    "PIL._tkinter_finder",
    "pkg_resources.py2_warn",
]
for pkg in ("crewai", "flask", "pydantic", "litellm", "instructor"):
    try:
        hiddenimports += collect_submodules(pkg)
    except Exception:
        pass

excludes = [
    "tests",
    "pytest",
    "IPython",
    "matplotlib",
    "numpy.distutils",
    "tkinter.test",
]

a = Analysis(
    [str(ROOT / "src" / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

_win_icon = str(_icon_ico) if _icon_ico.is_file() and sys.platform == "win32" else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TOPDFAnnotator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=sys.platform == "darwin",
    target_arch=_mac_arch,
    codesign_identity=None,
    entitlements_file=None,
    icon=_win_icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="TOPDFAnnotator",
)

_mac_icon = str(_icon_png) if _icon_png.is_file() and sys.platform == "darwin" else None

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="TOPDFAnnotator.app",
        icon=_mac_icon,
        bundle_identifier="com.topdf.annotator",
        info_plist={
            "CFBundleName": "TO PDF 批注工具",
            "CFBundleDisplayName": "TO PDF 批注工具",
            "CFBundleShortVersionString": APP_VERSION,
            "CFBundleVersion": APP_VERSION,
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
        },
    )
