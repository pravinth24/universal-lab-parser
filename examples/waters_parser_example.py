"""
Example usage of the Waters parser.

This demonstrates how to parse Waters HPLC/UPLC data files:
- .arw files (Empower/Millennium format)
- .raw folders (MassLynx legacy format)
"""

from pathlib import Path
from universal_lab_parser.parsers.waters import WatersParser
from universal_lab_parser import parse_file

# Example 1: Parse a Waters .arw file directly
print("=" * 60)
print("Example 1: Parsing Waters .arw file")
print("=" * 60)

# Initialize parser
parser = WatersParser()

# Check if parser can handle a file
test_file = "sample_data.arw"
if Path(test_file).exists():
    can_parse = parser.can_parse(test_file)
    print(f"Can parse {test_file}: {can_parse}")

    # Parse the file
    try:
        data = parser.parse(test_file)

        # Access parsed data
        print(f"\nMetadata:")
        print(f"  Instrument: {data.metadata.instrument_model}")
        print(f"  Sample: {data.metadata.sample_name}")
        print(f"  Method: {data.metadata.method_name}")
        print(f"  Operator: {data.metadata.operator}")
        print(f"  Date: {data.metadata.run_date}")

        print(f"\nChromatogram:")
        print(f"  Data points: {len(data.chromatogram.time)}")
        print(f"  Time range: {min(data.chromatogram.time):.2f} - {max(data.chromatogram.time):.2f} {data.chromatogram.time_units}")
        print(f"  Signal units: {data.chromatogram.signal_units}")

        print(f"\nPeaks:")
        print(f"  Number of peaks: {len(data.peaks)}")

        # Export to CSV
        data.to_csv("output.csv")
        print(f"\nExported to output.csv")

    except Exception as e:
        print(f"Error parsing file: {e}")
else:
    print(f"File {test_file} not found")

# Example 2: Parse a Waters .raw folder
print("\n" + "=" * 60)
print("Example 2: Parsing Waters .raw folder")
print("=" * 60)

test_folder = "sample_data.raw"
if Path(test_folder).exists() and Path(test_folder).is_dir():
    try:
        data = parser.parse(test_folder)

        print(f"\nMetadata:")
        print(f"  Instrument: {data.metadata.instrument_model}")
        print(f"  Sample: {data.metadata.sample_name}")

        print(f"\nChromatogram:")
        print(f"  Data points: {len(data.chromatogram.time)}")

        # Export to JSON
        data.to_json("output.json")
        print(f"\nExported to output.json")

    except Exception as e:
        print(f"Error parsing folder: {e}")
else:
    print(f"Folder {test_folder} not found")

# Example 3: Using the high-level parse_file function
print("\n" + "=" * 60)
print("Example 3: Using high-level parse_file function")
print("=" * 60)

# parse_file auto-detects format
test_file = "sample.arw"
if Path(test_file).exists():
    try:
        # Auto-detection
        data = parse_file(test_file)
        print(f"Automatically detected format and parsed successfully")
        print(f"Source: {data.source_file}")
        print(f"Parser version: {data.parser_version}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"File {test_file} not found")

# Example 4: Parsing with options
print("\n" + "=" * 60)
print("Example 4: Parsing with custom options")
print("=" * 60)

if Path("sample.arw").exists():
    try:
        # Parse without peak extraction (faster)
        data = parser.parse("sample.arw", extract_peaks=False)
        print(f"Parsed without peak extraction")
        print(f"Peaks extracted: {len(data.peaks)}")

        # Parse specific channel
        data = parser.parse("sample.arw", channel=2)
        print(f"Parsed channel 2")

    except Exception as e:
        print(f"Error: {e}")

# Example 5: Batch processing multiple Waters files
print("\n" + "=" * 60)
print("Example 5: Batch processing")
print("=" * 60)

data_dir = Path("./waters_data")
if data_dir.exists():
    arw_files = list(data_dir.glob("*.arw"))

    print(f"Found {len(arw_files)} .arw files")

    for file in arw_files[:3]:  # Process first 3 files
        try:
            data = parser.parse(str(file))
            print(f"✓ Parsed: {file.name} ({len(data.chromatogram.time)} points)")
        except Exception as e:
            print(f"✗ Failed: {file.name} - {e}")
else:
    print(f"Directory {data_dir} not found")

print("\n" + "=" * 60)
print("Waters Parser Features:")
print("=" * 60)
print("""
The Waters parser supports:

1. Binary Format Parsing:
   - Reads .arw binary files using struct unpacking
   - Extracts metadata from embedded ASCII strings
   - Locates chromatogram data using heuristics
   - Handles both float32 and float64 data types

2. Legacy Format Support:
   - Parses .raw folders with multiple files
   - Reads Header.txt for metadata
   - Extracts chromatogram from .DAT binary files
   - Supports multiple date formats

3. Intelligent Data Extraction:
   - Magic number signature verification
   - Automatic data block detection
   - Sanity checking for reasonable values
   - Handles malformed or partial files gracefully

4. Comprehensive Logging:
   - Debug-level logging for troubleshooting
   - Warnings for missing data
   - Detailed error messages

5. Flexible Options:
   - Optional peak extraction
   - Multi-channel support
   - Configurable parsing parameters

Note: Waters formats are proprietary and partially undocumented.
This parser uses reverse-engineering and may not work with all
file variations. If you encounter issues, please:
1. Share sample files on GitHub issues
2. Enable debug logging: logger.setLevel(logging.DEBUG)
3. Check file format version compatibility
""")

print("\nParser Information:")
print(f"Vendor: {parser.vendor_name}")
print(f"Supported extensions: {', '.join(parser.supported_extensions)}")
print(f"Instrument types: {', '.join(parser.instrument_types)}")
print(f"Known signatures: {[sig.decode('utf-8', errors='ignore') for sig in parser.ARW_SIGNATURES]}")
