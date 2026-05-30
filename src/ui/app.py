import customtkinter as ctk

from src.models.config import Settings
from src.ui.toolbar import Toolbar
from src.ui.status_bar import StatusBar


class App(ctk.CTk):
    """主应用窗口"""

    def __init__(self, settings: Settings):
        super().__init__()

        self.settings = settings

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

        # 文档预览区域
        self.preview_frame = ctk.CTkFrame(self.content_frame)

        # 批注侧边栏
        self.sidebar_frame = ctk.CTkFrame(self.content_frame, width=300)

        # 状态栏
        self.status_bar = StatusBar(self)

    def _configure_layout(self) -> None:
        """配置布局"""
        self.toolbar.pack(fill="x", padx=5, pady=5)
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.preview_frame.pack(side="left", fill="both", expand=True)
        self.sidebar_frame.pack(side="right", fill="y")
        self.status_bar.pack(fill="x", padx=5, pady=5)

    def update_status(self, message: str) -> None:
        """更新状态栏消息"""
        self.status_bar.set_message(message)

    def update_progress(self, current: int, total: int, status: str) -> None:
        """更新进度"""
        self.status_bar.set_progress(current, total, status)
