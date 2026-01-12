"""
BioTek Synergy plate reader parser.

Supports: Synergy H1, H4, Neo2, HTX
Format: CSV export from Gen5 software
"""

from pathlib import Path
import pandas as pd
import csv
from typing import Optional, Dict, List
from .base import BaseParser
from ..utils.logger import get_logger

logger = get_logger(__name__)


class BioTekParser(BaseParser):
    """Parser for BioTek Synergy plate reader data."""

    def parse(self, filepath: Path, **kwargs) -> pd.DataFrame:
        """
        Parse BioTek Synergy CSV export.

        Parameters
        ----------
        filepath : Path
            Path to BioTek CSV file
        **kwargs
            read_name : str, optional
                Specific read name to extract (default: first read found)

        Returns
        -------
        pd.DataFrame
            Parsed plate reader data with columns:
            - well: Well position (A1, B2, etc.)
            - value: Measured value (OD, fluorescence, etc.)
            - time: Time point (if kinetic read)
            - read_name: Name of the read
            - temperature: Temperature (if recorded)
        """
        read_name = kwargs.get('read_name', None)

        # Read file and detect structure
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Extract metadata and data sections
        metadata = self._extract_metadata(lines)
        data_sections = self._find_data_sections(lines)

        if not data_sections:
            raise ValueError("No data sections found in BioTek file")

        # Parse each data section
        all_data = []
        for section in data_sections:
            section_name = section['name']

            # Skip if looking for specific read and this isn't it
            if read_name and section_name != read_name:
                continue

            df = self._parse_plate_section(
                lines,
                section['start_line'],
                section['end_line']
            )

            if df is not None and not df.empty:
                df['read_name'] = section_name
                df['temperature'] = metadata.get('temperature', None)
                all_data.append(df)

        if not all_data:
            raise ValueError(f"No data found for read: {read_name or 'any'}")

        # Combine all sections
        result = pd.concat(all_data, ignore_index=True)

        logger.info(f"Parsed BioTek data: {len(result)} measurements")

        return result

    def _extract_metadata(self, lines: List[str]) -> Dict:
        """Extract metadata from header lines."""
        metadata = {}

        for line in lines[:50]:  # Check first 50 lines
            line = line.strip()

            if 'temperature' in line.lower():
                # Try to extract temperature value
                parts = line.split(',')
                for part in parts:
                    if '°' in part or 'c' in part.lower():
                        try:
                            temp = float(''.join(c for c in part if c.isdigit() or c == '.'))
                            metadata['temperature'] = temp
                        except ValueError:
                            pass

            if 'read' in line.lower() and 'time' in line.lower():
                metadata['has_kinetic'] = True

        return metadata

    def _find_data_sections(self, lines: List[str]) -> List[Dict]:
        """
        Find all plate data sections in the file.

        BioTek files can have multiple reads (e.g., OD600, GFP, RFP).
        Each section starts with a read name.
        """
        sections = []
        current_section = None

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Look for section header (like "Results")
            # followed by plate data within next few lines
            if line_stripped and not line_stripped.startswith(',') and i < len(lines) - 3:
                # Check next few lines for plate header pattern (,1,2,3,...)
                found_plate_header = False
                start_offset = 0

                for offset in range(1, 4):  # Check next 3 lines
                    if i + offset < len(lines):
                        check_line = lines[i + offset].strip()
                        # Look for column number headers: ,1,2,3,4,...
                        if check_line.startswith(',') and check_line.count(',') >= 3:
                            found_plate_header = True
                            start_offset = offset
                            break

                if found_plate_header:
                    if current_section:
                        current_section['end_line'] = i - 1
                        sections.append(current_section)

                    current_section = {
                        'name': line_stripped,
                        'start_line': i + start_offset,
                        'end_line': None
                    }

        # Close last section
        if current_section:
            current_section['end_line'] = len(lines) - 1
            sections.append(current_section)

        return sections

    def _parse_plate_section(
        self,
        lines: List[str],
        start_line: int,
        end_line: int
    ) -> Optional[pd.DataFrame]:
        """
        Parse a single plate data section.

        BioTek format is typically:
        ,1,2,3,4,5,6,7,8,9,10,11,12
        A,0.123,0.145,...
        B,0.234,0.267,...
        """
        try:
            # Extract section lines
            section_lines = lines[start_line:end_line + 1]

            # Remove empty lines
            section_lines = [l for l in section_lines if l.strip()]

            if len(section_lines) < 2:
                return None

            # Parse as CSV
            reader = csv.reader(section_lines)
            rows = list(reader)

            # First row should be column headers (1, 2, 3, ...)
            headers = rows[0]
            data_rows = rows[1:]

            # Parse plate data
            records = []
            for row in data_rows:
                if not row or len(row) < 2:
                    continue

                row_letter = row[0].strip().upper()
                if not row_letter or row_letter == '':
                    continue

                for col_idx, value in enumerate(row[1:], start=1):
                    if value.strip() == '':
                        continue

                    try:
                        numeric_value = float(value)
                        well = f"{row_letter}{col_idx}"

                        records.append({
                            'well': well,
                            'value': numeric_value,
                            'time': 0  # Will be updated if kinetic data
                        })
                    except ValueError:
                        continue

            if not records:
                return None

            return pd.DataFrame(records)

        except Exception as e:
            logger.warning(f"Failed to parse plate section: {e}")
            return None
