from typing import Optional
from pydantic import BaseModel, Field

class OpenAIConfig(BaseModel):
    """OpenAI 配置"""
    api_key: str = ""
    model: str = "gpt-4o"
    temperature: float = 0.3
    max_tokens: int = 4096

class OllamaConfig(BaseModel):
    """Ollama 配置"""
    base_url: str = "http://localhost:11434"
    model: str = "llama3:70b"
    temperature: float = 0.3

class DeepSeekConfig(BaseModel):
    """DeepSeek 配置"""
    api_key: str = ""
    model: str = "deepseek-v4-pro"
    temperature: float = 0.3
    max_tokens: int = 4096
    base_url: str = "https://api.deepseek.com"

class LLMConfig(BaseModel):
    """LLM 配置"""
    provider: str = "openai"  # "openai", "ollama" 或 "deepseek"
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    deepseek: DeepSeekConfig = Field(default_factory=DeepSeekConfig)

class AnnotationStyle(BaseModel):
    """批注样式配置"""
    font_family: str = "Microsoft YaHei"
    font_size: int = 12
    color: str = "#333333"
    background: str = "#FFFFCC"

class AnnotationConfig(BaseModel):
    """批注配置"""
    mode: str = "sidebar"  # "overlay" 或 "sidebar"
    detail_level: str = "detailed"  # "summary", "detailed", "custom"
    style: AnnotationStyle = Field(default_factory=AnnotationStyle)

class AppConfig(BaseModel):
    """应用配置"""
    language: str = "zh-CN"
    theme: str = "system"  # "light", "dark", "system"
    recent_files_limit: int = 10
    auto_save: bool = True

class Settings(BaseModel):
    """全局设置"""
    llm: LLMConfig = Field(default_factory=LLMConfig)
    annotation: AnnotationConfig = Field(default_factory=AnnotationConfig)
    app: AppConfig = Field(default_factory=AppConfig)