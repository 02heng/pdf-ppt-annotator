"""应用品牌图标路径与窗口设置"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from src.utils.runtime import get_resource_path


def get_branding_dir() -> Path:
    if getattr(sys, "frozen", False):
        return get_resource_path("assets", "branding")
    return get_resource_path("assets", "branding")


def get_icon_ico_path() -> Optional[Path]:
    p = get_branding_dir() / "icon.ico"
    return p if p.is_file() else None


def get_icon_png_path() -> Optional[Path]:
    p = get_branding_dir() / "icon.png"
    return p if p.is_file() else None


def get_toolbar_logo_path() -> Optional[Path]:
    p = get_branding_dir() / "toolbar-logo.png"
    if p.is_file():
        return p
    p = get_resource_path("src", "web", "brand-logo.png")
    if not getattr(sys, "frozen", False) and p.is_file():
        return p
    p = get_resource_path("web", "brand-logo.png")
    return p if p.is_file() else None


def apply_window_icon(window) -> None:
    """设置 Tk/CTk 窗口与任务栏图标（Windows 优先 .ico，含子窗口 Toplevel）"""
    import tkinter as tk

    ico = get_icon_ico_path()
    png = get_icon_png_path()
    try:
        if ico:
            path = str(ico)
            try:
                window.iconbitmap(path)
            except tk.TclError:
                window.iconbitmap(default=path)
            if png:
                try:
                    photo = tk.PhotoImage(file=str(png))
                    window.iconphoto(True, photo)
                    window._brand_icon_photo = photo
                except tk.TclError:
                    pass
            return
        if png:
            photo = tk.PhotoImage(file=str(png))
            window.iconphoto(True, photo)
            if not getattr(window, "_brand_icon_photo", None):
                window._brand_icon_photo = photo
    except Exception:
        pass


def load_toolbar_logo_ctk(size: int = 28):
    """顶栏品牌小图（CustomTkinter，需 PIL.Image）"""
    import customtkinter as ctk
    from PIL import Image

    path = get_toolbar_logo_path()
    if not path:
        return None
    try:
        pil = Image.open(path).convert("RGBA")
        return ctk.CTkImage(
            light_image=pil,
            dark_image=pil,
            size=(size, size),
        )
    except Exception:
        return None
