"""
Main API for lab_parser.

This module provides the high-level functions that users interact with.
"""

import pandas as pd
from pathlib import Path
from typing import Union, List, Optional, Dict
import warnings

from .detectors import detect_instrument_type
from .parsers import PARSER_REGISTRY
from .utils.logger import get_logger

logger = get_logger(__name__)


def read(
    filepath: Union[str, Path],
    instrument: Optional[str] = None,
    **kwargs
) -> pd.DataFrame:
    """
    Read and parse a lab instrument data file.

    Parameters
    ----------
    filepath : str or Path
        Path to the instrument data file
    instrument : str, optional
        Instrument type (e.g., 'biotek_synergy', 'quantstudio').
        If not provided, will auto-detect from file content.
    **kwargs
        Additional arguments passed to the specific parser

    Returns
    -------
    pd.DataFrame
        Parsed data in a clean pandas DataFrame

    Examples
    --------
    >>> import lab_parser as lp
    >>> df = lp.read("plate_reader.csv")
    >>> df.head()
       well sample    od600  time
    0   A1  control  0.234   0
    1   A2  drug_1   0.456   0

    >>> # Specify instrument explicitly
    >>> df = lp.read("data.xlsx", instrument="biotek_synergy")

    >>> # Parse qPCR data
    >>> df = lp.read("qpcr.xlsx", instrument="quantstudio")
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    # Auto-detect instrument if not specified
    if instrument is None:
        logger.debug(f"Auto-detecting instrument type for: {filepath.name}")
        instrument = detect_instrument_type(filepath)

        if instrument is None:
            raise ValueError(
                f"Could not auto-detect instrument type for: {filepath}\n"
                f"Please specify instrument explicitly using: instrument='type'\n"
                f"Available instruments: {list_instruments()}"
            )

        logger.info(f"Detected instrument: {instrument}")

    # Get the appropriate parser
    if instrument not in PARSER_REGISTRY:
        raise ValueError(
            f"Unknown instrument: {instrument}\n"
            f"Available instruments: {list_instruments()}\n"
            f"To add support for your instrument, please open an issue at:\n"
            f"https://github.com/pravinth24/universal-lab-parser/issues"
        )

    parser_class = PARSER_REGISTRY[instrument]
    parser = parser_class()

    # Parse the file
    try:
        df = parser.parse(filepath, **kwargs)
        logger.debug(f"Successfully parsed {filepath.name}: {len(df)} rows")
        return df

    except Exception as e:
        logger.error(f"Failed to parse {filepath}: {e}")
        raise


def read_batch(
    filepaths: List[Union[str, Path]],
    instrument: Optional[str] = None,
    combine: bool = False,
    **kwargs
) -> Union[List[pd.DataFrame], pd.DataFrame]:
    """
    Read and parse multiple lab instrument data files.

    Parameters
    ----------
    filepaths : list of str or Path
        List of file paths to parse
    instrument : str, optional
        Instrument type. If not provided, will auto-detect for each file.
    combine : bool, default False
        If True, concatenate all DataFrames into a single DataFrame
    **kwargs
        Additional arguments passed to the specific parser

    Returns
    -------
    list of pd.DataFrame or pd.DataFrame
        If combine=False, returns list of DataFrames.
        If combine=True, returns single concatenated DataFrame.

    Examples
    --------
    >>> import lab_parser as lp
    >>> from pathlib import Path

    >>> # Parse multiple files
    >>> files = Path("./data").glob("*.csv")
    >>> results = lp.read_batch(files)
    >>> len(results)
    10

    >>> # Combine into single DataFrame
    >>> df = lp.read_batch(files, combine=True)
    >>> df.shape
    (1000, 4)
    """
    results = []
    errors = []

    logger.info(f"Batch processing {len(filepaths)} files")

    for filepath in filepaths:
        try:
            df = read(filepath, instrument=instrument, **kwargs)

            # Add source file column
            df['_source_file'] = Path(filepath).name

            results.append(df)

        except Exception as e:
            logger.warning(f"Failed to parse {filepath}: {e}")
            errors.append((filepath, str(e)))

    logger.info(
        f"Batch processing complete: {len(results)} success, {len(errors)} errors"
    )

    if errors:
        warnings.warn(
            f"Failed to parse {len(errors)} files. "
            f"See log for details.",
            UserWarning
        )

    if combine:
        if results:
            return pd.concat(results, ignore_index=True)
        else:
            return pd.DataFrame()

    return results


def list_instruments() -> Dict[str, str]:
    """
    List all supported instruments.

    Returns
    -------
    dict
        Dictionary mapping instrument IDs to descriptions

    Examples
    --------
    >>> import lab_parser as lp
    >>> instruments = lp.list_instruments()
    >>> for key, desc in instruments.items():
    ...     print(f"{key}: {desc}")
    biotek_synergy: BioTek Synergy Plate Reader
    quantstudio: Applied Biosystems QuantStudio qPCR
    ...
    """
    from .parsers import INSTRUMENT_INFO
    return INSTRUMENT_INFO


def detect_instrument(filepath: Union[str, Path]) -> Optional[str]:
    """
    Detect the instrument type from a file without parsing.

    Parameters
    ----------
    filepath : str or Path
        Path to the instrument data file

    Returns
    -------
    str or None
        Instrument type if detected, None otherwise

    Examples
    --------
    >>> import lab_parser as lp
    >>> lp.detect_instrument("plate_reader.csv")
    'biotek_synergy'
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    return detect_instrument_type(filepath)
