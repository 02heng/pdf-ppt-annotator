# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 规格：Windows / macOS 共用。在项目根目录执行 build 脚本。"""
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH).resolve().parent

block_cipher = None

datas = [
    (str(ROOT / "config" / "default.yaml"), "config"),
    (str(ROOT / "src" / "web"), "web"),
]
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
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
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

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="TOPDFAnnotator.app",
        icon=None,
        bundle_identifier="com.topdf.annotator",
        info_plist={
            "CFBundleName": "TO PDF 批注工具",
            "CFBundleDisplayName": "TO PDF 批注工具",
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleVersion": "1.0.0",
            "NSHighResolutionCapable": True,
        },
    )
