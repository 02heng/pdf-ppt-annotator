import pytest
from src.models.document import Document
from src.models.page import Page

def test_document_creation():
    doc = Document(file_path="test.pdf", file_type="pdf")
    assert doc.file_path == "test.pdf"
    assert doc.file_type == "pdf"
    assert doc.pages == []
    assert doc.total_pages == 0

def test_document_add_page():
    doc = Document(file_path="test.pdf", file_type="pdf")
    page = Page(page_number=1, content="Test content")
    doc.add_page(page)
    assert doc.total_pages == 1
    assert doc.pages[0].content == "Test content"

def test_document_get_page():
    doc = Document(file_path="test.pdf", file_type="pdf")
    page1 = Page(page_number=1, content="Page 1")
    page2 = Page(page_number=2, content="Page 2")
    doc.add_page(page1)
    doc.add_page(page2)
    assert doc.get_page(1).content == "Page 1"
    assert doc.get_page(2).content == "Page 2"
    assert doc.get_page(3) is None