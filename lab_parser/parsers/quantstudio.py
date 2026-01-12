"""
Applied Biosystems QuantStudio qPCR parser.

Supports: QuantStudio 3, 5, 6, 7
Format: Excel export (.xlsx)
"""

from pathlib import Path
import pandas as pd
import openpyxl
from typing import Optional, Dict
from .base import BaseParser
from ..utils.logger import get_logger

logger = get_logger(__name__)


class QuantStudioParser(BaseParser):
    """Parser for Applied Biosystems QuantStudio qPCR data."""

    def parse(self, filepath: Path, **kwargs) -> pd.DataFrame:
        """
        Parse QuantStudio qPCR Excel file.

        Parameters
        ----------
        filepath : Path
            Path to QuantStudio Excel file
        **kwargs
            sheet_name : str, optional
                Sheet to parse (default: 'Results')
            include_undetermined : bool, optional
                Include wells with undetermined Ct (default: False)

        Returns
        -------
        pd.DataFrame
            Parsed qPCR data with columns:
            - well: Well position
            - sample_name: Sample name
            - target_name: Target gene name
            - ct: Ct value (threshold cycle)
            - quantity: Quantity (if standard curve)
            - omit: Whether well is flagged to omit
        """
        sheet_name = kwargs.get('sheet_name', 'Results')
        include_undetermined = kwargs.get('include_undetermined', False)

        if filepath.suffix.lower() not in ['.xlsx', '.xls']:
            raise ValueError("QuantStudio parser requires Excel file (.xlsx or .xls)")

        try:
            # Try to read Results sheet
            df = self._parse_results_sheet(filepath, sheet_name)

            # Filter out undetermined if requested
            if not include_undetermined:
                df = df[df['ct'] != 'Undetermined']

            # Convert Ct to numeric
            df['ct'] = pd.to_numeric(df['ct'], errors='coerce')

            logger.info(f"Parsed QuantStudio data: {len(df)} wells")

            return df

        except Exception as e:
            logger.error(f"Failed to parse QuantStudio file: {e}")
            raise

    def _parse_results_sheet(self, filepath: Path, sheet_name: str) -> pd.DataFrame:
        """
        Parse the Results sheet from QuantStudio Excel file.

        QuantStudio format typically has:
        - Header rows with run info
        - Column headers: Well, Sample Name, Target Name, CT, etc.
        - Data rows
        """
        try:
            # Read Excel file
            df = pd.read_excel(filepath, sheet_name=sheet_name)

            # Find the header row
            header_row = self._find_header_row(df)

            if header_row is None:
                raise ValueError("Could not find header row in Results sheet")

            # Re-read with correct header
            df = pd.read_excel(
                filepath,
                sheet_name=sheet_name,
                header=header_row
            )

            # Standardize column names
            df = self._standardize_columns(df)

            # Select relevant columns
            required_cols = ['well', 'sample_name', 'target_name', 'ct']
            optional_cols = ['quantity', 'omit']

            # Check for required columns
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                raise ValueError(f"Missing required columns: {missing}")

            # Select columns
            cols_to_keep = required_cols + [
                col for col in optional_cols if col in df.columns
            ]

            df = df[cols_to_keep]

            # Remove empty rows
            df = df.dropna(subset=['well'], how='all')

            return df

        except Exception as e:
            logger.error(f"Failed to parse Results sheet: {e}")
            raise

    def _find_header_row(self, df: pd.DataFrame) -> Optional[int]:
        """
        Find the row index containing column headers.

        QuantStudio files have metadata at top, then column headers.
        Look for row with 'Well' or 'Well Position'.
        """
        for idx, row in df.iterrows():
            row_str = str(row.values).lower()
            if 'well' in row_str and ('ct' in row_str or 'c(t)' in row_str):
                return idx

        return None

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names to consistent format."""
        col_mapping = {
            'Well': 'well',
            'Well Position': 'well',
            'Sample Name': 'sample_name',
            'Sample': 'sample_name',
            'Target Name': 'target_name',
            'Target': 'target_name',
            'CT': 'ct',
            'C(T)': 'ct',
            'Ct': 'ct',
            'Quantity': 'quantity',
            'Omit': 'omit',
        }

        # Rename columns
        for old_name, new_name in col_mapping.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})

        return df
