"""Parser for Thermo Fisher instrument data files (COMING SOON)."""

from universal_lab_parser.core.base_parser import BaseParser
from universal_lab_parser.core.data_model import LabData
from universal_lab_parser.core.exceptions import UnsupportedFormatError


class ThermoParser(BaseParser):
    """
    Parser for Thermo Fisher mass spectrometry data files.

    TODO: Implement support for:
    - .raw files (Xcalibur format)
    - Note: Can leverage existing tools like ThermoRawFileParser
    """

    def __init__(self):
        super().__init__()
        self.vendor_name = "Thermo Fisher"
        self.instrument_types = ["LC/MS", "GC/MS", "Orbitrap"]
        self.supported_extensions = [".raw"]

    def can_parse(self, filepath: str) -> bool:
        """Check if this parser can handle the file."""
        # TODO: Implement (need to differentiate from Waters .raw)
        return False

    def parse(self, filepath: str, **kwargs) -> LabData:
        """Parse a Thermo Fisher data file."""
        raise UnsupportedFormatError(
            "Thermo Fisher parser is not yet implemented. "
            "Want to help? See CONTRIBUTING.md"
        )
