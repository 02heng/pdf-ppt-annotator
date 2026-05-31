from typing import Optional
from crewai import LLM
from src.models.config import LLMConfig


class LLMService:
    """LLM 服务管理器"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.provider = config.provider
        self._llm: Optional[LLM] = None

        if self.provider not in ["openai", "ollama", "deepseek"]:
            raise ValueError(f"不支持的 LLM 提供商: {self.provider}")

    @property
    def llm(self) -> LLM:
        if self._llm is None:
            self._llm = self._create_llm()
        return self._llm

    def _create_llm(self) -> LLM:
        if self.provider == "openai":
            return self._create_openai_llm()
        elif self.provider == "ollama":
            return self._create_ollama_llm()
        elif self.provider == "deepseek":
            return self._create_deepseek_llm()
        else:
            raise ValueError(f"不支持的提供商: {self.provider}")

    def _create_openai_llm(self) -> LLM:
        config = self.config.openai
        return LLM(
            model=f"openai/{config.model}",
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            api_key=config.api_key
        )

    def _create_ollama_llm(self) -> LLM:
        config = self.config.ollama
        return LLM(
            model=f"ollama/{config.model}",
            base_url=config.base_url,
            temperature=config.temperature
        )

    def _create_deepseek_llm(self) -> LLM:
        config = self.config.deepseek
        return LLM(
            model=f"deepseek/{config.model}",
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            api_key=config.api_key,
            base_url=config.base_url
        )

    def switch_provider(self, provider: str) -> None:
        if provider not in ["openai", "ollama", "deepseek"]:
            raise ValueError(f"不支持的提供商: {provider}")
        self.provider = provider
        self._llm = None

    def update_config(self, config: LLMConfig) -> None:
        self.config = config
        self.provider = config.provider
        self._llm = None
