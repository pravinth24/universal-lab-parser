"""
Lab Parser - Universal laboratory instrument data parser.

Parse ANY lab instrument data file into clean pandas DataFrames.

Usage:
    import lab_parser as lp

    # Auto-detect and parse
    df = lp.read("plate_reader.csv")

    # Specify instrument
    df = lp.read("data.xlsx", instrument="biotek_synergy")

    # Batch processing
    results = lp.read_batch(["file1.csv", "file2.csv"])
"""

from .api import read, read_batch, list_instruments, detect_instrument
from .version import __version__

__all__ = [
    'read',
    'read_batch',
    'list_instruments',
    'detect_instrument',
    '__version__',
]
