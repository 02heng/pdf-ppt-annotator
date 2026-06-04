import customtkinter as ctk
from typing import Optional
from src.models.config import Settings
from src.ui.theme import UITheme


class SettingsDialog(ctk.CTkToplevel):
    """设置对话框"""
    
    def __init__(self, master, settings: Settings, **kwargs):
        super().__init__(master, **kwargs)
        
        self.settings = settings
        self.result: Optional[Settings] = None
        
        # 配置窗口
        self.title("系统 API 设置")
        self.geometry("520x680")
        self.resizable(False, False)
        
        # 模态对话框
        self.transient(master)
        self.grab_set()

        UITheme.apply_root(self)
        from src.utils.branding import apply_window_icon

        apply_window_icon(self)
        self.after(50, lambda: apply_window_icon(self))
        self._create_widgets()
        self._apply_theme()
    
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

    def _apply_theme(self) -> None:
        UITheme.style_tabview(self.tabview)
        UITheme.style_card(self.button_frame, elevated=False)
        UITheme.style_primary(self.save_btn)
        UITheme.style_secondary(self.cancel_btn)
        for seg in (
            getattr(self, "provider_segment", None),
            getattr(self, "xiaomi_mode_segment", None),
            getattr(self, "mode_segment", None),
            getattr(self, "detail_segment", None),
            getattr(self, "theme_segment", None),
            getattr(self, "language_segment", None),
        ):
            if seg is not None:
                UITheme.style_segmented_panel(seg)
        for frame in (
            getattr(self, "openai_frame", None),
            getattr(self, "ollama_frame", None),
            getattr(self, "deepseek_frame", None),
            getattr(self, "xiaomi_frame", None),
            getattr(self, "agnes_frame", None),
            getattr(self, "font_frame", None),
        ):
            if frame is not None:
                UITheme.style_card(frame, elevated=False)
    
    def _create_llm_settings(self) -> None:
        """创建 LLM 设置"""
        # 提供商选择
        ctk.CTkLabel(self.llm_tab, text="LLM 提供商:").pack(anchor="w", padx=10, pady=5)
        
        self._provider_value_map = {
            "OpenAI": "openai",
            "Ollama": "ollama",
            "DeepSeek": "deepseek",
            "小米 MiMo": "xiaomi",
            "Agnes": "agnes",
        }
        self._provider_label_map = {v: k for k, v in self._provider_value_map.items()}
        initial_label = self._provider_label_map.get(
            self.settings.llm.provider, "DeepSeek"
        )
        self.provider_var = ctk.StringVar(value=initial_label)
        self.provider_segment = ctk.CTkSegmentedButton(
            self.llm_tab,
            values=["OpenAI", "Ollama", "DeepSeek", "小米 MiMo", "Agnes"],
            variable=self.provider_var,
            command=self._on_provider_change,
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
        
        # DeepSeek 设置
        self.deepseek_frame = ctk.CTkFrame(self.llm_tab)
        self.deepseek_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.deepseek_frame, text="API Key:").pack(anchor="w", padx=5, pady=2)
        self.deepseek_api_key_entry = ctk.CTkEntry(self.deepseek_frame, show="*")
        self.deepseek_api_key_entry.pack(fill="x", padx=5, pady=2)
        self.deepseek_api_key_entry.insert(0, self.settings.llm.deepseek.api_key)
        
        ctk.CTkLabel(self.deepseek_frame, text="模型:").pack(anchor="w", padx=5, pady=2)
        self.deepseek_model_entry = ctk.CTkEntry(self.deepseek_frame)
        self.deepseek_model_entry.pack(fill="x", padx=5, pady=2)
        self.deepseek_model_entry.insert(0, self.settings.llm.deepseek.model)
        
        ctk.CTkLabel(self.deepseek_frame, text="Base URL:").pack(anchor="w", padx=5, pady=2)
        self.deepseek_base_url_entry = ctk.CTkEntry(self.deepseek_frame)
        self.deepseek_base_url_entry.pack(fill="x", padx=5, pady=2)
        self.deepseek_base_url_entry.insert(0, self.settings.llm.deepseek.base_url)

        from src.models.config import xiaomi_default_base_url

        self.xiaomi_frame = ctk.CTkFrame(self.llm_tab)
        self.xiaomi_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.xiaomi_frame, text="计费方式:").pack(anchor="w", padx=5, pady=2)
        mode_map = {"Token Plan 订阅": "token_plan", "按量付费 API": "payg"}
        self._xiaomi_mode_map = mode_map
        self._xiaomi_mode_label = {
            v: k for k, v in mode_map.items()
        }
        initial_mode = getattr(self.settings.llm.xiaomi, "api_mode", "token_plan") or "token_plan"
        self.xiaomi_mode_var = ctk.StringVar(
            value=self._xiaomi_mode_label.get(initial_mode, "Token Plan 订阅")
        )
        self.xiaomi_mode_segment = ctk.CTkSegmentedButton(
            self.xiaomi_frame,
            values=list(mode_map.keys()),
            variable=self.xiaomi_mode_var,
            command=self._on_xiaomi_mode_change,
        )
        self.xiaomi_mode_segment.pack(fill="x", padx=5, pady=4)

        ctk.CTkLabel(
            self.xiaomi_frame,
            text="Token Plan：在「订阅管理」复制 tp- 开头的 Key 与 Base URL\n"
            "https://platform.xiaomimimo.com/console/plan-manage",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=420,
            justify="left",
        ).pack(anchor="w", padx=5, pady=(0, 4))

        ctk.CTkLabel(self.xiaomi_frame, text="API Key:").pack(anchor="w", padx=5, pady=2)
        self.xiaomi_api_key_entry = ctk.CTkEntry(self.xiaomi_frame, show="*")
        self.xiaomi_api_key_entry.pack(fill="x", padx=5, pady=2)
        self.xiaomi_api_key_entry.insert(0, self.settings.llm.xiaomi.api_key)

        ctk.CTkLabel(self.xiaomi_frame, text="模型:").pack(anchor="w", padx=5, pady=2)
        self.xiaomi_model_entry = ctk.CTkEntry(self.xiaomi_frame)
        self.xiaomi_model_entry.pack(fill="x", padx=5, pady=2)
        self.xiaomi_model_entry.insert(0, self.settings.llm.xiaomi.model)

        ctk.CTkLabel(self.xiaomi_frame, text="Base URL（OpenAI 兼容 /v1）:").pack(
            anchor="w", padx=5, pady=2
        )
        self.xiaomi_base_url_entry = ctk.CTkEntry(self.xiaomi_frame)
        self.xiaomi_base_url_entry.pack(fill="x", padx=5, pady=2)
        saved_url = (self.settings.llm.xiaomi.base_url or "").strip()
        if not saved_url:
            saved_url = xiaomi_default_base_url(initial_mode)
        self.xiaomi_base_url_entry.insert(0, saved_url)

        ctk.CTkLabel(
            self.xiaomi_frame,
            text=(
                "请填 mimo-v2.5（全模态）。原位翻译会识整页图，在图表/正文旁各贴一行中文。"
                "若填 mimo-v2.5-pro，本应用仍会按 mimo-v2.5 调用 API。"
                "订阅 Base URL：token-plan-cn.xiaomimimo.com/v1"
            ),
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=420,
        ).pack(anchor="w", padx=5, pady=(0, 6))

        self.agnes_frame = ctk.CTkFrame(self.llm_tab)
        self.agnes_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            self.agnes_frame,
            text="在 Agnes 控制台获取 API Key：\nhttps://www.agnes-ai.com",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=420,
            justify="left",
        ).pack(anchor="w", padx=5, pady=(0, 4))

        ctk.CTkLabel(self.agnes_frame, text="API Key:").pack(anchor="w", padx=5, pady=2)
        self.agnes_api_key_entry = ctk.CTkEntry(self.agnes_frame, show="*")
        self.agnes_api_key_entry.pack(fill="x", padx=5, pady=2)
        self.agnes_api_key_entry.insert(0, self.settings.llm.agnes.api_key)

        ctk.CTkLabel(self.agnes_frame, text="模型:").pack(anchor="w", padx=5, pady=2)
        self.agnes_model_entry = ctk.CTkEntry(self.agnes_frame)
        self.agnes_model_entry.pack(fill="x", padx=5, pady=2)
        self.agnes_model_entry.insert(0, self.settings.llm.agnes.model)

        ctk.CTkLabel(self.agnes_frame, text="Base URL（OpenAI 兼容 /v1）:").pack(
            anchor="w", padx=5, pady=2
        )
        self.agnes_base_url_entry = ctk.CTkEntry(self.agnes_frame)
        self.agnes_base_url_entry.pack(fill="x", padx=5, pady=2)
        self.agnes_base_url_entry.insert(
            0,
            (self.settings.llm.agnes.base_url or "https://apihub.agnes-ai.com/v1").strip(),
        )

        ctk.CTkLabel(
            self.agnes_frame,
            text="模型名请使用 agnes-2.0-flash；支持全模态识图，原位翻译与批注将直接读页面图片（无需本地 OCR）。",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=420,
        ).pack(anchor="w", padx=5, pady=(0, 6))
        
        self._on_provider_change(self.provider_var.get())
    
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
        ctk.CTkLabel(
            self.annotation_tab,
            text="覆盖：在原文旁直接显示中文翻译；侧边栏：数字标记 + 长文批注",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=420,
        ).pack(anchor="w", padx=10, pady=(0, 8))

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
    
    def _on_xiaomi_mode_change(self, value: str) -> None:
        from src.models.config import xiaomi_default_base_url

        mode = getattr(self, "_xiaomi_mode_map", {}).get(value, "token_plan")
        if hasattr(self, "xiaomi_base_url_entry"):
            self.xiaomi_base_url_entry.delete(0, "end")
            self.xiaomi_base_url_entry.insert(0, xiaomi_default_base_url(mode))

    def _on_provider_change(self, value: str) -> None:
        """切换提供商时显示对应的设置框架"""
        provider = getattr(self, "_provider_value_map", {}).get(value, value)

        self.openai_frame.pack_forget()
        self.ollama_frame.pack_forget()
        self.deepseek_frame.pack_forget()
        self.xiaomi_frame.pack_forget()
        self.agnes_frame.pack_forget()

        if provider == "openai":
            self.openai_frame.pack(fill="x", padx=10, pady=5)
        elif provider == "ollama":
            self.ollama_frame.pack(fill="x", padx=10, pady=5)
        elif provider == "deepseek":
            self.deepseek_frame.pack(fill="x", padx=10, pady=5)
        elif provider == "xiaomi":
            self.xiaomi_frame.pack(fill="x", padx=10, pady=5)
        elif provider == "agnes":
            self.agnes_frame.pack(fill="x", padx=10, pady=5)
    
    def _on_save(self) -> None:
        """保存设置"""
        label = self.provider_var.get()
        self.settings.llm.provider = getattr(self, "_provider_value_map", {}).get(
            label, label.lower()
        )
        self.settings.llm.openai.api_key = self.api_key_entry.get()
        self.settings.llm.openai.model = self.model_entry.get()
        self.settings.llm.ollama.base_url = self.base_url_entry.get()
        self.settings.llm.ollama.model = self.ollama_model_entry.get()
        self.settings.llm.deepseek.api_key = self.deepseek_api_key_entry.get()
        self.settings.llm.deepseek.model = self.deepseek_model_entry.get()
        self.settings.llm.deepseek.base_url = self.deepseek_base_url_entry.get()
        xiaomi_mode_label = self.xiaomi_mode_var.get()
        self.settings.llm.xiaomi.api_mode = getattr(self, "_xiaomi_mode_map", {}).get(
            xiaomi_mode_label, "token_plan"
        )
        self.settings.llm.xiaomi.api_key = self.xiaomi_api_key_entry.get().strip()
        self.settings.llm.xiaomi.model = self.xiaomi_model_entry.get().strip()
        self.settings.llm.xiaomi.base_url = self.xiaomi_base_url_entry.get().strip()
        self.settings.llm.agnes.api_key = self.agnes_api_key_entry.get().strip()
        self.settings.llm.agnes.model = self.agnes_model_entry.get().strip()
        self.settings.llm.agnes.base_url = self.agnes_base_url_entry.get().strip()
        self.settings.annotation.mode = self.mode_var.get()
        self.settings.annotation.detail_level = self.detail_var.get()
        self.settings.app.theme = self.theme_var.get()
        self.settings.app.language = self.language_var.get()
        
        self.result = self.settings
        self.destroy()
    
    def _on_cancel(self) -> None:
        """取消"""
        self.destroy()
