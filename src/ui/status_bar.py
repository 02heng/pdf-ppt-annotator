import customtkinter as ctk


class StatusBar(ctk.CTkFrame):
    """状态栏"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._create_widgets()

    def _create_widgets(self) -> None:
        """创建状态栏组件"""
        # 状态消息
        self.message_label = ctk.CTkLabel(
            self,
            text="就绪",
            anchor="w"
        )
        self.message_label.pack(side="left", fill="x", expand=True, padx=5)

        # 进度条
        self.progress_bar = ctk.CTkProgressBar(self, width=200)
        self.progress_bar.pack(side="right", padx=5)
        self.progress_bar.set(0)

        # 进度文本
        self.progress_label = ctk.CTkLabel(
            self,
            text="",
            anchor="e"
        )
        self.progress_label.pack(side="right", padx=5)

    def set_message(self, message: str) -> None:
        """设置状态消息"""
        self.message_label.configure(text=message)

    def set_progress(self, current: int, total: int, status: str) -> None:
        """设置进度"""
        if total > 0:
            progress = current / total
            self.progress_bar.set(progress)
            self.progress_label.configure(text=f"{current}/{total}")
        self.message_label.configure(text=status)
