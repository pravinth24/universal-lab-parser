"""
Instrument detection module.

Automatically detects instrument type from file content.
"""

from pathlib import Path
from typing import Optional
import csv
import re


def detect_instrument_type(filepath: Path) -> Optional[str]:
    """
    Detect the instrument type from file content.

    Parameters
    ----------
    filepath : Path
        Path to the instrument data file

    Returns
    -------
    str or None
        Instrument type identifier, or None if not detected
    """
    # Read first few lines to detect format
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            header_lines = [f.readline() for _ in range(20)]
            header_text = ''.join(header_lines).lower()
    except Exception:
        return None

    # BioTek detection
    if any(marker in header_text for marker in ['biotek', 'synergy', 'gen5']):
        return 'biotek_synergy'

    # Molecular Devices detection
    if any(marker in header_text for marker in ['softmax', 'spectramax', 'molecular devices']):
        return 'molecular_devices'

    # Applied Biosystems qPCR detection
    if any(marker in header_text for marker in ['quantstudio', 'applied biosystems', 'real-time pcr']):
        return 'quantstudio'

    # Thermo NanoDrop detection
    if any(marker in header_text for marker in ['nanodrop', 'thermo scientific']) and 'wavelength' in header_text:
        return 'nanodrop'

    # BD flow cytometry detection
    if any(marker in header_text for marker in ['bd facsdiva', 'bd lsrfortessa', 'fsc-a', 'ssc-a']):
        return 'bd_facs'

    # Bio-Rad CFX qPCR detection
    if any(marker in header_text for marker in ['bio-rad', 'cfx', 'cfx manager']):
        return 'biorad_cfx'

    # Roche LightCycler detection
    if any(marker in header_text for marker in ['lightcycler', 'roche']):
        return 'roche_lightcycler'

    return None
