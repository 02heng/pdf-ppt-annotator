import pytest
from src.parsers.pdf_parser import PDFParser

def test_pdf_parser_initialization():
    parser = PDFParser()
    assert parser is not None

def test_pdf_parser_nonexistent_file():
    parser = PDFParser()
    with pytest.raises(FileNotFoundError):
        parser.parse("nonexistent.pdf")
