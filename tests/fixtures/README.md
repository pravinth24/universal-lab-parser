# Test Fixtures

This directory contains sample data files for testing parsers.

## Contributing Sample Files

We need example files from various instruments to develop and test parsers!

### How to Contribute Sample Files

1. **Anonymize your data:**
   - Remove or change sample names to generic names
   - Remove operator names
   - Remove any proprietary/confidential method information

2. **What we need:**
   - File name/extension
   - Instrument vendor and model
   - Software version used to create the file
   - Brief description (e.g., "HPLC run with 3 peaks")

3. **How to share:**
   - For small files (<10MB): Attach to a GitHub issue
   - For large files: Share via Google Drive/Dropbox link
   - Email: [your.email@example.com]

### Supported File Types

We're actively seeking samples for:

**High Priority:**
- Waters .arw files (Empower/Millennium)
- Waters .raw folders
- Agilent .d folders (ChemStation)
- Thermo Fisher .raw files (Xcalibur)

**Also Interested:**
- Shimadzu .lcd files
- PerkinElmer files
- Bruker files
- AB Sciex files

## Current Fixtures

(None yet - help us by contributing!)

### Example File Structure

```
tests/fixtures/
├── waters/
│   ├── sample_hplc_001.arw
│   ├── sample_uplc_002.arw
│   └── README.md
├── agilent/
│   ├── sample_gc_001.d/
│   └── README.md
└── thermo/
    ├── sample_ms_001.raw
    └── README.md
```

## Legal Note

By contributing sample files, you confirm:
- You have permission to share these files
- Files contain no confidential or proprietary information
- Files are suitable for inclusion in an open-source project

Files will be used solely for testing and development purposes.

## Questions?

Open an issue or email [your.email@example.com]
