import customtkinter as ctk
from typing import Optional
from src.models.config import Settings

class SettingsDialog(ctk.CTkToplevel):
    """设置对话框"""
    
    def __init__(self, master, settings: Settings, **kwargs):
        super().__init__(master, **kwargs)
        
        self.settings = settings
        self.result: Optional[Settings] = None
        
        # 配置窗口
        self.title("设置")
        self.geometry("500x600")
        self.resizable(False, False)
        
        # 模态对话框
        self.transient(master)
        self.grab_set()
        
        self._create_widgets()
    
    def _create_widgets(self) -> None:
        """创建设置组件"""
        # 选项卡
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # LLM 设置选项卡
        self.llm_tab = self.tabview.add("LLM 设置")
        self._create_llm_settings()
        
        # 批注设置选项卡
        self.annotation_tab = self.tabview.add("批注设置")
        self._create_annotation_settings()
        
        # 应用设置选项卡
        self.app_tab = self.tabview.add("应用设置")
        self._create_app_settings()
        
        # 按钮
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(fill="x", padx=10, pady=10)
        
        self.save_btn = ctk.CTkButton(
            self.button_frame,
            text="保存",
            command=self._on_save
        )
        self.save_btn.pack(side="right", padx=5)
        
        self.cancel_btn = ctk.CTkButton(
            self.button_frame,
            text="取消",
            command=self._on_cancel
        )
        self.cancel_btn.pack(side="right", padx=5)
    
    def _create_llm_settings(self) -> None:
        """创建 LLM 设置"""
        # 提供商选择
        ctk.CTkLabel(self.llm_tab, text="LLM 提供商:").pack(anchor="w", padx=10, pady=5)
        
        self.provider_var = ctk.StringVar(value=self.settings.llm.provider)
        self.provider_segment = ctk.CTkSegmentedButton(
            self.llm_tab,
            values=["openai", "ollama"],
            variable=self.provider_var
        )
        self.provider_segment.pack(fill="x", padx=10, pady=5)
        
        # OpenAI 设置
        self.openai_frame = ctk.CTkFrame(self.llm_tab)
        self.openai_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.openai_frame, text="API Key:").pack(anchor="w", padx=5, pady=2)
        self.api_key_entry = ctk.CTkEntry(self.openai_frame, show="*")
        self.api_key_entry.pack(fill="x", padx=5, pady=2)
        self.api_key_entry.insert(0, self.settings.llm.openai.api_key)
        
        ctk.CTkLabel(self.openai_frame, text="模型:").pack(anchor="w", padx=5, pady=2)
        self.model_entry = ctk.CTkEntry(self.openai_frame)
        self.model_entry.pack(fill="x", padx=5, pady=2)
        self.model_entry.insert(0, self.settings.llm.openai.model)
        
        # Ollama 设置
        self.ollama_frame = ctk.CTkFrame(self.llm_tab)
        self.ollama_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.ollama_frame, text="Base URL:").pack(anchor="w", padx=5, pady=2)
        self.base_url_entry = ctk.CTkEntry(self.ollama_frame)
        self.base_url_entry.pack(fill="x", padx=5, pady=2)
        self.base_url_entry.insert(0, self.settings.llm.ollama.base_url)
        
        ctk.CTkLabel(self.ollama_frame, text="模型:").pack(anchor="w", padx=5, pady=2)
        self.ollama_model_entry = ctk.CTkEntry(self.ollama_frame)
        self.ollama_model_entry.pack(fill="x", padx=5, pady=2)
        self.ollama_model_entry.insert(0, self.settings.llm.ollama.model)
    
    def _create_annotation_settings(self) -> None:
        """创建批注设置"""
        ctk.CTkLabel(self.annotation_tab, text="批注模式:").pack(anchor="w", padx=10, pady=5)
        
        self.mode_var = ctk.StringVar(value=self.settings.annotation.mode)
        self.mode_segment = ctk.CTkSegmentedButton(
            self.annotation_tab,
            values=["overlay", "sidebar"],
            variable=self.mode_var
        )
        self.mode_segment.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.annotation_tab, text="详细程度:").pack(anchor="w", padx=10, pady=5)
        
        self.detail_var = ctk.StringVar(value=self.settings.annotation.detail_level)
        self.detail_segment = ctk.CTkSegmentedButton(
            self.annotation_tab,
            values=["summary", "detailed", "custom"],
            variable=self.detail_var
        )
        self.detail_segment.pack(fill="x", padx=10, pady=5)
        
        self.font_frame = ctk.CTkFrame(self.annotation_tab)
        self.font_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.font_frame, text="字体大小:").pack(anchor="w", padx=5, pady=2)
        self.font_size_entry = ctk.CTkEntry(self.font_frame)
        self.font_size_entry.pack(fill="x", padx=5, pady=2)
        self.font_size_entry.insert(0, str(self.settings.annotation.style.font_size))
    
    def _create_app_settings(self) -> None:
        """创建应用设置"""
        ctk.CTkLabel(self.app_tab, text="主题:").pack(anchor="w", padx=10, pady=5)
        
        self.theme_var = ctk.StringVar(value=self.settings.app.theme)
        self.theme_segment = ctk.CTkSegmentedButton(
            self.app_tab,
            values=["light", "dark", "system"],
            variable=self.theme_var
        )
        self.theme_segment.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.app_tab, text="语言:").pack(anchor="w", padx=10, pady=5)
        
        self.language_var = ctk.StringVar(value=self.settings.app.language)
        self.language_segment = ctk.CTkSegmentedButton(
            self.app_tab,
            values=["zh-CN", "en-US"],
            variable=self.language_var
        )
        self.language_segment.pack(fill="x", padx=10, pady=5)
    
    def _on_save(self) -> None:
        """保存设置"""
        self.settings.llm.provider = self.provider_var.get()
        self.settings.llm.openai.api_key = self.api_key_entry.get()
        self.settings.llm.openai.model = self.model_entry.get()
        self.settings.llm.ollama.base_url = self.base_url_entry.get()
        self.settings.llm.ollama.model = self.ollama_model_entry.get()
        self.settings.annotation.mode = self.mode_var.get()
        self.settings.annotation.detail_level = self.detail_var.get()
        self.settings.app.theme = self.theme_var.get()
        self.settings.app.language = self.language_var.get()
        
        self.result = self.settings
        self.destroy()
    
    def _on_cancel(self) -> None:
        """取消"""
        self.destroy()
