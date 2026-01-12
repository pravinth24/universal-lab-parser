"""Parser for Waters instrument data files.

This parser supports Waters HPLC/UPLC data formats:
- .arw files (Empower/Millennium binary format)
- .raw folders (MassLynx legacy format)

Note: Waters formats are proprietary. This implementation is based on
reverse engineering and may not support all file variations.
"""

import struct
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import warnings

from universal_lab_parser.core.base_parser import BaseParser
from universal_lab_parser.core.data_model import LabData, Metadata, Chromatogram, Peak
from universal_lab_parser.core.exceptions import FileFormatError, ParseError
from universal_lab_parser.utils.logger import get_logger

logger = get_logger(__name__)


class WatersParser(BaseParser):
    """
    Parser for Waters HPLC/UPLC data files.

    Supports:
    - .arw files (Empower/Millennium raw data)
    - .raw folders (MassLynx format with Header.txt and .DAT files)

    Note: Waters formats are complex and partially undocumented.
    This parser handles common cases but may not work with all file variations.
    """

    # Known Waters file signatures
    ARW_SIGNATURES = [b'WATR', b'Empower', b'MILLENNIUM']

    def __init__(self):
        super().__init__()
        self.vendor_name = "Waters"
        self.instrument_types = ["HPLC", "UPLC", "ACQUITY", "Alliance"]
        self.supported_extensions = [".arw", ".raw"]

    def can_parse(self, filepath: str) -> bool:
        """Check if this parser can handle the file."""
        path = Path(filepath)

        # Check file extension
        if path.suffix.lower() in self.supported_extensions:
            return True

        # Check if it's a .raw folder (Waters legacy format)
        if path.is_dir() and path.suffix.lower() == ".raw":
            return True

        return False

    def parse(self, filepath: str, **kwargs) -> LabData:
        """
        Parse a Waters data file.

        Args:
            filepath: Path to .arw file or .raw folder
            **kwargs: Optional parsing parameters
                - extract_peaks: bool, whether to extract peak data (default: True)
                - channel: int, which channel to extract (default: 1)

        Returns:
            LabData: Parsed data object

        Raises:
            FileFormatError: If file format is invalid
            ParseError: If parsing fails
        """
        path = self.validate_file(filepath)

        if not self.can_parse(str(path)):
            raise FileFormatError(
                f"Waters parser cannot handle file: {filepath}\n"
                f"Supported extensions: {self.supported_extensions}"
            )

        try:
            if path.suffix.lower() == ".arw":
                logger.info(f"Parsing Waters .arw file: {path.name}")
                return self._parse_arw_file(path, **kwargs)
            elif path.is_dir() and path.suffix.lower() == ".raw":
                logger.info(f"Parsing Waters .raw folder: {path.name}")
                return self._parse_raw_folder(path, **kwargs)
            else:
                raise FileFormatError(f"Unsupported Waters file type: {path}")

        except Exception as e:
            logger.error(f"Failed to parse Waters file: {e}")
            raise ParseError(f"Failed to parse Waters file {filepath}: {e}")

    def _parse_arw_file(self, path: Path, extract_peaks: bool = True, channel: int = 1) -> LabData:
        """
        Parse Waters .arw binary file format.

        .arw files contain:
        - File header with signature
        - Metadata section
        - Chromatogram data blocks
        - Peak table (optional)

        Args:
            path: Path to .arw file
            extract_peaks: Whether to extract peak information
            channel: Which channel to extract (default: 1)

        Returns:
            LabData object with parsed data
        """
        with open(path, 'rb') as f:
            data = f.read()

        # Verify file signature
        signature_found = False
        for sig in self.ARW_SIGNATURES:
            if data[:len(sig)] == sig or sig in data[:512]:
                signature_found = True
                logger.debug(f"Found Waters signature: {sig}")
                break

        if not signature_found:
            logger.warning("No known Waters signature found, attempting parse anyway")

        # Parse metadata from header
        metadata = self._extract_arw_metadata(data, path)

        # Extract chromatogram data
        chromatogram = self._extract_arw_chromatogram(data, channel)

        # Extract peaks if requested
        peaks = []
        if extract_peaks:
            peaks = self._extract_arw_peaks(data)

        return LabData(
            metadata=metadata,
            chromatogram=chromatogram,
            peaks=peaks,
            source_file=str(path),
            parser_version="1.0.0"
        )

    def _extract_arw_metadata(self, data: bytes, path: Path) -> Metadata:
        """
        Extract metadata from .arw file header.

        Waters .arw files have metadata scattered throughout the binary.
        We look for ASCII strings and known patterns.
        """
        metadata_dict = {}

        # Extract readable ASCII strings from the first 4KB (header region)
        header = data[:4096]
        strings = self._extract_ascii_strings(header, min_length=3)

        # Look for common metadata patterns
        for s in strings:
            s_upper = s.upper()
            if 'ACQUITY' in s_upper or 'ALLIANCE' in s_upper:
                metadata_dict['instrument_model'] = s
            elif 'EMPOWER' in s_upper:
                metadata_dict['software'] = s
            elif 'SAMPLE' in s_upper and ':' in s:
                parts = s.split(':', 1)
                if len(parts) == 2:
                    metadata_dict['sample_name'] = parts[1].strip()
            elif 'METHOD' in s_upper and ':' in s:
                parts = s.split(':', 1)
                if len(parts) == 2:
                    metadata_dict['method_name'] = parts[1].strip()
            elif 'OPERATOR' in s_upper and ':' in s:
                parts = s.split(':', 1)
                if len(parts) == 2:
                    metadata_dict['operator'] = parts[1].strip()

        # Try to extract date from file
        try:
            run_date = datetime.fromtimestamp(path.stat().st_mtime)
        except:
            run_date = None

        return Metadata(
            instrument_type="HPLC",
            instrument_model=metadata_dict.get('instrument_model', 'Waters ACQUITY/Alliance'),
            software_version=metadata_dict.get('software', 'Empower'),
            sample_name=metadata_dict.get('sample_name', path.stem),
            method_name=metadata_dict.get('method_name'),
            operator=metadata_dict.get('operator'),
            run_date=run_date,
            raw_metadata=metadata_dict
        )

    def _extract_arw_chromatogram(self, data: bytes, channel: int = 1) -> Optional[Chromatogram]:
        """
        Extract chromatogram data from .arw file.

        Waters chromatogram data is typically stored as:
        - Time array (float32 or float64)
        - Signal array (float32 or float64)
        - Data blocks are often in the middle/end of the file

        This uses heuristics to find likely data blocks.
        """
        # Look for data blocks - typically large sections of sequential float values
        time_data, signal_data = self._find_chromatogram_data_blocks(data)

        if not time_data or not signal_data:
            logger.warning("Could not extract chromatogram data from .arw file")
            return Chromatogram(
                time=[],
                signal=[],
                time_units="minutes",
                signal_units="mAU",
                channel_name=f"Channel {channel}"
            )

        return Chromatogram(
            time=time_data,
            signal=signal_data,
            time_units="minutes",
            signal_units="mAU",
            channel_name=f"PDA Channel {channel}"
        )

    def _extract_arw_peaks(self, data: bytes) -> List[Peak]:
        """
        Extract peak data from .arw file.

        Peak tables in Waters files are challenging to locate without
        full format documentation. This is a best-effort implementation.
        """
        peaks = []

        # Look for peak table markers in ASCII strings
        strings = self._extract_ascii_strings(data, min_length=4)

        # Waters peak tables sometimes have recognizable patterns
        # This is a simplified heuristic approach
        for i, s in enumerate(strings):
            if 'PEAK' in s.upper() or 'RT' in s.upper():
                # Try to extract numerical data nearby
                # This is highly heuristic and may not work for all files
                pass

        logger.debug(f"Extracted {len(peaks)} peaks from .arw file")
        return peaks

    def _find_chromatogram_data_blocks(self, data: bytes) -> Tuple[List[float], List[float]]:
        """
        Find chromatogram data blocks in binary data.

        Uses heuristics:
        - Look for large blocks of floats in reasonable ranges
        - Time data: typically 0-100 minutes, monotonically increasing
        - Signal data: typically 0-10000 mAU, varies
        """
        time_data = []
        signal_data = []

        # Search through the file for float arrays
        # Try both float32 and float64
        for offset in range(0, len(data) - 8, 4):
            try:
                # Try to unpack as float32
                values = []
                for i in range(min(100, (len(data) - offset) // 4)):
                    val = struct.unpack('<f', data[offset + i*4:offset + i*4 + 4])[0]

                    # Check if value is in reasonable range for time (0-200 minutes)
                    if 0 <= val <= 200:
                        values.append(val)
                    else:
                        break

                # If we found a sequence of reasonable values
                if len(values) >= 50:
                    # Check if monotonically increasing (time data)
                    if all(values[i] <= values[i+1] for i in range(len(values)-1)):
                        if not time_data or len(values) > len(time_data):
                            logger.debug(f"Found potential time data at offset {offset}, length {len(values)}")
                            time_data = values

                    # Or check if it looks like signal data (varies)
                    elif not signal_data or len(values) > len(signal_data):
                        logger.debug(f"Found potential signal data at offset {offset}, length {len(values)}")
                        signal_data = values

            except (struct.error, ValueError):
                continue

        # If arrays are different lengths, truncate to shorter
        if time_data and signal_data:
            min_len = min(len(time_data), len(signal_data))
            time_data = time_data[:min_len]
            signal_data = signal_data[:min_len]

        return time_data, signal_data

    def _parse_raw_folder(self, path: Path, extract_peaks: bool = True, **kwargs) -> LabData:
        """
        Parse Waters .raw folder (MassLynx legacy format).

        .raw folders contain multiple files:
        - _HEADER.TXT or Header.txt: Metadata
        - _FUNC001.DAT: Binary chromatogram data
        - _FUNC001.INF: Acquisition information
        - _INLET.INF: Inlet parameters
        - etc.

        Args:
            path: Path to .raw folder
            extract_peaks: Whether to extract peaks

        Returns:
            LabData object
        """
        # Find header file (case insensitive)
        header_file = None
        for name in ['_HEADER.TXT', 'Header.txt', '_header.txt', 'HEADER.TXT']:
            candidate = path / name
            if candidate.exists():
                header_file = candidate
                break

        if not header_file:
            logger.warning(f".raw folder missing header file, using defaults")
            metadata = Metadata(
                instrument_type="HPLC",
                instrument_model="Waters MassLynx",
                sample_name=path.stem
            )
        else:
            metadata = self._parse_header_txt(header_file)

        # Parse chromatogram data from .DAT files
        chromatogram = self._parse_dat_files(path)

        # Parse peaks if available
        peaks = []
        if extract_peaks:
            peaks = self._extract_raw_peaks(path)

        return LabData(
            metadata=metadata,
            chromatogram=chromatogram,
            peaks=peaks,
            source_file=str(path),
            parser_version="1.0.0"
        )

    def _parse_header_txt(self, header_path: Path) -> Metadata:
        """
        Parse Waters Header.txt file for metadata.

        Format is typically key: value pairs.
        """
        metadata_dict = {}

        try:
            with open(header_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata_dict[key.strip()] = value.strip()
        except Exception as e:
            logger.warning(f"Error parsing header file: {e}")

        # Try to parse date
        run_date = None
        date_str = metadata_dict.get('Acquired Date') or metadata_dict.get('Date')
        if date_str:
            try:
                # Try common date formats
                for fmt in ['%Y-%m-%d %H:%M:%S', '%d-%b-%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S']:
                    try:
                        run_date = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
            except Exception as e:
                logger.debug(f"Could not parse date '{date_str}': {e}")

        return Metadata(
            instrument_type="HPLC",
            instrument_model=metadata_dict.get("Instrument", "Waters MassLynx"),
            method_name=metadata_dict.get("Method", None),
            sample_name=metadata_dict.get("Sample Name", None) or metadata_dict.get("SampleName", None),
            operator=metadata_dict.get("Operator", None),
            run_date=run_date,
            raw_metadata=metadata_dict
        )

    def _parse_dat_files(self, raw_folder: Path) -> Optional[Chromatogram]:
        """
        Parse .DAT files in a .raw folder for chromatogram data.

        .DAT files contain binary chromatogram data, usually as:
        - Header section
        - Data pairs (time, intensity) as float32 or float64

        Typical filename: _FUNC001.DAT
        """
        # Find .DAT files
        dat_files = list(raw_folder.glob("*.DAT")) + list(raw_folder.glob("*.dat"))

        if not dat_files:
            logger.warning("No .DAT files found in .raw folder")
            return Chromatogram(time=[], signal=[], time_units="minutes", signal_units="counts")

        # Parse the first .DAT file found
        dat_file = dat_files[0]
        logger.debug(f"Parsing .DAT file: {dat_file.name}")

        try:
            with open(dat_file, 'rb') as f:
                data = f.read()

            # .DAT files often have a header followed by data
            # Skip header (typically first 512-2048 bytes)
            header_size = self._estimate_dat_header_size(data)
            data_section = data[header_size:]

            # Try to parse as pairs of float32 or float64
            time_data, signal_data = self._parse_dat_binary_data(data_section)

            return Chromatogram(
                time=time_data,
                signal=signal_data,
                time_units="minutes",
                signal_units="counts",
                channel_name="Function 1"
            )

        except Exception as e:
            logger.error(f"Error parsing .DAT file: {e}")
            return Chromatogram(time=[], signal=[], time_units="minutes", signal_units="counts")

    def _estimate_dat_header_size(self, data: bytes) -> int:
        """
        Estimate header size in a .DAT file.

        Headers typically contain ASCII text followed by binary data.
        """
        # Look for first occurrence of consistent binary patterns
        # This is heuristic-based
        for offset in [512, 1024, 2048, 256]:
            if offset < len(data):
                # Check if data after this offset looks like float values
                try:
                    test_vals = struct.unpack('<10f', data[offset:offset+40])
                    # Check if values are in reasonable range
                    if all(0 <= abs(v) <= 100000 for v in test_vals):
                        logger.debug(f"Estimated .DAT header size: {offset} bytes")
                        return offset
                except:
                    continue

        return 512  # Default fallback

    def _parse_dat_binary_data(self, data: bytes) -> Tuple[List[float], List[float]]:
        """
        Parse binary chromatogram data from .DAT file data section.

        Data can be:
        - Pairs of float32: (time1, signal1, time2, signal2, ...)
        - Pairs of float64
        - Separate arrays of time and signal
        """
        time_data = []
        signal_data = []

        # Try float32 pairs first
        try:
            num_pairs = len(data) // 8  # 2 float32 values per pair
            for i in range(num_pairs):
                offset = i * 8
                if offset + 8 <= len(data):
                    time, signal = struct.unpack('<ff', data[offset:offset+8])

                    # Sanity check values
                    if 0 <= time <= 200 and -1000000 <= signal <= 1000000:
                        time_data.append(time)
                        signal_data.append(signal)
                    else:
                        # If values seem unreasonable, stop
                        if i > 10:  # But keep data if we got some good values
                            break
        except Exception as e:
            logger.debug(f"Error parsing as float32 pairs: {e}")

        # If that didn't work well, try float64 pairs
        if len(time_data) < 10:
            time_data = []
            signal_data = []
            try:
                num_pairs = len(data) // 16  # 2 float64 values per pair
                for i in range(num_pairs):
                    offset = i * 16
                    if offset + 16 <= len(data):
                        time, signal = struct.unpack('<dd', data[offset:offset+16])

                        if 0 <= time <= 200 and -1000000 <= signal <= 1000000:
                            time_data.append(time)
                            signal_data.append(signal)
                        else:
                            if i > 10:
                                break
            except Exception as e:
                logger.debug(f"Error parsing as float64 pairs: {e}")

        logger.debug(f"Parsed {len(time_data)} data points from .DAT file")
        return time_data, signal_data

    def _extract_raw_peaks(self, raw_folder: Path) -> List[Peak]:
        """
        Extract peak data from .raw folder.

        Peaks may be stored in:
        - .PKL files (peak list)
        - .INF files (may contain peak info)
        """
        peaks = []

        # Look for .PKL files
        pkl_files = list(raw_folder.glob("*.PKL")) + list(raw_folder.glob("*.pkl"))

        for pkl_file in pkl_files:
            try:
                # .PKL files are often text-based
                with open(pkl_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Parse peak information
                    # Format varies, but often contains RT, Area, Height
                    # This is highly format-dependent
                    pass
            except Exception as e:
                logger.debug(f"Error parsing .PKL file: {e}")

        return peaks

    @staticmethod
    def _extract_ascii_strings(data: bytes, min_length: int = 4) -> List[str]:
        """
        Extract ASCII strings from binary data.

        Useful for finding metadata in binary files.

        Args:
            data: Binary data
            min_length: Minimum string length to extract

        Returns:
            List of extracted strings
        """
        strings = []
        current_string = []

        for byte in data:
            # Check if byte is printable ASCII (space to ~)
            if 32 <= byte <= 126:
                current_string.append(chr(byte))
            else:
                # End of string
                if len(current_string) >= min_length:
                    strings.append(''.join(current_string))
                current_string = []

        # Don't forget the last string
        if len(current_string) >= min_length:
            strings.append(''.join(current_string))

        return strings


# Example usage and testing
if __name__ == "__main__":
    parser = WatersParser()
    print(f"Waters Parser initialized")
    print(f"Vendor: {parser.vendor_name}")
    print(f"Supported extensions: {parser.supported_extensions}")
    print(f"Instrument types: {parser.instrument_types}")
