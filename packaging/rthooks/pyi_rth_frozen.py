"""PyInstaller 运行时钩子：修复无控制台模式下 PyMuPDF / DLL 加载问题。"""
import os
import sys

if getattr(sys, "frozen", False):
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")

    if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        for sub in ("", "pymupdf"):
            dll_dir = os.path.join(base, sub) if sub else base
            if os.path.isdir(dll_dir):
                try:
                    os.add_dll_directory(dll_dir)
                except OSError:
                    pass
