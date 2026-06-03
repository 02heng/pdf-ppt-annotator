"""系统已安装字体列表（供批注字体选择）。"""
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

_PREFERRED = (
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


def get_system_font_families(*, limit: int = 120) -> list[str]:
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
        families = list(_PREFERRED)

    ordered: list[str] = []
    seen = set()
    for name in _PREFERRED:
        if name in families and name not in seen:
            ordered.append(name)
            seen.add(name)
    for name in families:
        if name not in seen:
            ordered.append(name)
            seen.add(name)
    return ordered[:limit]
