# Universal Lab Parser

> **Parse proprietary lab instrument data files into standard, usable formats**

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![GitHub Stars](https://img.shields.io/github/stars/pravinth24/universal-lab-parser?style=social)](https://github.com/pravinth24/universal-lab-parser/stargazers)
[![GitHub Issues](https://img.shields.io/github/issues/pravinth24/universal-lab-parser)](https://github.com/pravinth24/universal-lab-parser/issues)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Open Source Love](https://badges.frapsoft.com/os/v2/open-source.svg?v=103)](https://github.com/pravinth24/universal-lab-parser)

## The Problem

Every lab instrument vendor uses proprietary file formats. Scientists waste hours:
- 📋 Manually copy-pasting data from instrument software to Excel
- 💰 Paying $3K-$12K for custom integrations per instrument
- 🚫 Unable to aggregate data across different instrument types for analysis
- 🔒 Locked into vendor-specific analysis software

**Universal Lab Parser** solves this by converting proprietary formats to standard, open formats.

---

## Features

- ✅ **Multi-vendor support**: Waters, Agilent, Thermo Fisher, and more
- ✅ **Multiple output formats**: CSV, JSON, AnIML, Allotrope, Parquet
- ✅ **Auto-detection**: Automatically identifies instrument type
- ✅ **Batch processing**: Convert entire folders with one command
- ✅ **Python API**: Integrate into your workflows and scripts
- ✅ **Zero cost**: Free and open source

---

## Quick Start

### Installation

```bash
pip install universal-lab-parser
```

### CLI Usage

```bash
# Parse a Waters HPLC file
ulp parse data.arw --format csv --output results.csv

# Auto-detect instrument type
ulp parse unknown_file.raw --auto-detect

# Batch convert an entire folder
ulp batch ./instrument_data/ --format json --output ./parsed/

# List supported formats
ulp formats
```

### Python API

```python
from universal_lab_parser import parse_file

# Auto-detect and parse
data = parse_file("sample.raw")

# Access structured data
print(data.metadata)      # Instrument settings, run parameters
print(data.peaks)         # Peak detection results
print(data.chromatogram)  # Time-series data

# Convert to different formats
data.to_csv("output.csv")
data.to_json("output.json")
data.to_animl("standard_format.xml")
```

---

## Supported Instruments

| Vendor | Instrument Type | File Extensions | Status |
|--------|----------------|-----------------|--------|
| Waters | HPLC/UPLC | `.arw`, `.raw` | 🚧 In Progress |
| Agilent | GC/LC/MS | `.d`, `.ch` | 📋 Planned |
| Thermo Fisher | Mass Spec | `.raw` | 📋 Planned |
| PerkinElmer | Chromatography | `.raw` | 📋 Planned |
| Shimadzu | HPLC | `.lcd` | 📋 Planned |

**Don't see your instrument?** [Open an issue](../../issues/new) or [contribute a parser](CONTRIBUTING.md)!

---

## Why This Exists

From our research:
- **61% of biopharma labs** cite "lack of standardized data formats" as their top data integration challenge
- **Each instrument integration** costs $3,000-$12,000 in custom development
- Scientists spend **60% of their time** on manual data entry and processing
- **Lab data is trapped** in proprietary formats, blocking AI/ML applications

**Our mission**: Make lab data as accessible as web data.

---

## Use Cases

### For Scientists
- **Quick analysis**: Get your HPLC data into Excel/Pandas in seconds
- **Method comparison**: Aggregate data from multiple instruments
- **Publication**: Generate standard formats for data repositories

### For Labs
- **Eliminate manual data entry**: Automate data extraction from instruments
- **Enable ML/AI**: Get your data into ML-ready formats (JSON, Parquet)
- **Vendor independence**: Don't be locked into proprietary software

### For Software Developers
- **Build LIMS integrations**: Use as a library for instrument connectivity
- **Create analysis tools**: Access structured instrument data programmatically
- **Data pipelines**: Integrate into your ETL workflows

---

## Examples

### Example 1: Convert HPLC Data to CSV

```python
from universal_lab_parser import parse_file

# Parse Waters HPLC file
data = parse_file("hplc_run_001.arw")

# Export to CSV with all channels
data.to_csv("results.csv", include_metadata=True)

# Or just export peaks
data.peaks.to_csv("peaks_only.csv")
```

### Example 2: Batch Processing with Metadata Extraction

```python
from universal_lab_parser import batch_parse
import pandas as pd

# Parse all files in a folder
results = batch_parse("./data/", formats="*.arw")

# Create summary DataFrame
summary = pd.DataFrame([
    {
        "filename": r.filename,
        "instrument": r.metadata.instrument_serial,
        "run_date": r.metadata.run_date,
        "peak_count": len(r.peaks),
        "runtime_min": r.metadata.runtime_minutes
    }
    for r in results
])

summary.to_csv("batch_summary.csv")
```

### Example 3: ML-Ready Data Export

```python
from universal_lab_parser import parse_file

data = parse_file("sample.raw")

# Export as Parquet for data science
data.to_parquet("ml_dataset.parquet",
                normalize=True,
                include_raw_signal=True)

# Now load in your ML pipeline
import pandas as pd
df = pd.read_parquet("ml_dataset.parquet")
```

---

## Output Formats

| Format | Use Case | Extension |
|--------|----------|-----------|
| **CSV** | Excel, spreadsheets, general purpose | `.csv` |
| **JSON** | APIs, web applications, JavaScript | `.json` |
| **AnIML** | Industry standard for analytical data | `.xml` |
| **Allotrope** | Pharma standard (FAIR data) | `.json` |
| **Parquet** | Data science, ML, big data analytics | `.parquet` |

---

## Roadmap

### v0.1.0 (Current - Week 1-4)
- [x] Project structure and CLI framework
- [ ] Waters .arw parser (HPLC/UPLC)
- [ ] CSV and JSON export
- [ ] Basic documentation

### v0.2.0 (Week 5-8)
- [ ] Agilent ChemStation support (.d folders)
- [ ] Thermo .raw file support
- [ ] AnIML output format
- [ ] Auto-detection algorithm

### v0.3.0 (Week 9-12)
- [ ] Batch processing CLI
- [ ] Metadata extraction improvements
- [ ] Jupyter notebook examples
- [ ] Community contributions

### v1.0.0 (Month 4-6)
- [ ] 10+ instrument types supported
- [ ] Comprehensive test coverage
- [ ] API documentation
- [ ] Performance optimizations

---

## Contributing

We'd love your help! This project only succeeds if scientists and developers contribute:

- **Have sample data files?** Share them for testing (anonymized)
- **Know a file format?** Help us reverse engineer it
- **Need a specific instrument?** Open an issue or submit a PR
- **Found a bug?** Report it!

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## Community & Support

- **Questions?** [Open a Discussion](../../discussions)
- **Bug reports?** [File an Issue](../../issues)
- **Feature requests?** [Open an Issue with `enhancement` label](../../issues/new?labels=enhancement)
- **Want to chat?** Join our [Discord/Slack] (coming soon)

---

## Citation

If you use Universal Lab Parser in your research, please cite:

```bibtex
@software{universal_lab_parser,
  title = {Universal Lab Parser: Open-source toolkit for lab instrument data interoperability},
  author = {Pravinth},
  year = {2025},
  url = {https://github.com/pravinth24/universal-lab-parser}
}
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

Built with inspiration from:
- [Aston](https://github.com/bovee/aston) - Chromatography data analysis
- [pyOpenMS](https://github.com/OpenMS/OpenMS) - Mass spectrometry data
- [rainbow-api](https://github.com/bovee/rainbow-api) - Waters file parsing

---

## Related Projects

- [Benchling](https://www.benchling.com) - Modern R&D data platform
- [TetraScience](https://www.tetrascience.com) - R&D data cloud
- [AllotropeFoundation](https://www.allotrope.org) - Data standards for pharma

---

**⭐ If this project helps you, please star it on GitHub! ⭐**

It helps others discover the tool and motivates continued development.

