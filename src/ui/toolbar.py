import customtkinter as ctk


class Toolbar(ctk.CTkFrame):
    """工具栏"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
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
        pass

    def _on_export(self) -> None:
        """导出文件"""
        pass

    def _on_mode_change(self, value: str) -> None:
        """切换批注模式"""
        pass

    def _on_llm_change(self, value: str) -> None:
        """切换 LLM"""
        pass

    def _on_settings(self) -> None:
        """打开设置"""
        pass
