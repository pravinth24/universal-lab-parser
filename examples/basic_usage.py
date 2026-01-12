"""
Basic usage examples for Universal Lab Parser.

Run this script to see how to use the library.
"""

from universal_lab_parser import parse_file, batch_parse


def example_1_parse_single_file():
    """Example 1: Parse a single Waters file."""
    print("=" * 60)
    print("Example 1: Parse Single File")
    print("=" * 60)

    # Parse a Waters HPLC file
    # Note: Replace with actual file path
    filepath = "path/to/your/sample.arw"

    try:
        data = parse_file(filepath)

        # Print summary
        print(f"Sample: {data.metadata.sample_name}")
        print(f"Instrument: {data.metadata.instrument_model}")
        print(f"Run Date: {data.metadata.run_date}")
        print(f"Number of peaks: {len(data.peaks)}")

        # Export to CSV
        data.to_csv("output.csv")
        print("\n✓ Exported to output.csv")

    except FileNotFoundError:
        print(f"File not found: {filepath}")
        print("Replace with path to an actual data file to run this example")


def example_2_access_data():
    """Example 2: Access different parts of the data."""
    print("\n" + "=" * 60)
    print("Example 2: Access Parsed Data")
    print("=" * 60)

    filepath = "path/to/your/sample.arw"

    try:
        data = parse_file(filepath)

        # Access metadata
        print("\nMetadata:")
        print(f"  Instrument: {data.metadata.instrument_model}")
        print(f"  Method: {data.metadata.method_name}")
        print(f"  Runtime: {data.metadata.runtime_minutes} min")

        # Access chromatogram
        if data.chromatogram:
            print("\nChromatogram:")
            print(f"  Data points: {len(data.chromatogram.time)}")
            print(f"  Time range: {min(data.chromatogram.time):.2f} - "
                  f"{max(data.chromatogram.time):.2f} {data.chromatogram.time_units}")

        # Access peaks
        if data.peaks:
            print("\nPeaks:")
            for i, peak in enumerate(data.peaks[:5], 1):  # First 5 peaks
                print(f"  Peak {i}: RT={peak.retention_time:.2f} min, "
                      f"Area={peak.area}")

    except FileNotFoundError:
        print("Replace with path to an actual data file to run this example")


def example_3_batch_processing():
    """Example 3: Process multiple files."""
    print("\n" + "=" * 60)
    print("Example 3: Batch Processing")
    print("=" * 60)

    directory = "path/to/your/data/folder"

    try:
        # Parse all .arw files in directory
        results = batch_parse(directory, pattern="*.arw")

        print(f"Parsed {len(results)} files\n")

        # Process each result
        for data in results:
            print(f"Sample: {data.metadata.sample_name}")
            print(f"  Peaks: {len(data.peaks)}")
            print(f"  Runtime: {data.metadata.runtime_minutes} min\n")

            # Export each to separate CSV
            output_name = f"{data.metadata.sample_name}.csv"
            data.to_csv(output_name)

        print(f"✓ Exported {len(results)} files")

    except FileNotFoundError:
        print("Replace with path to an actual directory to run this example")


def example_4_convert_formats():
    """Example 4: Convert to different formats."""
    print("\n" + "=" * 60)
    print("Example 4: Format Conversion")
    print("=" * 60)

    filepath = "path/to/your/sample.arw"

    try:
        data = parse_file(filepath)

        # Export to multiple formats
        data.to_csv("output.csv", include_metadata=True)
        print("✓ Exported to CSV")

        data.to_json("output.json")
        print("✓ Exported to JSON")

        try:
            data.to_parquet("output.parquet", normalize=True)
            print("✓ Exported to Parquet (ML-ready)")
        except ImportError:
            print("⚠ Parquet export requires pyarrow: pip install pyarrow")

    except FileNotFoundError:
        print("Replace with path to an actual data file to run this example")


def example_5_work_with_pandas():
    """Example 5: Use with pandas for analysis."""
    print("\n" + "=" * 60)
    print("Example 5: Pandas Integration")
    print("=" * 60)

    try:
        import pandas as pd
        from universal_lab_parser import parse_file

        filepath = "path/to/your/sample.arw"

        try:
            data = parse_file(filepath)

            # Convert chromatogram to DataFrame
            if data.chromatogram:
                df = data.chromatogram.to_dataframe()
                print("\nChromatogram DataFrame:")
                print(df.head())
                print(f"\nShape: {df.shape}")

                # Basic statistics
                print("\nSignal Statistics:")
                print(df['signal'].describe())

            # Convert peaks to DataFrame
            if data.peaks:
                peaks_df = pd.DataFrame([p.model_dump() for p in data.peaks])
                print("\nPeaks DataFrame:")
                print(peaks_df.head())

        except FileNotFoundError:
            print("Replace with path to an actual data file to run this example")

    except ImportError:
        print("This example requires pandas: pip install pandas")


if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "Universal Lab Parser Examples" + " " * 18 + "║")
    print("╚" + "═" * 58 + "╝")

    # Run examples
    example_1_parse_single_file()
    example_2_access_data()
    example_3_batch_processing()
    example_4_convert_formats()
    example_5_work_with_pandas()

    print("\n" + "=" * 60)
    print("For more examples, see:")
    print("  - examples/batch_processing.py")
    print("  - examples/notebooks/")
    print("  - Documentation: https://github.com/yourusername/universal-lab-parser")
    print("=" * 60 + "\n")
