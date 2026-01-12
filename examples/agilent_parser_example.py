"""
Example usage of the Agilent parser.

This demonstrates how to parse Agilent GC/LC/MS data files:
- .D folders (ChemStation/MassHunter format)
- .CH files (individual channel chromatograms)
- .MS files (mass spectrometry data)
"""

from pathlib import Path
from universal_lab_parser.parsers.agilent import AgilentParser
from universal_lab_parser import parse_file

# Example 1: Parse an Agilent .D folder
print("=" * 60)
print("Example 1: Parsing Agilent .D folder")
print("=" * 60)

parser = AgilentParser()

test_folder = "sample.D"
if Path(test_folder).exists():
    can_parse = parser.can_parse(test_folder)
    print(f"Can parse {test_folder}: {can_parse}")

    try:
        data = parser.parse(test_folder)

        # Access metadata from multiple text files
        print(f"\nMetadata:")
        print(f"  Instrument: {data.metadata.instrument_model}")
        print(f"  Sample: {data.metadata.sample_name}")
        print(f"  Method: {data.metadata.method_name}")
        print(f"  Operator: {data.metadata.operator}")
        print(f"  Injection Volume: {data.metadata.injection_volume} µL")
        print(f"  Date: {data.metadata.run_date}")

        print(f"\nChromatogram:")
        print(f"  Data points: {len(data.chromatogram.time)}")
        print(f"  Channel: {data.chromatogram.channel_name}")
        print(f"  Signal units: {data.chromatogram.signal_units}")

        print(f"\nPeaks (from RESULTS.CSV):")
        print(f"  Number of peaks: {len(data.peaks)}")
        for i, peak in enumerate(data.peaks[:5]):
            print(f"    Peak {i+1}: RT={peak.retention_time:.2f} min, Area={peak.area}")

        # Export
        data.to_csv("output.csv")
        print(f"\nExported to output.csv")

    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"Folder {test_folder} not found")

# Example 2: Parse specific signal from .D folder
print("\n" + "=" * 60)
print("Example 2: Parsing specific signal (FID1A)")
print("=" * 60)

if Path("sample.D").exists():
    try:
        # Parse specific detector signal
        data = parser.parse("sample.D", signal="FID1A")
        print(f"Parsed signal: {data.chromatogram.channel_name}")
        print(f"Data points: {len(data.chromatogram.time)}")

    except Exception as e:
        print(f"Error: {e}")

# Example 3: Parse individual .CH file
print("\n" + "=" * 60)
print("Example 3: Parsing .CH file")
print("=" * 60)

ch_file = "FID1A.CH"
if Path(ch_file).exists():
    try:
        data = parser.parse(ch_file)

        print(f"Channel: {data.chromatogram.channel_name}")
        print(f"Signal units: {data.chromatogram.signal_units}")
        print(f"Data points: {len(data.chromatogram.time)}")

        if data.chromatogram.time:
            print(f"Time range: {min(data.chromatogram.time):.2f} - {max(data.chromatogram.time):.2f} minutes")

    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"File {ch_file} not found")

# Example 4: Parse without peak extraction (faster)
print("\n" + "=" * 60)
print("Example 4: Fast parsing without peaks")
print("=" * 60)

if Path("sample.D").exists():
    try:
        # Skip peak extraction for faster parsing
        data = parser.parse("sample.D", extract_peaks=False)
        print(f"Parsed successfully (no peaks extracted)")
        print(f"Chromatogram data points: {len(data.chromatogram.time)}")

    except Exception as e:
        print(f"Error: {e}")

# Example 5: Batch processing .D folders
print("\n" + "=" * 60)
print("Example 5: Batch processing")
print("=" * 60)

data_dir = Path("./agilent_data")
if data_dir.exists():
    d_folders = [f for f in data_dir.iterdir() if f.is_dir() and f.suffix.lower() == ".d"]

    print(f"Found {len(d_folders)} .D folders")

    for folder in d_folders[:3]:
        try:
            data = parser.parse(str(folder))
            print(f"✓ Parsed: {folder.name}")
            print(f"  Sample: {data.metadata.sample_name}")
            print(f"  Data points: {len(data.chromatogram.time)}")
            print(f"  Peaks: {len(data.peaks)}")
        except Exception as e:
            print(f"✗ Failed: {folder.name} - {e}")
else:
    print(f"Directory {data_dir} not found")

print("\n" + "=" * 60)
print("Agilent Parser Features:")
print("=" * 60)
print("""
The Agilent parser supports:

1. .D Folder Parsing (ChemStation/MassHunter):
   - Comprehensive metadata extraction from multiple text files
     * SAMPLE.TXT / SAMPLE.XML - sample information
     * ACQ.TXT / ACQMETH.TXT - acquisition method
     * INJINFO.TXT - injection details
     * *.REG files - registry-style metadata

   - Chromatogram extraction from binary files
     * *.CH files (FID, DAD, TCD, etc.)
     * DATA.MS files (mass spectrometry TIC)

   - Peak integration results
     * RESULTS.CSV parsing with flexible column names
     * REPORT.TXT parsing for peak tables

2. Individual .CH File Parsing:
   - Binary chromatogram data extraction
   - ChemStation signature detection
   - Automatic detector type recognition (FID, DAD, TCD)
   - Heuristic header size detection

3. .MS File Support:
   - Mass spectrometry data (basic TIC extraction)
   - Framework for future spectral data parsing

4. Intelligent Parsing:
   - Case-insensitive file detection
   - Multiple date format support
   - Flexible CSV column name matching
   - Graceful degradation on missing files

5. Comprehensive Logging:
   - Debug-level logging for troubleshooting
   - Warnings for missing data
   - Detailed error messages

Note: Agilent formats are proprietary and vary by instrument/software version.
This parser handles common cases but may not work with all variations.

If you encounter issues:
1. Enable debug logging: setup_logger(level=logging.DEBUG)
2. Share sample .D folder structure on GitHub issues
3. Check that your files match expected format
""")

print("\nParser Information:")
print(f"Vendor: {parser.vendor_name}")
print(f"Supported extensions: {', '.join(parser.supported_extensions)}")
print(f"Instrument types: {', '.join(parser.instrument_types)}")
