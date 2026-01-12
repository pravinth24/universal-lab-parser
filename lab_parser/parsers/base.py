"""
Base parser class for all instrument parsers.
"""

from pathlib import Path
from typing import Optional
import pandas as pd
from abc import ABC, abstractmethod
import re


class BaseParser(ABC):
    """
    Abstract base class for instrument parsers.

    All instrument-specific parsers should inherit from this class
    and implement the parse() method.
    """

    @abstractmethod
    def parse(self, filepath: Path, **kwargs) -> pd.DataFrame:
        """
        Parse an instrument data file.

        Parameters
        ----------
        filepath : Path
            Path to the data file
        **kwargs
            Additional parser-specific arguments

        Returns
        -------
        pd.DataFrame
            Parsed data in standard format
        """
        raise NotImplementedError("Parser must implement parse() method")

    def _standardize_well_format(self, well: str) -> str:
        """
        Standardize well format to A1, B2, etc.

        Parameters
        ----------
        well : str
            Well identifier (e.g., 'A01', 'A1', 'a1')

        Returns
        -------
        str
            Standardized well format (e.g., 'A1')
        """
        if not well:
            return well

        well = well.strip().upper()

        # Extract letter and number
        match = re.match(r'([A-Z]+)(\d+)', well)
        if match:
            letter, number = match.groups()
            return f"{letter}{int(number)}"

        return well

    def _extract_plate_layout(self, rows: int = 8, cols: int = 12) -> list:
        """
        Generate standard plate well layout.

        Parameters
        ----------
        rows : int
            Number of rows (default: 8 for 96-well plate)
        cols : int
            Number of columns (default: 12 for 96-well plate)

        Returns
        -------
        list
            List of well identifiers (e.g., ['A1', 'A2', ..., 'H12'])
        """
        wells = []
        for row in range(rows):
            row_letter = chr(ord('A') + row)
            for col in range(1, cols + 1):
                wells.append(f"{row_letter}{col}")
        return wells
