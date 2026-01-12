"""Tests for parser implementations."""

import pytest
from pathlib import Path
from universal_lab_parser.parsers import get_parser, list_parsers, WatersParser
from universal_lab_parser.core.exceptions import ParserNotFoundError


class TestParserRegistry:
    """Tests for parser registry functionality."""

    def test_list_parsers(self):
        """Test listing available parsers."""
        parsers = list_parsers()
        assert isinstance(parsers, list)
        assert "waters" in parsers

    def test_get_parser_valid(self):
        """Test getting a valid parser."""
        parser = get_parser("waters")
        assert isinstance(parser, WatersParser)

    def test_get_parser_invalid(self):
        """Test getting an invalid parser raises error."""
        with pytest.raises(ParserNotFoundError):
            get_parser("nonexistent")


class TestWatersParser:
    """Tests for Waters parser."""

    def test_parser_initialization(self):
        """Test Waters parser initializes correctly."""
        parser = WatersParser()
        assert parser.vendor_name == "Waters"
        assert ".arw" in parser.supported_extensions
        assert ".raw" in parser.supported_extensions

    def test_can_parse_arw(self):
        """Test Waters parser recognizes .arw files."""
        parser = WatersParser()
        assert parser.can_parse("sample.arw")
        assert parser.can_parse("SAMPLE.ARW")

    def test_can_parse_raw_folder(self):
        """Test Waters parser recognizes .raw folders."""
        parser = WatersParser()
        # Would need actual folder to test
        # For now, just test extension check works
        assert ".raw" in parser.supported_extensions

    def test_cannot_parse_other_formats(self):
        """Test Waters parser rejects other formats."""
        parser = WatersParser()
        assert not parser.can_parse("sample.txt")
        assert not parser.can_parse("sample.d")

    # Note: Add integration tests with actual data files once available
    # @pytest.mark.skipif(not Path("tests/fixtures/waters/sample.arw").exists(),
    #                     reason="No test fixtures available")
    # def test_parse_real_file(self):
    #     """Test parsing a real Waters file."""
    #     parser = WatersParser()
    #     data = parser.parse("tests/fixtures/waters/sample.arw")
    #     assert data.metadata is not None
    #     assert data.metadata.instrument_type == "HPLC"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
