"""Base parser class that all instrument-specific parsers inherit from."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from universal_lab_parser.core.data_model import LabData


class BaseParser(ABC):
    """Abstract base class for all instrument parsers."""

    def __init__(self):
        """Initialize the parser."""
        self.supported_extensions = []
        self.vendor_name = "Unknown"
        self.instrument_types = []

    @abstractmethod
    def parse(self, filepath: str, **kwargs) -> LabData:
        """
        Parse an instrument data file.

        Args:
            filepath: Path to the data file
            **kwargs: Parser-specific options

        Returns:
            LabData: Parsed data object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        pass

    @abstractmethod
    def can_parse(self, filepath: str) -> bool:
        """
        Check if this parser can handle the given file.

        Args:
            filepath: Path to check

        Returns:
            bool: True if parser can handle this file
        """
        pass

    def validate_file(self, filepath: str) -> Path:
        """
        Validate that file exists and is readable.

        Args:
            filepath: Path to validate

        Returns:
            Path: Validated Path object

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        return path

    def __repr__(self) -> str:
        """String representation of parser."""
        return (
            f"{self.__class__.__name__}("
            f"vendor={self.vendor_name}, "
            f"types={self.instrument_types}, "
            f"extensions={self.supported_extensions}"
            f")"
        )
