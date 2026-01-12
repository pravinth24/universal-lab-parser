"""File type detection utilities."""

from pathlib import Path
from typing import Optional


def detect_file_type(filepath: str) -> Optional[str]:
    """
    Auto-detect the instrument type from file path/extension.

    Args:
        filepath: Path to the file

    Returns:
        str: Parser type ('waters', 'agilent', 'thermo', etc.) or None if unknown

    Example:
        >>> detect_file_type("sample.arw")
        'waters'
    """
    path = Path(filepath)

    # Extension-based detection
    extension_map = {
        '.arw': 'waters',
        '.raw': 'waters',  # Could also be Thermo - need deeper inspection
        '.d': 'agilent',
        '.ch': 'agilent',
        '.lcd': 'shimadzu',
    }

    detected_type = extension_map.get(path.suffix.lower())
    if detected_type:
        return detected_type

    # Folder-based detection (e.g., Agilent .d folders)
    if path.is_dir():
        if path.suffix.lower() == '.d':
            return 'agilent'
        elif path.suffix.lower() == '.raw':
            # Check if it's a Waters .raw folder
            if (path / 'Header.txt').exists():
                return 'waters'

    # Could add magic number (file signature) detection here
    # For example, reading first few bytes to identify format

    return None


def is_supported(filepath: str) -> bool:
    """
    Check if a file is supported.

    Args:
        filepath: Path to check

    Returns:
        bool: True if file type is recognized
    """
    return detect_file_type(filepath) is not None
