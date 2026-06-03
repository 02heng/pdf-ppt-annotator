"""渐变顶栏等装饰组件"""

from __future__ import annotations

import tkinter as tk
from typing import Tuple

import customtkinter as ctk

from src.ui.theme import UITheme


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _lerp_rgb(
    a: Tuple[int, int, int], b: Tuple[int, int, int], t: float
) -> Tuple[int, int, int]:
    return tuple(int(x + (y - x) * t) for x, y in zip(a, b))


class GradientToolbar(ctk.CTkFrame):
    """紫渐变工具栏容器，按钮放在 inner 上"""

    def __init__(self, master, height: int = 58, **kwargs):
        super().__init__(
            master,
            fg_color=UITheme.PURPLE_700,
            corner_radius=UITheme.RADIUS_LG,
            height=height,
            **kwargs,
        )
        self.pack_propagate(False)
        self._canvas = tk.Canvas(
            self,
            highlightthickness=0,
            borderwidth=0,
            bg=UITheme.PURPLE_700,
        )
        self.inner = ctk.CTkFrame(self, fg_color="transparent")
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.inner.place(x=0, y=0, relwidth=1, relheight=1)
        self.bind("<Configure>", self._paint_gradient)
        self.after(80, self._paint_gradient)

    def _paint_gradient(self, _event=None) -> None:
        w = max(self.winfo_width(), 2)
        h = max(self.winfo_height(), 2)
        self._canvas.delete("all")
        top = _hex_to_rgb(UITheme.GRADIENT_START)
        bottom = _hex_to_rgb(UITheme.GRADIENT_END)
        for y in range(h):
            t = y / max(h - 1, 1)
            r, g, b = _lerp_rgb(top, bottom, t)
            fill = f"#{r:02x}{g:02x}{b:02x}"
            self._canvas.create_line(0, y, w, y, fill=fill)


class SectionHeader(ctk.CTkFrame):
    """侧栏分区标题（紫条 + 文案）"""

    def __init__(self, master, text: str, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        accent = ctk.CTkFrame(self, width=4, height=18, corner_radius=2, fg_color=UITheme.PURPLE_600)
        accent.pack(side="left", padx=(0, 8))
        accent.pack_propagate(False)
        ctk.CTkLabel(
            self,
            text=text,
            font=UITheme.font_section(),
            text_color=UITheme.TEXT,
        ).pack(side="left")
