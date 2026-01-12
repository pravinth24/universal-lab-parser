"""
Universal Lab Parser

Parse proprietary lab instrument data files into standard, usable formats.
"""

from universal_lab_parser.__version__ import __version__
from universal_lab_parser.core.base_parser import BaseParser
from universal_lab_parser.core.data_model import LabData, Chromatogram, Peak, Metadata

# Convenience function for quick parsing
def parse_file(filepath, parser_type=None, **kwargs):
    """
    Parse a lab instrument file.

    Args:
        filepath: Path to the instrument data file
        parser_type: Optional parser type ('waters', 'agilent', 'thermo').
                     If None, auto-detection is attempted.
        **kwargs: Additional parser-specific options

    Returns:
        LabData: Parsed data object

    Example:
        >>> from universal_lab_parser import parse_file
        >>> data = parse_file("sample.arw")
        >>> data.to_csv("output.csv")
    """
    from universal_lab_parser.utils.file_detection import detect_file_type
    from universal_lab_parser.parsers import get_parser

    if parser_type is None:
        parser_type = detect_file_type(filepath)

    parser = get_parser(parser_type)
    return parser.parse(filepath, **kwargs)


def batch_parse(directory, pattern="*", parser_type=None, **kwargs):
    """
    Parse multiple files in a directory.

    Args:
        directory: Path to directory containing files
        pattern: Glob pattern for files to parse (default: "*")
        parser_type: Optional parser type. If None, auto-detection per file.
        **kwargs: Additional parser-specific options

    Returns:
        list[LabData]: List of parsed data objects

    Example:
        >>> results = batch_parse("./data/", pattern="*.arw")
        >>> for data in results:
        ...     data.to_csv(f"{data.metadata.sample_name}.csv")
    """
    import glob
    from pathlib import Path

    directory_path = Path(directory)
    files = glob.glob(str(directory_path / pattern))

    results = []
    for filepath in files:
        try:
            data = parse_file(filepath, parser_type=parser_type, **kwargs)
            results.append(data)
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")

    return results


__all__ = [
    "__version__",
    "parse_file",
    "batch_parse",
    "BaseParser",
    "LabData",
    "Chromatogram",
    "Peak",
    "Metadata",
]
