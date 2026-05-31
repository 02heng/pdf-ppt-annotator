import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Optional


class Toolbar(ctk.CTkFrame):
    """工具栏"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.app = master  # 保存主应用引用
        self._create_widgets()

    def _create_widgets(self) -> None:
        """创建工具栏按钮"""
        # 导入按钮
        self.import_btn = ctk.CTkButton(
            self,
            text="导入文件",
            command=self._on_import
        )
        self.import_btn.pack(side="left", padx=5)

        # 开始批注按钮
        self.annotate_btn = ctk.CTkButton(
            self,
            text="开始批注",
            command=self._on_annotate,
            fg_color="#2ecc71",
            hover_color="#27ae60"
        )
        self.annotate_btn.pack(side="left", padx=5)

        # 导出按钮
        self.export_btn = ctk.CTkButton(
            self,
            text="导出",
            command=self._on_export
        )
        self.export_btn.pack(side="left", padx=5)

        # 批注模式切换
        self.mode_var = ctk.StringVar(value="sidebar")
        self.mode_switch = ctk.CTkSegmentedButton(
            self,
            values=["覆盖", "侧边栏"],
            variable=self.mode_var,
            command=self._on_mode_change
        )
        self.mode_switch.pack(side="left", padx=5)

        # LLM 切换
        self.llm_var = ctk.StringVar(value="openai")
        self.llm_switch = ctk.CTkSegmentedButton(
            self,
            values=["OpenAI", "Ollama"],
            variable=self.llm_var,
            command=self._on_llm_change
        )
        self.llm_switch.pack(side="left", padx=5)

        # 设置按钮
        self.settings_btn = ctk.CTkButton(
            self,
            text="设置",
            command=self._on_settings
        )
        self.settings_btn.pack(side="right", padx=5)

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
            # 存储选中的文件
            self.app.selected_files = list(files)

            # 更新文件列表显示
            self.app.update_file_list(list(files))

            # 更新状态栏
            file_names = [f.split("/")[-1].split("\\")[-1] for f in files]
            self.app.update_status(f"已导入 {len(files)} 个文件: {', '.join(file_names)}")

    def _on_annotate(self) -> None:
        """开始批注"""
        if not hasattr(self.app, 'selected_files') or not self.app.selected_files:
            messagebox.showwarning("警告", "请先导入文件")
            return

        # 检查LLM配置
        if self.app.settings.llm.provider == "openai" and not self.app.settings.llm.openai.api_key:
            messagebox.showwarning("警告", "请先在设置中配置 OpenAI API Key")
            return

        messagebox.showinfo("开始批注", "批注功能即将启动，正在处理文件...")

        # 这里可以启动批注处理服务
        # TODO: 集成批注处理服务

    def _on_export(self) -> None:
        """导出文件"""
        if not hasattr(self.app, 'selected_files') or not self.app.selected_files:
            messagebox.showwarning("警告", "没有可导出的文件，请先导入并批注文件")
            return

        # 选择导出目录
        export_dir = filedialog.askdirectory(title="选择导出目录")

        if export_dir:
            messagebox.showinfo("导出", f"文件将导出到: {export_dir}")
            # TODO: 集成导出服务

    def _on_mode_change(self, value: str) -> None:
        """切换批注模式"""
        mode = "overlay" if value == "覆盖" else "sidebar"
        self.app.settings.annotation.mode = mode
        self.app.update_status(f"批注模式已切换为: {value}")

    def _on_llm_change(self, value: str) -> None:
        """切换 LLM"""
        provider = "openai" if value == "OpenAI" else "ollama"
        self.app.settings.llm.provider = provider
        self.app.update_status(f"LLM 已切换为: {value}")

    def _on_settings(self) -> None:
        """打开设置"""
        from src.ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.app, self.app.settings)
        self.app.wait_window(dialog)

        if dialog.result:
            self.app.settings = dialog.result
            self.app.update_status("设置已保存")
            messagebox.showinfo("成功", "设置已保存")
