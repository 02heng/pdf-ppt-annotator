import pytest
from src.parsers.ppt_parser import PPTParser

def test_ppt_parser_initialization():
    parser = PPTParser()
    assert parser is not None

def test_ppt_parser_nonexistent_file():
    parser = PPTParser()
    with pytest.raises(FileNotFoundError):
        parser.parse("nonexistent.pptx")
