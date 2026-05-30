import customtkinter as ctk
from tkinter import filedialog
from typing import List, Callable
from src.utils.file_utils import is_supported_file


class FilePanel(ctk.CTkFrame):
    """文件导入面板"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.files: List[str] = []
        self.on_files_selected: Callable = None
        self._create_widgets()

    def _create_widgets(self) -> None:
        """创建文件面板组件"""
        self.title_label = ctk.CTkLabel(
            self,
            text="文件导入",
            font=("Arial", 14, "bold")
        )
        self.title_label.pack(pady=10)

        self.import_btn = ctk.CTkButton(
            self,
            text="选择文件",
            command=self._on_import
        )
        self.import_btn.pack(pady=5)

        self.file_list = ctk.CTkScrollableFrame(self)
        self.file_list.pack(fill="both", expand=True, padx=10, pady=5)

        self.process_btn = ctk.CTkButton(
            self,
            text="开始处理",
            command=self._on_process,
            state="disabled"
        )
        self.process_btn.pack(pady=10)

    def _on_import(self) -> None:
        """导入文件"""
        filetypes = [
            ("PDF 文件", "*.pdf"),
            ("PPT 文件", "*.ppt *.pptx"),
            ("所有支持的文件", "*.pdf *.ppt *.pptx")
        ]

        files = filedialog.askopenfilenames(
            title="选择文件",
            filetypes=filetypes
        )

        if files:
            self.files = list(files)
            self._update_file_list()

            if self.on_files_selected:
                self.on_files_selected(self.files)

    def _update_file_list(self) -> None:
        """更新文件列表显示"""
        for widget in self.file_list.winfo_children():
            widget.destroy()

        for file_path in self.files:
            frame = ctk.CTkFrame(self.file_list)
            frame.pack(fill="x", pady=2)

            label = ctk.CTkLabel(
                frame,
                text=file_path.split("/")[-1],
                anchor="w"
            )
            label.pack(side="left", fill="x", expand=True, padx=5)

            remove_btn = ctk.CTkButton(
                frame,
                text="移除",
                width=60,
                command=lambda p=file_path: self._remove_file(p)
            )
            remove_btn.pack(side="right", padx=5)

        if self.files:
            self.process_btn.configure(state="normal")
        else:
            self.process_btn.configure(state="disabled")

    def _remove_file(self, file_path: str) -> None:
        """移除文件"""
        if file_path in self.files:
            self.files.remove(file_path)
            self._update_file_list()

    def _on_process(self) -> None:
        """开始处理"""
        pass

    def get_selected_files(self) -> List[str]:
        """获取选中的文件"""
        return self.files.copy()
