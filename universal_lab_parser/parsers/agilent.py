"""Parser for Agilent instrument data files (COMING SOON)."""

from universal_lab_parser.core.base_parser import BaseParser
from universal_lab_parser.core.data_model import LabData
from universal_lab_parser.core.exceptions import UnsupportedFormatError


class AgilentParser(BaseParser):
    """
    Parser for Agilent GC/LC/MS data files.

    TODO: Implement support for:
    - .d folders (ChemStation data)
    - .ch files (individual channels)
    - MassHunter files
    """

    def __init__(self):
        super().__init__()
        self.vendor_name = "Agilent"
        self.instrument_types = ["GC", "LC", "LC/MS", "GC/MS"]
        self.supported_extensions = [".d", ".ch"]

    def can_parse(self, filepath: str) -> bool:
        """Check if this parser can handle the file."""
        # TODO: Implement
        return False

    def parse(self, filepath: str, **kwargs) -> LabData:
        """Parse an Agilent data file."""
        raise UnsupportedFormatError(
            "Agilent parser is not yet implemented. "
            "Want to help? See CONTRIBUTING.md"
        )
