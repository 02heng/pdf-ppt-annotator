"""在 PyInstaller 输出目录中测试 PyMuPDF + ImageTk 渲染链路。"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    internal = root / "dist" / "TOPDFAnnotator" / "_internal"
    if not internal.is_dir():
        print("MISSING bundle:", internal)
        return 1

    sys.path.insert(0, str(internal))
    os.chdir(internal)
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(internal))
        pymupdf_dir = internal / "pymupdf"
        if pymupdf_dir.is_dir():
            os.add_dll_directory(str(pymupdf_dir))

    import fitz  # noqa: F401
    from PIL import Image, ImageTk
    import tkinter as tk

    pdf_path = None
    desktop = Path.home() / "Desktop"
    for candidate in desktop.rglob("*.pdf"):
        pdf_path = candidate
        break
    if pdf_path is None:
        print("NO_PDF on Desktop")
        return 1

    print("PDF:", pdf_path)
    doc = fitz.open(str(pdf_path))
    page = doc[0]
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    data = pix.tobytes("png")
    img = Image.open(io.BytesIO(data))
    img.load()
    print("Image size:", img.size, "mode:", img.mode)

    win = tk.Tk()
    win.withdraw()
    tkimg = ImageTk.PhotoImage(img)
    print("PhotoImage ok:", tkimg.width(), "x", tkimg.height())
    win.destroy()
    doc.close()
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
