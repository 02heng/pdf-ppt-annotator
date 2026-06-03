import customtkinter as ctk

from src.ui.theme import UITheme


class StatusBar(ctk.CTkFrame):
    """状态栏：进度 + 生成提示"""

    HEIGHT = 44

    def __init__(self, master, **kwargs):
        super().__init__(master, height=self.HEIGHT, **kwargs)
        self.pack_propagate(False)
        UITheme.style_status_bar(self)
        self._create_widgets()

    def _create_widgets(self) -> None:
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=UITheme.PAD_SM, pady=6)

        self.message_label = ctk.CTkLabel(
            inner,
            text="就绪",
            anchor="w",
            font=UITheme.font_body(),
            text_color=UITheme.TEXT,
        )
        self.message_label.pack(side="left", fill="x", expand=True, padx=(4, 12))

        self.progress_label = ctk.CTkLabel(
            inner,
            text="",
            anchor="e",
            font=UITheme.font_caption(),
            text_color=UITheme.PURPLE_800,
            width=56,
        )
        self.progress_label.pack(side="right", padx=(0, 8))

        self.progress_bar = ctk.CTkProgressBar(
            inner,
            width=220,
            height=10,
            progress_color=UITheme.PURPLE_700,
            fg_color=UITheme.PURPLE_100,
        )
        self.progress_bar.pack(side="right", padx=4)
        self.progress_bar.set(0)

    def set_message(self, message: str) -> None:
        self.message_label.configure(text=message)

    def set_progress(self, current: int, total: int, status: str) -> None:
        if total > 0:
            self.progress_bar.set(min(max(current / total, 0.0), 1.0))
            self.progress_label.configure(text=f"{current}/{total}")
        else:
            self.progress_bar.set(0)
            self.progress_label.configure(text="")
        self.message_label.configure(text=status)
