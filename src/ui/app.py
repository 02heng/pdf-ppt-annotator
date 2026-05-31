import customtkinter as ctk
from tkinter import messagebox
from typing import List

from src.models.config import Settings
from src.ui.toolbar import Toolbar
from src.ui.status_bar import StatusBar


class App(ctk.CTk):
    """主应用窗口"""

    def __init__(self, settings: Settings):
        super().__init__()

        self.settings = settings
        self.selected_files: List[str] = []

        # 配置窗口
        self.title("PDF/PPT 中文批注工具")
        self.geometry("1200x800")

        # 设置主题
        ctk.set_appearance_mode(settings.app.theme)
        ctk.set_default_color_theme("blue")

        # 创建 UI 组件
        self._create_widgets()

        # 配置布局
        self._configure_layout()

    def _create_widgets(self) -> None:
        """创建 UI 组件"""
        # 工具栏
        self.toolbar = Toolbar(self)

        # 主内容区域
        self.content_frame = ctk.CTkFrame(self)

        # 左侧文件列表
        self.file_list_frame = ctk.CTkFrame(self.content_frame, width=250)
        self._create_file_list()

        # 文档预览区域
        self.preview_frame = ctk.CTkFrame(self.content_frame)

        # 批注侧边栏
        self.sidebar_frame = ctk.CTkFrame(self.content_frame, width=300)
        self._create_sidebar()

        # 状态栏
        self.status_bar = StatusBar(self)

    def _create_file_list(self) -> None:
        """创建文件列表"""
        # 标题
        title_label = ctk.CTkLabel(
            self.file_list_frame,
            text="已导入文件",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=10)

        # 文件列表
        self.file_listbox = ctk.CTkScrollableFrame(self.file_list_frame)
        self.file_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # 提示标签
        self.file_hint = ctk.CTkLabel(
            self.file_list_frame,
            text="点击「导入文件」添加文档",
            text_color="gray"
        )
        self.file_hint.pack(pady=10)

    def _create_sidebar(self) -> None:
        """创建批注侧边栏"""
        # 标题
        title_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="中文批注",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=10)

        # 批注内容
        self.annotation_text = ctk.CTkTextbox(self.sidebar_frame)
        self.annotation_text.pack(fill="both", expand=True, padx=5, pady=5)

        # 提示
        self.annotation_hint = ctk.CTkLabel(
            self.sidebar_frame,
            text="导入文件并开始批注后\n中文注释将显示在此处",
            text_color="gray"
        )
        self.annotation_hint.pack(pady=10)

    def _configure_layout(self) -> None:
        """配置布局"""
        self.toolbar.pack(fill="x", padx=5, pady=5)
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.file_list_frame.pack(side="left", fill="y")
        self.preview_frame.pack(side="left", fill="both", expand=True)
        self.sidebar_frame.pack(side="right", fill="y")
        self.status_bar.pack(fill="x", padx=5, pady=5)

    def update_status(self, message: str) -> None:
        """更新状态栏消息"""
        self.status_bar.set_message(message)

    def update_progress(self, current: int, total: int, status: str) -> None:
        """更新进度"""
        self.status_bar.set_progress(current, total, status)

    def update_file_list(self, files: List[str]) -> None:
        """更新文件列表显示"""
        # 清空现有列表
        for widget in self.file_listbox.winfo_children():
            widget.destroy()

        if not files:
            self.file_hint.configure(text="点击「导入文件」添加文档")
            return

        self.file_hint.configure(text="")

        for file_path in files:
            frame = ctk.CTkFrame(self.file_listbox)
            frame.pack(fill="x", pady=2)

            # 文件图标和名称
            file_name = file_path.split("/")[-1].split("\\")[-1]
            icon = "📄" if file_name.endswith(".pdf") else "📊"

            label = ctk.CTkLabel(
                frame,
                text=f"{icon} {file_name}",
                anchor="w"
            )
            label.pack(side="left", fill="x", expand=True, padx=5)
