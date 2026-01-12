"""
Parser registry for all supported instruments.
"""

from .base import BaseParser
from .biotek import BioTekParser
from .molecular_devices import MolecularDevicesParser
from .quantstudio import QuantStudioParser
from .nanodrop import NanoDropParser

# Parser registry mapping instrument IDs to parser classes
PARSER_REGISTRY = {
    'biotek_synergy': BioTekParser,
    'molecular_devices': MolecularDevicesParser,
    'quantstudio': QuantStudioParser,
    'nanodrop': NanoDropParser,
}

# Instrument information for display
INSTRUMENT_INFO = {
    'biotek_synergy': 'BioTek Synergy Plate Reader (H1, H4, Neo2, HTX)',
    'molecular_devices': 'Molecular Devices SpectraMax Plate Reader',
    'quantstudio': 'Applied Biosystems QuantStudio qPCR',
    'nanodrop': 'Thermo NanoDrop Spectrophotometer',
}

__all__ = [
    'BaseParser',
    'BioTekParser',
    'MolecularDevicesParser',
    'QuantStudioParser',
    'NanoDropParser',
    'PARSER_REGISTRY',
    'INSTRUMENT_INFO',
]
