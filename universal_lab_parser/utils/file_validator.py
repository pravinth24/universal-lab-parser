"""Advanced file validation using magic numbers and file signatures."""

from pathlib import Path
from typing import Optional, Dict, Tuple
import struct


# Magic number signatures for common instrument file formats
# Format: {parser_type: [(offset, magic_bytes, description)]}
MAGIC_NUMBERS: Dict[str, list] = {
    "waters": [
        # Waters .arw files often have specific headers
        (0, b'WATR', "Waters binary file header"),
        (0, b'EMPOWER', "Waters Empower format"),
    ],
    "agilent": [
        # Agilent ChemStation files
        (0, b'179', "Agilent ChemStation"),
    ],
    "thermo": [
        # Thermo .raw files
        (0, b'Finnigan', "Thermo Finnigan format"),
    ],
}


class FileValidator:
    """Validates instrument data files."""

    def __init__(self, filepath: Path):
        """
        Initialize file validator.

        Args:
            filepath: Path to file to validate
        """
        self.filepath = Path(filepath)

    def validate_exists(self) -> bool:
        """Check if file exists."""
        return self.filepath.exists()

    def validate_size(self, max_size_mb: int = 500) -> Tuple[bool, str]:
        """
        Validate file size.

        Args:
            max_size_mb: Maximum allowed file size in MB

        Returns:
            Tuple of (is_valid, message)
        """
        if not self.filepath.exists():
            return False, "File does not exist"

        size_mb = self.filepath.stat().st_size / (1024 * 1024)

        if size_mb > max_size_mb:
            return False, f"File too large: {size_mb:.2f} MB (max: {max_size_mb} MB)"

        return True, f"File size OK: {size_mb:.2f} MB"

    def validate_readable(self) -> Tuple[bool, str]:
        """Check if file is readable."""
        try:
            with open(self.filepath, 'rb') as f:
                f.read(1)  # Try to read first byte
            return True, "File is readable"
        except PermissionError:
            return False, "Permission denied"
        except Exception as e:
            return False, f"Cannot read file: {e}"

    def detect_by_magic_number(self) -> Optional[str]:
        """
        Detect file type using magic numbers.

        Returns:
            Parser type if detected, None otherwise
        """
        try:
            with open(self.filepath, 'rb') as f:
                # Read first 512 bytes for magic number detection
                header = f.read(512)

            for parser_type, signatures in MAGIC_NUMBERS.items():
                for offset, magic_bytes, description in signatures:
                    if len(header) >= offset + len(magic_bytes):
                        if header[offset:offset+len(magic_bytes)] == magic_bytes:
                            return parser_type

            return None

        except Exception:
            return None

    def get_file_info(self) -> Dict[str, any]:
        """
        Get comprehensive file information.

        Returns:
            Dictionary with file info
        """
        if not self.filepath.exists():
            return {"error": "File does not exist"}

        stat = self.filepath.stat()

        return {
            "name": self.filepath.name,
            "extension": self.filepath.suffix,
            "size_bytes": stat.st_size,
            "size_mb": stat.st_size / (1024 * 1024),
            "is_file": self.filepath.is_file(),
            "is_dir": self.filepath.is_dir(),
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "is_readable": self.validate_readable()[0],
        }

    def validate_all(self, max_size_mb: int = 500) -> Tuple[bool, list]:
        """
        Run all validations.

        Args:
            max_size_mb: Maximum file size in MB

        Returns:
            Tuple of (all_valid, list of validation messages)
        """
        messages = []
        all_valid = True

        # Check exists
        if not self.validate_exists():
            messages.append("✗ File does not exist")
            return False, messages
        messages.append("✓ File exists")

        # Check size
        valid, msg = self.validate_size(max_size_mb)
        messages.append(f"{'✓' if valid else '✗'} {msg}")
        if not valid:
            all_valid = False

        # Check readable
        valid, msg = self.validate_readable()
        messages.append(f"{'✓' if valid else '✗'} {msg}")
        if not valid:
            all_valid = False

        # Try magic number detection
        detected_type = self.detect_by_magic_number()
        if detected_type:
            messages.append(f"✓ Detected format: {detected_type}")
        else:
            messages.append("⚠ Could not detect format by magic number (will try extension)")

        return all_valid, messages


def validate_file(filepath: Path, max_size_mb: int = 500) -> Tuple[bool, str]:
    """
    Quick file validation.

    Args:
        filepath: Path to validate
        max_size_mb: Maximum file size

    Returns:
        Tuple of (is_valid, message)
    """
    validator = FileValidator(filepath)
    all_valid, messages = validator.validate_all(max_size_mb)

    return all_valid, "\n".join(messages)
