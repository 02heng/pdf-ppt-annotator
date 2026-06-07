"""系统已安装字体列表（供批注字体选择）。"""
from __future__ import annotations

import sys
import tkinter as tk
import tkinter.font as tkfont

_PREFERRED_WIN = (
    "Microsoft YaHei UI",
    "Microsoft YaHei",
    "微软雅黑",
    "SimHei",
    "黑体",
    "SimSun",
    "宋体",
    "KaiTi",
    "楷体",
    "FangSong",
    "仿宋",
    "Arial",
    "Times New Roman",
    "Segoe UI",
    "Calibri",
    "Tahoma",
    "Verdana",
)

_PREFERRED_MAC = (
    "PingFang SC",
    "PingFang TC",
    "Hiragino Sans GB",
    "Heiti SC",
    "STHeiti",
    "Songti SC",
    "STSong",
    "Kaiti SC",
    "STKaiti",
    "Helvetica Neue",
    "Helvetica",
    "Arial",
    "Times New Roman",
    "Verdana",
)

_PREFERRED_LINUX = (
    "Noto Sans CJK SC",
    "WenQuanYi Micro Hei",
    "Source Han Sans SC",
    "Droid Sans Fallback",
    "Arial",
    "Times New Roman",
    "Verdana",
)


def _get_preferred() -> tuple:
    if sys.platform == "darwin":
        return _PREFERRED_MAC
    if sys.platform == "win32":
        return _PREFERRED_WIN
    return _PREFERRED_LINUX


def get_system_font_families(*, limit: int = 120) -> list[str]:
    preferred = _get_preferred()
    try:
        root = tk._default_root
        if root is None:
            root = tk.Tk()
            root.withdraw()
            families = sorted(set(tkfont.families(root)))
            root.destroy()
        else:
            families = sorted(set(tkfont.families(root)))
    except Exception:
        families = list(preferred)

    ordered: list[str] = []
    seen = set()
    for name in preferred:
        if name in families and name not in seen:
            ordered.append(name)
            seen.add(name)
    for name in families:
        if name not in seen:
            ordered.append(name)
            seen.add(name)
    return ordered[:limit]
