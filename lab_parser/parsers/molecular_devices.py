"""
Molecular Devices SpectraMax plate reader parser.

Supports: SpectraMax (all models), SoftMax Pro export
Format: Excel (.xlsx) or CSV
"""

from pathlib import Path
import pandas as pd
import openpyxl
from typing import Optional, Dict
from .base import BaseParser
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MolecularDevicesParser(BaseParser):
    """Parser for Molecular Devices SpectraMax plate reader data."""

    def parse(self, filepath: Path, **kwargs) -> pd.DataFrame:
        """
        Parse Molecular Devices SpectraMax file.

        Parameters
        ----------
        filepath : Path
            Path to SpectraMax Excel or CSV file
        **kwargs
            sheet_name : str, optional
                Excel sheet name to parse (default: first sheet)

        Returns
        -------
        pd.DataFrame
            Parsed plate reader data with columns:
            - well: Well position (A1, B2, etc.)
            - value: Measured value
            - wavelength: Wavelength (if applicable)
            - read_type: Type of read (absorbance, fluorescence, etc.)
        """
        if filepath.suffix.lower() in ['.xlsx', '.xls']:
            return self._parse_excel(filepath, **kwargs)
        else:
            return self._parse_csv(filepath, **kwargs)

    def _parse_excel(self, filepath: Path, **kwargs) -> pd.DataFrame:
        """Parse Excel file from SoftMax Pro."""
        sheet_name = kwargs.get('sheet_name', 0)

        try:
            # Read Excel file
            wb = openpyxl.load_workbook(filepath, data_only=True)

            if isinstance(sheet_name, int):
                sheet = wb.worksheets[sheet_name]
            else:
                sheet = wb[sheet_name]

            # Find plate data section
            plate_data = self._find_plate_data_in_sheet(sheet)

            if plate_data is None:
                raise ValueError("No plate data found in Excel file")

            logger.info(f"Parsed Molecular Devices data: {len(plate_data)} measurements")

            return plate_data

        except Exception as e:
            logger.error(f"Failed to parse Excel file: {e}")
            raise

    def _find_plate_data_in_sheet(self, sheet) -> Optional[pd.DataFrame]:
        """
        Find and extract plate data from Excel sheet.

        SoftMax Pro format typically has:
        - Metadata in top rows
        - Plate layout with row letters (A-H) and column numbers (1-12)
        """
        records = []

        # Search for plate data pattern
        for row_idx, row in enumerate(sheet.iter_rows(values_only=True), start=1):
            if not row or len(row) < 2:
                continue

            # Check if this row starts with a letter (A-H for plate rows)
            first_cell = str(row[0]).strip().upper() if row[0] else ''

            if len(first_cell) == 1 and first_cell.isalpha():
                row_letter = first_cell

                # Parse values from this row
                for col_idx, value in enumerate(row[1:13], start=1):  # Columns 1-12
                    if value is not None and value != '':
                        try:
                            numeric_value = float(value)
                            well = f"{row_letter}{col_idx}"

                            records.append({
                                'well': well,
                                'value': numeric_value
                            })
                        except (ValueError, TypeError):
                            continue

        if not records:
            return None

        df = pd.DataFrame(records)
        df['read_type'] = 'absorbance'  # Default, can be updated if metadata found

        return df

    def _parse_csv(self, filepath: Path, **kwargs) -> pd.DataFrame:
        """Parse CSV file from SoftMax Pro export."""
        try:
            # Read CSV
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Find plate data section
            plate_start = None
            for i, line in enumerate(lines):
                # Look for line starting with plate row letter
                if line.strip() and line[0].upper() in 'ABCDEFGH':
                    plate_start = i
                    break

            if plate_start is None:
                raise ValueError("No plate data found in CSV file")

            # Parse plate section
            records = []
            for line in lines[plate_start:plate_start + 8]:  # 8 rows for 96-well
                parts = line.strip().split(',')

                if len(parts) < 2:
                    continue

                row_letter = parts[0].strip().upper()

                if len(row_letter) != 1 or not row_letter.isalpha():
                    continue

                for col_idx, value in enumerate(parts[1:13], start=1):
                    if value.strip() == '':
                        continue

                    try:
                        numeric_value = float(value)
                        well = f"{row_letter}{col_idx}"

                        records.append({
                            'well': well,
                            'value': numeric_value
                        })
                    except ValueError:
                        continue

            if not records:
                raise ValueError("No valid plate data found")

            df = pd.DataFrame(records)
            df['read_type'] = 'absorbance'

            logger.info(f"Parsed Molecular Devices CSV: {len(df)} measurements")

            return df

        except Exception as e:
            logger.error(f"Failed to parse CSV file: {e}")
            raise
