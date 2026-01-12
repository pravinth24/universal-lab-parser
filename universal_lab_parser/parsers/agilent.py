"""Parser for Agilent instrument data files.

This parser supports Agilent GC/LC/MS data formats:
- .D folders (ChemStation and MassHunter format)
- .CH files (individual channel data)
- .MS files (mass spectrometry data)

Note: Agilent formats are proprietary. This implementation is based on
reverse engineering and may not support all file variations.
"""

import struct
import csv
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import warnings

from universal_lab_parser.core.base_parser import BaseParser
from universal_lab_parser.core.data_model import LabData, Metadata, Chromatogram, Peak
from universal_lab_parser.core.exceptions import FileFormatError, ParseError
from universal_lab_parser.utils.logger import get_logger

logger = get_logger(__name__)


class AgilentParser(BaseParser):
    """
    Parser for Agilent GC/LC/MS data files.

    Supports:
    - .D folders (ChemStation/MassHunter data directory format)
    - .CH files (individual chromatogram channel files)
    - .MS files (mass spectrometry data)

    Note: Agilent formats are complex and partially undocumented.
    This parser handles common cases but may not work with all file variations.
    """

    # Known Agilent file signatures
    CHEMSTATION_SIGNATURES = [b'179', b'\x02\x33\x30', b'Agilent']
    MS_SIGNATURES = [b'GC/MSD', b'LC/MSD', b'MS']

    def __init__(self):
        super().__init__()
        self.vendor_name = "Agilent"
        self.instrument_types = ["GC", "LC", "HPLC", "GC/MS", "LC/MS", "UPLC"]
        self.supported_extensions = [".d", ".ch", ".ms"]

    def can_parse(self, filepath: str) -> bool:
        """Check if this parser can handle the file."""
        path = Path(filepath)

        # Check if it's a .D folder
        if path.is_dir() and path.suffix.lower() == ".d":
            return True

        # Check file extensions
        if path.suffix.lower() in self.supported_extensions:
            return True

        return False

    def parse(self, filepath: str, **kwargs) -> LabData:
        """
        Parse an Agilent data file.

        Args:
            filepath: Path to .D folder, .CH file, or .MS file
            **kwargs: Optional parsing parameters
                - extract_peaks: bool, whether to extract peak data (default: True)
                - signal: str, which signal to extract (e.g., "FID1A", "DAD1A")

        Returns:
            LabData: Parsed data object

        Raises:
            FileFormatError: If file format is invalid
            ParseError: If parsing fails
        """
        path = self.validate_file(filepath)

        if not self.can_parse(str(path)):
            raise FileFormatError(
                f"Agilent parser cannot handle file: {filepath}\n"
                f"Supported extensions: {self.supported_extensions}"
            )

        try:
            if path.is_dir() and path.suffix.lower() == ".d":
                logger.info(f"Parsing Agilent .D folder: {path.name}")
                return self._parse_d_folder(path, **kwargs)
            elif path.suffix.lower() == ".ch":
                logger.info(f"Parsing Agilent .CH file: {path.name}")
                return self._parse_ch_file(path, **kwargs)
            elif path.suffix.lower() == ".ms":
                logger.info(f"Parsing Agilent .MS file: {path.name}")
                return self._parse_ms_file(path, **kwargs)
            else:
                raise FileFormatError(f"Unsupported Agilent file type: {path}")

        except Exception as e:
            logger.error(f"Failed to parse Agilent file: {e}")
            raise ParseError(f"Failed to parse Agilent file {filepath}: {e}")

    def _parse_d_folder(self, path: Path, extract_peaks: bool = True, signal: Optional[str] = None) -> LabData:
        """
        Parse Agilent .D folder (ChemStation/MassHunter format).

        .D folders contain multiple files:
        - ACQ.TXT / ACQMETH.TXT: Acquisition method
        - SAMPLE.TXT / SAMPLE.XML: Sample information
        - DATA.MS / *.CH: Binary chromatogram data
        - RESULTS.CSV: Integration results (peaks)
        - Various .REG files: Metadata

        Args:
            path: Path to .D folder
            extract_peaks: Whether to extract peaks
            signal: Specific signal to extract (e.g., "FID1A")

        Returns:
            LabData object
        """
        # Parse metadata from various text files
        metadata = self._extract_d_folder_metadata(path)

        # Find and parse chromatogram data
        chromatogram = self._extract_d_folder_chromatogram(path, signal)

        # Extract peaks if requested
        peaks = []
        if extract_peaks:
            peaks = self._extract_d_folder_peaks(path)

        return LabData(
            metadata=metadata,
            chromatogram=chromatogram,
            peaks=peaks,
            source_file=str(path),
            parser_version="1.0.0"
        )

    def _extract_d_folder_metadata(self, path: Path) -> Metadata:
        """
        Extract metadata from .D folder files.

        Looks for metadata in:
        - SAMPLE.TXT / SAMPLE.XML
        - ACQ.TXT / ACQMETH.TXT
        - INJINFO.TXT
        - *.REG files
        """
        metadata_dict = {}

        # Try to parse SAMPLE.TXT or SAMPLE.XML
        for sample_file in ['SAMPLE.TXT', 'sample.txt', 'SAMPLE.XML', 'sample.xml']:
            sample_path = path / sample_file
            if sample_path.exists():
                metadata_dict.update(self._parse_sample_file(sample_path))
                break

        # Try to parse ACQ.TXT or ACQMETH.TXT
        for acq_file in ['ACQ.TXT', 'acq.txt', 'ACQMETH.TXT', 'acqmeth.txt']:
            acq_path = path / acq_file
            if acq_path.exists():
                metadata_dict.update(self._parse_acq_file(acq_path))
                break

        # Try to parse INJINFO.TXT
        injinfo_path = path / 'INJINFO.TXT'
        if not injinfo_path.exists():
            injinfo_path = path / 'injinfo.txt'
        if injinfo_path.exists():
            metadata_dict.update(self._parse_injinfo_file(injinfo_path))

        # Parse .REG files for additional metadata
        reg_files = list(path.glob("*.REG")) + list(path.glob("*.reg"))
        for reg_file in reg_files:
            metadata_dict.update(self._parse_reg_file(reg_file))

        # Try to parse date
        run_date = self._extract_date_from_metadata(metadata_dict)
        if not run_date:
            # Fallback to folder modification time
            try:
                run_date = datetime.fromtimestamp(path.stat().st_mtime)
            except:
                run_date = None

        return Metadata(
            instrument_type=metadata_dict.get('instrument_type', 'LC'),
            instrument_model=metadata_dict.get('instrument_name', 'Agilent ChemStation'),
            software_version=metadata_dict.get('software_version'),
            sample_name=metadata_dict.get('sample_name', path.stem),
            method_name=metadata_dict.get('method_name'),
            operator=metadata_dict.get('operator'),
            run_date=run_date,
            injection_volume=metadata_dict.get('injection_volume'),
            raw_metadata=metadata_dict
        )

    def _parse_sample_file(self, sample_path: Path) -> Dict[str, str]:
        """Parse SAMPLE.TXT or SAMPLE.XML for sample information."""
        metadata = {}

        try:
            with open(sample_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

                # Parse as key-value pairs or XML
                if sample_path.suffix.lower() == '.txt':
                    for line in content.split('\n'):
                        if ':' in line or '=' in line:
                            sep = ':' if ':' in line else '='
                            parts = line.split(sep, 1)
                            if len(parts) == 2:
                                key = parts[0].strip().lower().replace(' ', '_')
                                value = parts[1].strip()
                                metadata[key] = value
                else:
                    # Basic XML parsing for common fields
                    import re
                    sample_match = re.search(r'<Sample.*?Name="([^"]+)"', content)
                    if sample_match:
                        metadata['sample_name'] = sample_match.group(1)

        except Exception as e:
            logger.debug(f"Error parsing sample file: {e}")

        return metadata

    def _parse_acq_file(self, acq_path: Path) -> Dict[str, str]:
        """Parse ACQ.TXT or ACQMETH.TXT for acquisition method info."""
        metadata = {}

        try:
            with open(acq_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if ':' in line or '=' in line:
                        sep = ':' if ':' in line else '='
                        parts = line.split(sep, 1)
                        if len(parts) == 2:
                            key = parts[0].strip().lower().replace(' ', '_')
                            value = parts[1].strip()
                            metadata[key] = value

                            # Map to standard fields
                            if 'method' in key:
                                metadata['method_name'] = value
                            elif 'instrument' in key:
                                metadata['instrument_name'] = value
        except Exception as e:
            logger.debug(f"Error parsing ACQ file: {e}")

        return metadata

    def _parse_injinfo_file(self, injinfo_path: Path) -> Dict[str, str]:
        """Parse INJINFO.TXT for injection information."""
        metadata = {}

        try:
            with open(injinfo_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip().lower().replace(' ', '_')
                        value = value.strip()
                        metadata[key] = value

                        # Map specific fields
                        if 'inj_vol' in key or 'injection_volume' in key:
                            try:
                                metadata['injection_volume'] = float(value)
                            except:
                                pass
                        elif 'operator' in key:
                            metadata['operator'] = value
                        elif 'date' in key or 'time' in key:
                            metadata['injection_date'] = value

        except Exception as e:
            logger.debug(f"Error parsing INJINFO file: {e}")

        return metadata

    def _parse_reg_file(self, reg_path: Path) -> Dict[str, str]:
        """Parse .REG file for registry-style metadata."""
        metadata = {}

        try:
            with open(reg_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('['):
                        key, value = line.split('=', 1)
                        key = key.strip().lower().replace(' ', '_')
                        value = value.strip().strip('"')
                        metadata[key] = value

        except Exception as e:
            logger.debug(f"Error parsing REG file: {e}")

        return metadata

    def _extract_date_from_metadata(self, metadata: Dict) -> Optional[datetime]:
        """Extract and parse date from metadata dictionary."""
        date_keys = ['date', 'injection_date', 'acquisition_date', 'run_date', 'acq_date']

        for key in date_keys:
            if key in metadata:
                date_str = metadata[key]
                # Try multiple date formats
                formats = [
                    '%Y-%m-%d %H:%M:%S',
                    '%m/%d/%Y %H:%M:%S',
                    '%d-%b-%Y %H:%M:%S',
                    '%Y-%m-%d',
                    '%m/%d/%Y',
                ]

                for fmt in formats:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue

        return None

    def _extract_d_folder_chromatogram(self, path: Path, signal: Optional[str] = None) -> Optional[Chromatogram]:
        """
        Extract chromatogram data from .D folder.

        Looks for:
        - *.CH files (individual channel chromatograms)
        - DATA.MS (mass spectrometry data)
        """
        # Find .CH files
        ch_files = list(path.glob("*.CH")) + list(path.glob("*.ch"))

        if signal:
            # Try to find specific signal file
            signal_file = path / f"{signal.upper()}.CH"
            if not signal_file.exists():
                signal_file = path / f"{signal.lower()}.ch"
            if signal_file.exists():
                ch_files = [signal_file]

        if ch_files:
            # Parse the first (or specified) .CH file
            ch_file = ch_files[0]
            logger.debug(f"Parsing chromatogram from: {ch_file.name}")
            return self._parse_ch_file_data(ch_file)

        # If no .CH files, look for DATA.MS
        ms_file = path / "DATA.MS"
        if not ms_file.exists():
            ms_file = path / "data.ms"

        if ms_file.exists():
            logger.debug(f"Parsing chromatogram from: {ms_file.name}")
            return self._parse_ms_file_data(ms_file)

        logger.warning("No chromatogram data files found in .D folder")
        return Chromatogram(time=[], signal=[], time_units="minutes", signal_units="counts")

    def _extract_d_folder_peaks(self, path: Path) -> List[Peak]:
        """
        Extract peak data from .D folder.

        Looks for:
        - RESULTS.CSV (integration results)
        - REPORT.TXT (report with peak table)
        """
        peaks = []

        # Try to parse RESULTS.CSV
        results_file = path / "RESULTS.CSV"
        if not results_file.exists():
            results_file = path / "results.csv"

        if results_file.exists():
            peaks = self._parse_results_csv(results_file)

        # If no RESULTS.CSV, try REPORT.TXT
        if not peaks:
            report_file = path / "REPORT.TXT"
            if not report_file.exists():
                report_file = path / "report.txt"

            if report_file.exists():
                peaks = self._parse_report_txt(report_file)

        logger.debug(f"Extracted {len(peaks)} peaks from .D folder")
        return peaks

    def _parse_results_csv(self, csv_path: Path) -> List[Peak]:
        """Parse RESULTS.CSV file for peak data."""
        peaks = []

        try:
            with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # CSV format varies, try common column names
                    rt = self._extract_float(row, ['RT', 'Retention Time', 'Time', 'RetTime'])
                    area = self._extract_float(row, ['Area', 'Peak Area', 'PeakArea'])
                    height = self._extract_float(row, ['Height', 'Peak Height', 'PeakHeight'])
                    name = row.get('Name') or row.get('Compound') or row.get('Peak Name')

                    if rt is not None:
                        peaks.append(Peak(
                            retention_time=rt,
                            area=area,
                            height=height,
                            name=name
                        ))

        except Exception as e:
            logger.debug(f"Error parsing RESULTS.CSV: {e}")

        return peaks

    def _parse_report_txt(self, report_path: Path) -> List[Peak]:
        """Parse REPORT.TXT for peak data (basic extraction)."""
        peaks = []

        try:
            with open(report_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

                # Look for peak table section
                # This is highly heuristic and format-dependent
                lines = content.split('\n')
                in_peak_table = False

                for line in lines:
                    # Simple heuristic: lines with multiple numbers separated by spaces
                    if 'Peak' in line or 'RT' in line:
                        in_peak_table = True
                        continue

                    if in_peak_table:
                        parts = line.split()
                        if len(parts) >= 3:
                            try:
                                rt = float(parts[1])
                                area = float(parts[2]) if len(parts) > 2 else None
                                height = float(parts[3]) if len(parts) > 3 else None

                                peaks.append(Peak(
                                    retention_time=rt,
                                    area=area,
                                    height=height
                                ))
                            except ValueError:
                                continue

        except Exception as e:
            logger.debug(f"Error parsing REPORT.TXT: {e}")

        return peaks

    def _extract_float(self, row: Dict, possible_keys: List[str]) -> Optional[float]:
        """Try to extract float value from dict using multiple possible keys."""
        for key in possible_keys:
            if key in row:
                try:
                    return float(row[key])
                except (ValueError, TypeError):
                    pass
        return None

    def _parse_ch_file(self, path: Path, **kwargs) -> LabData:
        """
        Parse Agilent .CH file (individual channel chromatogram).

        .CH files are binary files containing:
        - File header with metadata
        - Chromatogram data points (time, signal pairs)

        Args:
            path: Path to .CH file

        Returns:
            LabData object
        """
        # Parse chromatogram from .CH file
        chromatogram = self._parse_ch_file_data(path)

        # Minimal metadata from file
        metadata = Metadata(
            instrument_type="LC",
            instrument_model="Agilent ChemStation",
            sample_name=path.stem,
            run_date=datetime.fromtimestamp(path.stat().st_mtime)
        )

        return LabData(
            metadata=metadata,
            chromatogram=chromatogram,
            peaks=[],
            source_file=str(path),
            parser_version="1.0.0"
        )

    def _parse_ch_file_data(self, ch_path: Path) -> Chromatogram:
        """
        Parse chromatogram data from .CH binary file.

        Agilent .CH file structure (ChemStation format):
        - Header: ~0x1000 bytes
        - Data section: series of (time, signal) values
        - Encoding: typically float32 or int32
        """
        try:
            with open(ch_path, 'rb') as f:
                data = f.read()

            # Try to find signature and determine version
            signature_offset = self._find_chemstation_signature(data)

            # Extract data using heuristics
            time_data, signal_data = self._extract_ch_data_heuristic(data)

            # Determine signal units from filename
            filename_upper = ch_path.name.upper()
            signal_units = "counts"
            channel_name = ch_path.stem

            if 'FID' in filename_upper:
                signal_units = "pA"
                channel_name = "FID"
            elif 'DAD' in filename_upper or 'UV' in filename_upper:
                signal_units = "mAU"
                channel_name = "DAD"
            elif 'TCD' in filename_upper:
                signal_units = "µV"
                channel_name = "TCD"

            return Chromatogram(
                time=time_data,
                signal=signal_data,
                time_units="minutes",
                signal_units=signal_units,
                channel_name=channel_name
            )

        except Exception as e:
            logger.error(f"Error parsing .CH file: {e}")
            return Chromatogram(time=[], signal=[], time_units="minutes", signal_units="counts")

    def _find_chemstation_signature(self, data: bytes) -> Optional[int]:
        """Find ChemStation file signature in binary data."""
        for sig in self.CHEMSTATION_SIGNATURES:
            idx = data.find(sig)
            if idx != -1:
                logger.debug(f"Found ChemStation signature at offset {idx}")
                return idx
        return None

    def _extract_ch_data_heuristic(self, data: bytes) -> Tuple[List[float], List[float]]:
        """
        Extract chromatogram data from .CH file using heuristics.

        Agilent .CH files typically have data after header (~0x1000 bytes).
        Data is usually stored as:
        - Interleaved (time, signal) pairs
        - OR separate time and signal arrays
        """
        time_data = []
        signal_data = []

        # Skip header (typically ~4096 bytes)
        header_sizes = [4096, 2048, 1024, 8192]

        for header_size in header_sizes:
            if header_size >= len(data):
                continue

            data_section = data[header_size:]

            # Try parsing as float32 pairs
            try:
                num_pairs = min(10000, len(data_section) // 8)
                temp_time = []
                temp_signal = []

                for i in range(num_pairs):
                    offset = i * 8
                    if offset + 8 <= len(data_section):
                        try:
                            t, s = struct.unpack('<ff', data_section[offset:offset+8])

                            # Validate: time should be increasing, reasonable range
                            if 0 <= t <= 200 and -1e6 <= s <= 1e6:
                                # Check if monotonically increasing
                                if not temp_time or t > temp_time[-1]:
                                    temp_time.append(t)
                                    temp_signal.append(s)
                                else:
                                    break
                        except struct.error:
                            break

                # If we got good data, use it
                if len(temp_time) >= 50:
                    logger.debug(f"Extracted {len(temp_time)} data points with header size {header_size}")
                    time_data = temp_time
                    signal_data = temp_signal
                    break

            except Exception as e:
                logger.debug(f"Error with header size {header_size}: {e}")
                continue

        return time_data, signal_data

    def _parse_ms_file(self, path: Path, **kwargs) -> LabData:
        """
        Parse Agilent .MS file (mass spectrometry data).

        .MS files contain MS data in binary format.
        """
        chromatogram = self._parse_ms_file_data(path)

        metadata = Metadata(
            instrument_type="LC/MS",
            instrument_model="Agilent MassHunter",
            sample_name=path.stem,
            run_date=datetime.fromtimestamp(path.stat().st_mtime)
        )

        return LabData(
            metadata=metadata,
            chromatogram=chromatogram,
            peaks=[],
            source_file=str(path),
            parser_version="1.0.0"
        )

    def _parse_ms_file_data(self, ms_path: Path) -> Chromatogram:
        """
        Parse chromatogram data from .MS binary file.

        MS files are more complex, containing spectral data.
        This extracts TIC (Total Ion Chromatogram) if available.
        """
        try:
            with open(ms_path, 'rb') as f:
                data = f.read()

            # Basic extraction - this is simplified
            # Real MS files would need spectrum parsing
            time_data, signal_data = self._extract_ms_tic_heuristic(data)

            return Chromatogram(
                time=time_data,
                signal=signal_data,
                time_units="minutes",
                signal_units="intensity",
                channel_name="TIC"
            )

        except Exception as e:
            logger.error(f"Error parsing .MS file: {e}")
            return Chromatogram(time=[], signal=[], time_units="minutes", signal_units="intensity")

    def _extract_ms_tic_heuristic(self, data: bytes) -> Tuple[List[float], List[float]]:
        """Extract TIC (Total Ion Chromatogram) from MS data using heuristics."""
        # Placeholder for MS parsing - this is complex
        # Would need detailed format specification
        time_data = []
        signal_data = []

        # Skip large header (MS files have bigger headers)
        header_size = 16384  # 16KB typical for MS files

        if len(data) > header_size:
            # Try to find data patterns
            # This is highly simplified
            pass

        return time_data, signal_data


# Example usage and testing
if __name__ == "__main__":
    parser = AgilentParser()
    print(f"Agilent Parser initialized")
    print(f"Vendor: {parser.vendor_name}")
    print(f"Supported extensions: {parser.supported_extensions}")
    print(f"Instrument types: {parser.instrument_types}")
