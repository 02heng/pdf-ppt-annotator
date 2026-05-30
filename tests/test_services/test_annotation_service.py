import pytest
from src.services.annotation_service import AnnotationService
from src.models.document import Document
from src.models.page import Page
from src.models.config import LLMConfig


def test_annotation_service_initialization():
    config = LLMConfig(provider="openai")
    service = AnnotationService(config)
    assert service is not None


def test_annotation_service_process_document():
    config = LLMConfig(provider="openai")
    service = AnnotationService(config)

    doc = Document(file_path="test.pdf", file_type="pdf")
    doc.add_page(Page(page_number=1, content="Test content"))

    # Note: actual test needs mock CrewService
    # result = service.process_document(doc)
    # assert result is not None
