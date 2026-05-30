import pytest
from src.services.crew_service import CrewService
from src.models.config import LLMConfig


def test_crew_service_initialization():
    config = LLMConfig(provider="openai")
    service = CrewService(config)
    assert service is not None


def test_crew_service_create_crew():
    config = LLMConfig(provider="openai")
    service = CrewService(config)
    # Note: actual test needs mock LLM
    # crew = service.create_crew()
    # assert crew is not None
