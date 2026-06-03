"""紫白主题消息框（替代系统 messagebox）"""

from __future__ import annotations

import customtkinter as ctk

from src.ui.theme import UITheme
from src.utils.branding import apply_window_icon


class ThemedDialog(ctk.CTkToplevel):
    """统一风格：系统标题栏 + 白内容区 + 主题按钮"""

    def __init__(
        self,
        master,
        title: str,
        message: str,
        *,
        kind: str = "yesno",
        width: int = 440,
    ):
        super().__init__(master)
        self.result: bool | None = None
        self._kind = kind

        self.title(title)
        self.geometry(f"{width}x1")
        self.resizable(False, False)
        self.configure(fg_color=UITheme.BG)

        self.transient(master)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        apply_window_icon(self)
        self.after(50, lambda: apply_window_icon(self))

        self._build(title, message)
        self.update_idletasks()
        h = max(self.winfo_reqheight(), 200)
        self.geometry(f"{width}x{h}")
        self._center_on(master)

        self.grab_set()
        self.focus_force()
        if self._kind == "yesno":
            self.bind("<Return>", lambda _e: self._on_yes())
            self.bind("<Escape>", lambda _e: self._on_no())
        else:
            self.bind("<Return>", lambda _e: self._on_ok())
            self.bind("<Escape>", lambda _e: self._on_close())

    def _center_on(self, master) -> None:
        self.update_idletasks()
        mw = master.winfo_width()
        mh = master.winfo_height()
        mx = master.winfo_rootx()
        my = master.winfo_rooty()
        w = self.winfo_width()
        h = self.winfo_height()
        x = mx + (mw - w) // 2
        y = my + (mh - h) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _on_close(self) -> None:
        if self._kind == "yesno":
            self.result = False
        else:
            self.result = True
        self.grab_release()
        self.destroy()

    def _build(self, title: str, message: str) -> None:
        body = ctk.CTkFrame(self, fg_color=UITheme.SURFACE, corner_radius=0)
        body.pack(fill="both", expand=True, padx=0, pady=0)

        content = ctk.CTkFrame(body, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=UITheme.PAD, pady=UITheme.PAD)

        icon_frame = ctk.CTkFrame(
            content,
            width=40,
            height=40,
            corner_radius=20,
            fg_color=UITheme.PURPLE_100,
        )
        icon_frame.pack(side="left", anchor="n", padx=(0, 12))
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(
            icon_frame,
            text="!",
            font=ctk.CTkFont(family=UITheme.FONT_FAMILY, size=20, weight="bold"),
            text_color=UITheme.PURPLE_800,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            content,
            text=message,
            font=UITheme.font_body(),
            text_color=UITheme.TEXT,
            justify="left",
            wraplength=340,
            anchor="w",
        ).pack(side="left", fill="both", expand=True)

        footer = ctk.CTkFrame(body, fg_color=UITheme.SURFACE_ALT, corner_radius=0)
        footer.pack(fill="x", padx=0, pady=0)

        btn_row = ctk.CTkFrame(footer, fg_color="transparent")
        btn_row.pack(fill="x", padx=UITheme.PAD, pady=UITheme.PAD)

        if self._kind == "yesno":
            no_btn = ctk.CTkButton(
                btn_row,
                text="否",
                width=100,
                command=self._on_no,
            )
            no_btn.pack(side="right", padx=(UITheme.PAD_SM, 0))
            UITheme.style_secondary(no_btn)

            yes_btn = ctk.CTkButton(
                btn_row,
                text="是",
                width=100,
                command=self._on_yes,
            )
            yes_btn.pack(side="right", padx=UITheme.PAD_SM)
            UITheme.style_primary(yes_btn)
        else:
            ok_btn = ctk.CTkButton(
                btn_row,
                text="确定",
                width=120,
                command=self._on_ok,
            )
            ok_btn.pack(side="right")
            UITheme.style_primary(ok_btn)

    def _on_yes(self) -> None:
        self.result = True
        self.grab_release()
        self.destroy()

    def _on_no(self) -> None:
        self.result = False
        self.grab_release()
        self.destroy()

    def _on_ok(self) -> None:
        self.result = True
        self.grab_release()
        self.destroy()


def ask_yes_no(parent, title: str, message: str, *, width: int = 440) -> bool:
    dialog = ThemedDialog(parent, title, message, kind="yesno", width=width)
    parent.wait_window(dialog)
    return bool(dialog.result)


def show_warning(parent, title: str, message: str) -> None:
    dialog = ThemedDialog(parent, title, message, kind="ok")
    parent.wait_window(dialog)


def show_info(parent, title: str, message: str) -> None:
    dialog = ThemedDialog(parent, title, message, kind="ok")
    parent.wait_window(dialog)


