"""
Quick test script to validate parsers work correctly.

This script tests basic functionality of all parsers.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import lab_parser as lp


def test_biotek_parser():
    """Test BioTek parser."""
    print("\n=== Testing BioTek Parser ===")

    filepath = Path(__file__).parent / "sample_data" / "biotek_sample.csv"

    if not filepath.exists():
        print(f"❌ Sample file not found: {filepath}")
        return False

    try:
        # Test auto-detection
        detected = lp.detect_instrument(filepath)
        print(f"✓ Auto-detected instrument: {detected}")

        # Test parsing
        df = lp.read(filepath)
        print(f"✓ Parsed {len(df)} measurements")
        print(f"✓ Columns: {list(df.columns)}")
        print(f"✓ Wells: {df['well'].nunique()} unique wells")
        print(f"\nFirst few rows:")
        print(df.head())

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_list_instruments():
    """Test list_instruments function."""
    print("\n=== Testing list_instruments() ===")

    try:
        instruments = lp.list_instruments()
        print(f"✓ Found {len(instruments)} supported instruments:")
        for key, desc in instruments.items():
            print(f"  - {key}: {desc}")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Lab Parser Test Suite")
    print("=" * 60)

    results = []

    # Test list instruments
    results.append(("list_instruments", test_list_instruments()))

    # Test BioTek parser
    results.append(("BioTek parser", test_biotek_parser()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
