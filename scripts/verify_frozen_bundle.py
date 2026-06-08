"""在 PyInstaller 输出目录中验证 Electron 后端关键资源与 PyMuPDF 导入。"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    internal = root / "packaging" / "dist" / "topdf-backend" / "_internal"
    if not internal.is_dir():
        internal = root / "packaging" / "dist" / "topdf-backend"

    required = [
        internal / "pymupdf" / "mupdfcpp64.dll",
        internal / "pymupdf" / "_mupdf.pyd",
        internal / "web" / "index.html",
        internal / "web" / "pdf.min.js",
        internal / "web" / "pdf.worker.min.js",
        internal / "config" / "default.yaml",
    ]
    missing = [str(p.relative_to(internal)) for p in required if not p.is_file()]
    if missing:
        print("MISSING:", ", ".join(missing))
        return 1

    sys.path.insert(0, str(internal))
    os.chdir(internal)
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(internal))
        pymupdf_dir = internal / "pymupdf"
        if pymupdf_dir.is_dir():
            os.add_dll_directory(str(pymupdf_dir))

    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")

    import fitz  # noqa: F401

    print("OK: topdf-backend bundle resources and fitz import verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
