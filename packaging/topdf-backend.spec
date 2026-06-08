# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller：冻结 Electron 用 Flask 后端。"""
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_dynamic_libs, collect_submodules

ROOT = Path(SPECPATH).resolve().parent
_version_file = ROOT / "VERSION"
APP_VERSION = _version_file.read_text(encoding="utf-8").strip() if _version_file.is_file() else "0.2.0"

block_cipher = None
_brand = ROOT / "assets" / "branding"

datas = [
    (str(ROOT / "config" / "default.yaml"), "config"),
    (str(ROOT / "src" / "web"), "web"),
]
if _brand.is_dir():
    datas.append((str(_brand), "assets/branding"))

_binaries = collect_dynamic_libs("pymupdf")

_pkg_datas, _pkg_bins, _pkg_hidden = [], [], []
for pkg in ("flask", "werkzeug", "pydantic", "openai", "pptx", "liteparse"):
    try:
        d, b, h = collect_all(pkg)
        _pkg_datas += d
        _pkg_bins += b
        _pkg_hidden += h
    except Exception:
        pass

datas += _pkg_datas
_binaries += _pkg_bins

hiddenimports = _pkg_hidden + [
    "fitz",
    "pymupdf",
    "pymupdf._mupdf",
    "pymupdf._extra",
    "yaml",
    "PIL",
    "PIL.Image",
]
for pkg in ("flask", "werkzeug", "pydantic", "liteparse"):
    try:
        hiddenimports += collect_submodules(pkg)
    except Exception:
        pass

excludes = [
    "matplotlib",
    "IPython",
    "pytest",
    "tests",
]

a = Analysis(
    [str(ROOT / "src" / "run_electron_server.py")],
    pathex=[str(ROOT)],
    binaries=_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(ROOT / "packaging" / "rthooks" / "pyi_rth_frozen.py")],
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
    name="topdf-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
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
    upx=False,
    upx_exclude=[],
    name="topdf-backend",
)
