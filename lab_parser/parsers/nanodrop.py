"""
Thermo NanoDrop spectrophotometer parser.

Supports: NanoDrop One, NanoDrop 2000, NanoDrop 8000
Format: Tab-delimited text files
"""

from pathlib import Path
import pandas as pd
from typing import Optional
from .base import BaseParser
from ..utils.logger import get_logger

logger = get_logger(__name__)


class NanoDropParser(BaseParser):
    """Parser for Thermo NanoDrop spectrophotometer data."""

    def parse(self, filepath: Path, **kwargs) -> pd.DataFrame:
        """
        Parse NanoDrop text file.

        Parameters
        ----------
        filepath : Path
            Path to NanoDrop tab-delimited file
        **kwargs
            encoding : str, optional
                File encoding (default: 'utf-8')

        Returns
        -------
        pd.DataFrame
            Parsed spectrophotometer data with columns:
            - sample_id: Sample identifier
            - concentration: Nucleic acid concentration (ng/µL)
            - a260: Absorbance at 260nm
            - a280: Absorbance at 280nm
            - a260_280_ratio: 260/280 ratio (purity indicator)
            - a260_230_ratio: 260/230 ratio (purity indicator)
        """
        encoding = kwargs.get('encoding', 'utf-8')

        try:
            # Read tab-delimited file
            df = pd.read_csv(
                filepath,
                sep='\t',
                encoding=encoding,
                skip_blank_lines=True
            )

            # Standardize column names
            df = self._standardize_columns(df)

            # Extract relevant columns
            df = self._extract_measurements(df)

            logger.info(f"Parsed NanoDrop data: {len(df)} samples")

            return df

        except Exception as e:
            logger.error(f"Failed to parse NanoDrop file: {e}")
            raise

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names from NanoDrop format."""
        col_mapping = {
            'Sample ID': 'sample_id',
            'Sample Name': 'sample_id',
            'Name': 'sample_id',
            'User name': 'user_name',
            'Date': 'date',
            'Time': 'time',
            'Nucleic Acid(ng/ul)': 'concentration',
            'Nucleic Acid': 'concentration',
            'Conc.': 'concentration',
            'A260': 'a260',
            '260': 'a260',
            'A280': 'a280',
            '280': 'a280',
            'A230': 'a230',
            '230': 'a230',
            '260/280': 'a260_280_ratio',
            'A260/A280': 'a260_280_ratio',
            '260/230': 'a260_230_ratio',
            'A260/A230': 'a260_230_ratio',
            'Cursor Position (nm)': 'cursor_pos',
            'Cursor Abs': 'cursor_abs',
        }

        # Rename columns
        for old_name, new_name in col_mapping.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})

        return df

    def _extract_measurements(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract and validate measurement columns."""
        # Required columns
        if 'sample_id' not in df.columns:
            raise ValueError("Missing sample identifier column")

        # Select available columns in preferred order
        preferred_cols = [
            'sample_id',
            'concentration',
            'a260',
            'a280',
            'a230',
            'a260_280_ratio',
            'a260_230_ratio',
            'user_name',
            'date',
            'time',
            'cursor_pos',
            'cursor_abs'
        ]

        available_cols = [col for col in preferred_cols if col in df.columns]

        df = df[available_cols]

        # Remove empty rows
        df = df.dropna(subset=['sample_id'], how='all')

        # Convert numeric columns
        numeric_cols = [
            'concentration', 'a260', 'a280', 'a230',
            'a260_280_ratio', 'a260_230_ratio'
        ]

        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df
