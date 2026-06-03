# tests/integration_test.py
import pytest
import os
import tempfile
from src.models.config import Settings, LLMConfig
from src.parsers.pdf_parser import PDFParser
from src.parsers.ppt_parser import PPTParser
from src.models.document import Document

def test_pdf_parser_integration():
    """PDF 解析器集成测试"""
    parser = PDFParser()
    
    # 测试不存在的文件
    with pytest.raises(FileNotFoundError):
        parser.parse("nonexistent.pdf")
    
    # 测试不支持的格式（创建临时txt文件）
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        with pytest.raises(ValueError):
            parser.parse(tmp_path)
    finally:
        os.unlink(tmp_path)

def test_ppt_parser_integration():
    """PPT 解析器集成测试"""
    parser = PPTParser()
    
    # 测试不存在的文件
    with pytest.raises(FileNotFoundError):
        parser.parse("nonexistent.pptx")
    
    # 测试不支持的格式（创建临时txt文件）
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        with pytest.raises(ValueError):
            parser.parse(tmp_path)
    finally:
        os.unlink(tmp_path)

def test_settings_model():
    """设置模型测试"""
    settings = Settings()
    
    assert settings.llm.provider == "openai"
    assert settings.annotation.mode == "overlay"
    assert settings.app.language == "zh-CN"

def test_document_model():
    """文档模型测试"""
    from src.models.page import Page
    from src.models.annotation import Annotation
    
    doc = Document(file_path="test.pdf", file_type="pdf")
    
    # 添加页面
    page = Page(page_number=1, content="Test content")
    doc.add_page(page)
    
    assert doc.total_pages == 1
    assert doc.get_page(1).content == "Test content"
    
    # 添加批注
    annotation = Annotation(
        id="test-1",
        page_number=1,
        content="测试批注",
        agent_role="translator"
    )
    page.add_annotation(annotation)
    
    assert len(page.annotations) == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])