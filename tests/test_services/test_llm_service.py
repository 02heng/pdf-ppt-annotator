import pytest
from src.services.llm_service import LLMService
from src.models.config import LLMConfig, OpenAIConfig, OllamaConfig


def test_llm_service_initialization():
    config = LLMConfig(provider="openai")
    service = LLMService(config)
    assert service is not None
    assert service.provider == "openai"


def test_llm_service_invalid_provider():
    config = LLMConfig(provider="invalid")
    with pytest.raises(ValueError):
        LLMService(config)