class PageRangeDialog(ctk.CTkToplevel):
    """选择批注页码范围（1-based，含起止页）"""

    def __init__(self, parent, *, total_pages: int, width: int = 420):
        super().__init__(parent)
        self.total_pages = max(1, total_pages)
        self.result: tuple[int, int] | None = None

        self.title("选择批注范围")
        self.geometry(f"{width}x1")
        self.resizable(False, False)
        self.configure(fg_color=UITheme.BG)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        apply_window_icon(self)
        self.after(50, lambda: apply_window_icon(self))

        self._build()
        self.update_idletasks()
        h = max(self.winfo_reqheight(), 240)
        self.geometry(f"{width}x{h}")
        self._center_on(parent)

        self.grab_set()
        self.focus_force()
        self.bind("<Return>", lambda _e: self._on_ok())
        self.bind("<Escape>", lambda _e: self._on_cancel())

    def _center_on(self, master) -> None:
        self.update_idletasks()
        mx = master.winfo_rootx()
        my = master.winfo_rooty()
        mw = master.winfo_width()
        mh = master.winfo_height()
        w = self.winfo_width()
        h = self.winfo_height()
        x = mx + (mw - w) // 2
        y = my + (mh - h) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def _build(self) -> None:
        body = ctk.CTkFrame(self, fg_color=UITheme.SURFACE, corner_radius=0)
        body.pack(fill="both", expand=True)

        content = ctk.CTkFrame(body, fg_color="transparent")
        content.pack(fill="x", padx=UITheme.PAD, pady=UITheme.PAD)

        ctk.CTkLabel(
            content,
            text=f"当前文档共 {self.total_pages} 页，请选择要生成 AI 批注的页码范围：",
            font=UITheme.font_body(),
            text_color=UITheme.TEXT,
            justify="left",
            wraplength=360,
        ).pack(anchor="w", pady=(0, UITheme.PAD))

        row = ctk.CTkFrame(content, fg_color="transparent")
        row.pack(fill="x", pady=UITheme.PAD_SM)

        ctk.CTkLabel(
            row,
            text="从第",
            font=UITheme.font_body(),
            text_color=UITheme.TEXT,
        ).pack(side="left")

        self.start_var = ctk.StringVar(value="1")
        start_entry = ctk.CTkEntry(row, width=72, textvariable=self.start_var, justify="center")
        start_entry.pack(side="left", padx=8)

        ctk.CTkLabel(
            row,
            text="页  到第",
            font=UITheme.font_body(),
            text_color=UITheme.TEXT,
        ).pack(side="left")

        self.end_var = ctk.StringVar(value=str(self.total_pages))
        end_entry = ctk.CTkEntry(row, width=72, textvariable=self.end_var, justify="center")
        end_entry.pack(side="left", padx=8)

        ctk.CTkLabel(
            row,
            text="页",
            font=UITheme.font_body(),
            text_color=UITheme.TEXT,
        ).pack(side="left")

        self.hint = ctk.CTkLabel(
            content,
            text="",
            font=UITheme.font_caption(),
            text_color=UITheme.DANGER,
        )
        self.hint.pack(anchor="w", pady=(4, 0))

        footer = ctk.CTkFrame(body, fg_color=UITheme.SURFACE_ALT, corner_radius=0)
        footer.pack(fill="x")

        btn_row = ctk.CTkFrame(footer, fg_color="transparent")
        btn_row.pack(fill="x", padx=UITheme.PAD, pady=UITheme.PAD)

        cancel_btn = ctk.CTkButton(btn_row, text="取消", width=100, command=self._on_cancel)
        cancel_btn.pack(side="right", padx=(UITheme.PAD_SM, 0))
        UITheme.style_secondary(cancel_btn)

        ok_btn = ctk.CTkButton(btn_row, text="下一步", width=100, command=self._on_ok)
        ok_btn.pack(side="right", padx=UITheme.PAD_SM)
        UITheme.style_primary(ok_btn)

    def _parse_range(self) -> tuple[int, int] | None:
        try:
            start = int(self.start_var.get().strip())
            end = int(self.end_var.get().strip())
        except ValueError:
            self.hint.configure(text="请输入有效的页码数字")
            return None
        if start < 1 or end < 1:
            self.hint.configure(text="页码不能小于 1")
            return None
        if start > self.total_pages or end > self.total_pages:
            self.hint.configure(text=f"页码不能超过 {self.total_pages}")
            return None
        if start > end:
            self.hint.configure(text="起始页不能大于结束页")
            return None
        self.hint.configure(text="")
        return start, end

    def _on_ok(self) -> None:
        parsed = self._parse_range()
        if parsed is None:
            return
        self.result = parsed
        self.grab_release()
        self.destroy()

    def _on_cancel(self) -> None:
        self.result = None
        self.grab_release()
        self.destroy()


def ask_page_range(parent, total_pages: int) -> tuple[int, int] | None:
    """返回 1-based (start, end)，取消则 None"""
    dialog = PageRangeDialog(parent, total_pages=total_pages)
    parent.wait_window(dialog)
    return dialog.result
