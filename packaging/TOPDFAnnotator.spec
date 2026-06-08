# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 规格：Windows / macOS 共用。在项目根目录执行 build 脚本。"""
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

ROOT = Path(SPECPATH).resolve().parent
_version_file = ROOT / "VERSION"
APP_VERSION = (
    _version_file.read_text(encoding="utf-8").strip()
    if _version_file.is_file()
    else "0.1.0"
)

import platform

block_cipher = None

# macOS 目标架构：根据环境变量决定，默认使用当前平台原生架构
import os as _os_early
import platform as _platform
_mac_arch = _os_early.environ.get("PYINSTALLER_TARGET_ARCH", None)

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

# CustomTkinter 主题/字体（缺失会导致启动闪退）
datas += collect_data_files("customtkinter")
# darkdetect：CustomTkinter 在 macOS 上用它探测系统外观，缺失会启动闪退
try:
    datas += collect_data_files("darkdetect")
except Exception:
    pass

# crewai 翻译文件 (i18n) — 仅在 crewai 可用时包含
try:
    import crewai as _crewai_pkg

    _crewai_dir = Path(_crewai_pkg.__file__).parent
    _crewai_translations = _crewai_dir / "translations"
    if _crewai_translations.is_dir():
        datas.append((str(_crewai_translations), "crewai/translations"))
except ImportError:
    pass

hiddenimports = [
    "PIL._tkinter_finder",
    "PIL.ImageTk",
    "fitz",
    "pymupdf",
    "pymupdf._mupdf",
    "pymupdf._extra",
    "pymupdf.mupdf",
    "tkinter",
    "tkinter.font",
    "tkinter.ttk",
    "_tkinter",
    "darkdetect",
    "customtkinter",
]
for pkg in ("flask", "pydantic", "liteparse"):
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

import os as _os
import glob as _glob

# PyMuPDF 原生库（缺失会导致 PDF 预览白屏）
_binaries = collect_dynamic_libs("pymupdf")
_pymupdf_dir = _os.path.dirname(_os.path.abspath(__import__("pymupdf").__file__))
if sys.platform == "win32":
    _mupdf_dll = _os.path.join(_pymupdf_dir, "mupdfcpp64.dll")
    if _os.path.isfile(_mupdf_dll) and not any(src == _mupdf_dll for src, _ in _binaries):
        _binaries.append((_mupdf_dll, "pymupdf"))
else:
    for _ext in ("*.dylib", "*.so"):
        for _lib in _glob.glob(_os.path.join(_pymupdf_dir, _ext)):
            if not any(src == _lib for src, _ in _binaries):
                _binaries.append((_lib, "pymupdf"))

# UPX 压缩会破坏 VC 运行时与 MuPDF DLL，导致闪退或白屏
_upx_exclude = [
    "vcruntime140.dll",
    "vcruntime140_1.dll",
    "msvcp140.dll",
    "python*.dll",
    "mupdfcpp64.dll",
    "_mupdf.pyd",
    "_extra.pyd",
    "tcl86t.dll",
    "tk86t.dll",
]

_runtime_hooks = [str(ROOT / "packaging" / "rthooks" / "pyi_rth_frozen.py")]

a = Analysis(
    [str(ROOT / "src" / "main.py")],
    pathex=[str(ROOT)],
    binaries=_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=_runtime_hooks,
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
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
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
    upx=False,
    upx_exclude=_upx_exclude,
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
            "NSRequiresAquaSystemAppearance": True,
            "CFBundleDocumentTypes": [
                {
                    "CFBundleTypeName": "PDF Document",
                    "CFBundleTypeRole": "Viewer",
                    "LSItemContentTypes": ["com.adobe.pdf"],
                },
                {
                    "CFBundleTypeName": "PowerPoint Presentation",
                    "CFBundleTypeRole": "Viewer",
                    "LSItemContentTypes": [
                        "org.openxmlformats.presentationml.presentation",
                        "com.microsoft.powerpoint.ppt",
                    ],
                },
            ],
        },
    )
