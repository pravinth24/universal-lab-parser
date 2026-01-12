# Contributing to Universal Lab Parser

Thank you for considering contributing! This project only succeeds with help from the community.

## How You Can Help

### 1. Share Sample Data Files

We need example instrument files to develop and test parsers.

**How to share:**
- Open an issue titled "Sample files: [Instrument Type]"
- Attach anonymized/example files (remove sensitive sample info)
- Include: instrument model, software version, file format

**Need help anonymizing?** We can sign an NDA or help you sanitize files.

### 2. Request New Instrument Support

Don't see your instrument? Let us know!

**Open an issue with:**
- Instrument vendor and model
- File extension/format
- Software used to generate files
- Any documentation you have about the format

### 3. Contribute Code

#### Areas Needing Help

**High Priority:**
- Complete Waters .arw binary parser
- Agilent ChemStation .d folder parser
- Thermo .raw file parser
- Peak detection algorithms
- AnIML export implementation

**Good First Issues:**
- Add file validation
- Improve error messages
- Write documentation
- Add unit tests
- Create example notebooks

#### Development Setup

```bash
# Clone the repo
git clone https://github.com/pravinth24/universal-lab-parser.git
cd universal-lab-parser

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black universal_lab_parser/
isort universal_lab_parser/
```

#### Code Standards

- **Python 3.8+** compatible
- **Type hints** for all functions
- **Docstrings** for public APIs
- **Tests** for new functionality
- **Black** for formatting (line length: 100)
- **No breaking changes** without discussion

#### Adding a New Parser

1. **Create parser file:** `universal_lab_parser/parsers/vendor_name.py`

```python
from universal_lab_parser.core.base_parser import BaseParser
from universal_lab_parser.core.data_model import LabData

class VendorParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.vendor_name = "Vendor"
        self.instrument_types = ["Type1", "Type2"]
        self.supported_extensions = [".ext"]

    def can_parse(self, filepath: str) -> bool:
        # Implementation
        pass

    def parse(self, filepath: str, **kwargs) -> LabData:
        # Implementation
        pass
```

2. **Register parser:** Add to `parsers/__init__.py`
3. **Add tests:** Create `tests/test_vendor_parser.py`
4. **Update README:** Add to supported instruments table
5. **Submit PR:** With sample files if possible

#### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_waters.py

# With coverage
pytest --cov=universal_lab_parser --cov-report=html
```

### 4. Improve Documentation

Documentation lives in `docs/` and the README.

**Needed:**
- Tutorials for specific use cases
- API reference improvements
- "How instrument X stores data" explainers
- Jupyter notebook examples

### 5. Report Bugs

**Good bug reports include:**
- Instrument type and file format
- Full error message and traceback
- Sample file (if shareable)
- Expected vs. actual behavior
- Environment (OS, Python version, package versions)

**Template:**

```markdown
### Bug Description
[Clear description of the issue]

### To Reproduce
[Steps to reproduce the behavior]

### Expected Behavior
[What you expected to happen]

### Environment
- OS: [e.g., macOS 13.2]
- Python: [e.g., 3.10.5]
- Package version: [e.g., 0.1.0]
- Instrument: [e.g., Waters ACQUITY]
```

## Development Process

### Branching Strategy

- `main` - stable, released code
- `develop` - active development
- `feature/*` - new features
- `fix/*` - bug fixes

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add Agilent ChemStation parser
fix: correct peak area calculation in Waters parser
docs: add tutorial for batch processing
test: add tests for file detection
```

### Pull Request Process

1. **Fork the repo** and create your branch from `develop`
2. **Write tests** for new functionality
3. **Update documentation** (README, docstrings)
4. **Run tests and linting:**
   ```bash
   pytest
   black universal_lab_parser/
   flake8 universal_lab_parser/
   ```
5. **Submit PR** with clear description:
   - What does this PR do?
   - Why is it needed?
   - How was it tested?
   - Any breaking changes?

### Review Process

- Maintainers will review within 1 week
- Address feedback in comments
- Once approved, we'll merge and release

## Reverse Engineering File Formats

Many instrument formats are undocumented. Here's how to approach them:

### Tools You'll Need

- **Hex editor:** [HxD](https://mh-nexus.de/en/hxd/) (Windows), [Hex Fiend](https://hexfiend.com/) (Mac)
- **Binary diff:** Compare two similar files
- **Strings:** `strings filename.raw` to extract readable text
- **File:** `file filename.raw` to detect format

### Reverse Engineering Process

1. **Collect samples:** Get multiple files with known differences
2. **Hex dump analysis:** Look for patterns, headers, magic numbers
3. **Differential analysis:** Compare two files differing by one parameter
4. **Instrument software debugging:** Run software in debugger, watch I/O
5. **Community knowledge:** Search forums, academic papers
6. **Incremental implementation:** Start with metadata, then chromatogram, then peaks

### Example: Finding the Data Block

```python
# Read binary file
with open("sample.raw", "rb") as f:
    data = f.read()

# Look for patterns
import re
pattern = re.compile(b'\x00\x00\x80\x3f')  # Common float pattern
matches = pattern.finditer(data)

for match in matches:
    offset = match.start()
    print(f"Found pattern at offset: {offset}")
```

### Documentation is Helpful

Check these resources:
- Vendor SDK documentation (if available)
- Academic papers mentioning file formats
- GitHub repos with similar parsers
- Chromatography forums (Chromforum.org)

## Community Guidelines

- **Be respectful** and professional
- **Assume good intentions**
- **Ask questions** if unclear
- **Help others** when you can
- **Share knowledge** - document what you learn

## Legal Considerations

### Reverse Engineering

Reverse engineering for interoperability is legal in most jurisdictions:
- **US:** Protected under fair use (Sony v. Connectix, Sega v. Accolade)
- **EU:** Explicitly allowed under Copyright Directive Article 6
- **Goal:** Enable data access, not circumvent protection

### Contributions

- By contributing, you agree to license your work under the MIT License
- You retain copyright but grant broad permissions
- Ensure you have rights to contribute (employer agreements, etc.)

## Questions?

- **General questions:** [Open a Discussion](../../discussions)
- **Bug reports:** [File an Issue](../../issues)
- **Security issues:** Email [144460619+pravinth24@users.noreply.github.com]
- **Want to chat?** [Discord/Slack link] (coming soon)

---

**Thank you for contributing! Together we're making lab data accessible to everyone.** 🚀
