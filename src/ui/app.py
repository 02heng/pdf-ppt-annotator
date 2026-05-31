import customtkinter as ctk
from tkinter import messagebox
from typing import List, Optional

from src.models.config import Settings
from src.ui.toolbar import Toolbar
from src.ui.status_bar import StatusBar


class App(ctk.CTk):
    """主应用窗口"""

    def __init__(self, settings: Settings):
        super().__init__()

        self.settings = settings
        self.selected_files: List[str] = []
        self.current_file_index: int = -1

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
        self._create_preview()

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

    def _create_preview(self) -> None:
        """创建文档预览区域"""
        # 页面导航
        self.nav_frame = ctk.CTkFrame(self.preview_frame)
        self.nav_frame.pack(fill="x", padx=5, pady=5)

        self.prev_btn = ctk.CTkButton(
            self.nav_frame,
            text="上一页",
            command=self._prev_page,
            width=80
        )
        self.prev_btn.pack(side="left", padx=5)

        self.page_label = ctk.CTkLabel(
            self.nav_frame,
            text="0 / 0"
        )
        self.page_label.pack(side="left", expand=True)

        self.next_btn = ctk.CTkButton(
            self.nav_frame,
            text="下一页",
            command=self._next_page,
            width=80
        )
        self.next_btn.pack(side="right", padx=5)

        # 文件信息
        self.file_info_label = ctk.CTkLabel(
            self.preview_frame,
            text="请选择一个文件进行预览",
            font=("Arial", 12)
        )
        self.file_info_label.pack(pady=5)

        # 内容显示区域
        self.content_text = ctk.CTkTextbox(self.preview_frame)
        self.content_text.pack(fill="both", expand=True, padx=5, pady=5)

        # 当前页面索引
        self.current_page = 0
        self.total_pages = 0

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

        for idx, file_path in enumerate(files):
            frame = ctk.CTkFrame(self.file_listbox)
            frame.pack(fill="x", pady=2)

            # 文件图标和名称
            file_name = file_path.split("/")[-1].split("\\")[-1]
            icon = "📄" if file_name.endswith(".pdf") else "📊"

            # 可点击的文件按钮
            file_btn = ctk.CTkButton(
                frame,
                text=f"{icon} {file_name}",
                anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda i=idx: self._on_file_select(i)
            )
            file_btn.pack(side="left", fill="x", expand=True, padx=5)

            # 移除按钮
            remove_btn = ctk.CTkButton(
                frame,
                text="×",
                width=30,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda i=idx: self._remove_file(i)
            )
            remove_btn.pack(side="right", padx=2)

        # 默认选中第一个文件
        if files:
            self._on_file_select(0)

    def _on_file_select(self, index: int) -> None:
        """选择文件"""
        if 0 <= index < len(self.selected_files):
            self.current_file_index = index
            file_path = self.selected_files[index]
            file_name = file_path.split("/")[-1].split("\\")[-1]

            # 更新文件信息
            self.file_info_label.configure(text=f"当前文件: {file_name}")

            # 尝试读取文件内容
            self._load_file_content(file_path)

            # 更新状态栏
            self.update_status(f"已选择: {file_name}")

    def _load_file_content(self, file_path: str) -> None:
        """加载文件内容"""
        self.content_text.delete("1.0", "end")

        try:
            if file_path.lower().endswith('.pdf'):
                self._load_pdf(file_path)
            elif file_path.lower().endswith(('.ppt', '.pptx')):
                self._load_ppt(file_path)
            else:
                self.content_text.insert("1.0", "不支持的文件格式")
        except Exception as e:
            self.content_text.insert("1.0", f"加载文件时出错: {str(e)}")

    def _load_pdf(self, file_path: str) -> None:
        """加载PDF文件"""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            self.total_pages = len(doc)
            self.current_page = 0

            if self.total_pages > 0:
                page = doc[self.current_page]
                text = page.get_text()
                self.content_text.insert("1.0", text)
                self.page_label.configure(text=f"{self.current_page + 1} / {self.total_pages}")
            else:
                self.content_text.insert("1.0", "PDF文件为空")

            doc.close()
        except ImportError:
            self.content_text.insert("1.0", "请安装PyMuPDF: pip install pymupdf")
        except Exception as e:
            self.content_text.insert("1.0", f"读取PDF出错: {str(e)}")

    def _load_ppt(self, file_path: str) -> None:
        """加载PPT文件"""
        try:
            from pptx import Presentation
            prs = Presentation(file_path)
            self.total_pages = len(prs.slides)
            self.current_page = 0

            if self.total_pages > 0:
                slide = prs.slides[self.current_page]
                text_content = []
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text_content.append(shape.text)
                self.content_text.insert("1.0", "\n".join(text_content))
                self.page_label.configure(text=f"{self.current_page + 1} / {self.total_pages}")
            else:
                self.content_text.insert("1.0", "PPT文件为空")
        except ImportError:
            self.content_text.insert("1.0", "请安装python-pptx: pip install python-pptx")
        except Exception as e:
            self.content_text.insert("1.0", f"读取PPT出错: {str(e)}")

    def _prev_page(self) -> None:
        """上一页"""
        if self.current_file_index < 0 or not self.selected_files:
            return

        if self.current_page > 0:
            self.current_page -= 1
            self._reload_current_page()

    def _next_page(self) -> None:
        """下一页"""
        if self.current_file_index < 0 or not self.selected_files:
            return

        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self._reload_current_page()

    def _reload_current_page(self) -> None:
        """重新加载当前页面"""
        if self.current_file_index < 0 or not self.selected_files:
            return

        file_path = self.selected_files[self.current_file_index]
        self.content_text.delete("1.0", "end")

        try:
            if file_path.lower().endswith('.pdf'):
                import fitz
                doc = fitz.open(file_path)
                page = doc[self.current_page]
                text = page.get_text()
                self.content_text.insert("1.0", text)
                doc.close()
            elif file_path.lower().endswith(('.ppt', '.pptx')):
                from pptx import Presentation
                prs = Presentation(file_path)
                slide = prs.slides[self.current_page]
                text_content = []
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text_content.append(shape.text)
                self.content_text.insert("1.0", "\n".join(text_content))

            self.page_label.configure(text=f"{self.current_page + 1} / {self.total_pages}")
        except Exception as e:
            self.content_text.insert("1.0", f"加载页面出错: {str(e)}")

    def _remove_file(self, index: int) -> None:
        """移除文件"""
        if 0 <= index < len(self.selected_files):
            removed = self.selected_files.pop(index)

            # 如果移除的是当前选中的文件
            if index == self.current_file_index:
                if self.selected_files:
                    self._on_file_select(0)
                else:
                    self.current_file_index = -1
                    self.file_info_label.configure(text="请选择一个文件进行预览")
                    self.content_text.delete("1.0", "end")
                    self.page_label.configure(text="0 / 0")
            elif index < self.current_file_index:
                self.current_file_index -= 1

            # 更新文件列表显示
            self.update_file_list(self.selected_files)

            file_name = removed.split("/")[-1].split("\\")[-1]
            self.update_status(f"已移除: {file_name}")
