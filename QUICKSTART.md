# Quick Start Guide

## For Users

### Installation
```bash
pip install SVG2DrawIOLib
```

### Basic Usage

#### Create a New Library
```bash
# Convert individual SVG files
SVG2DrawIOLib create icon.svg -o my-library.xml
SVG2DrawIOLib create icon1.svg icon2.svg icon3.svg -o my-library.xml

# Convert all SVGs in a directory
SVG2DrawIOLib create icons/ -o my-library.xml

# Convert all SVGs in a directory and subdirectories (recursive)
SVG2DrawIOLib create icons/ -o my-library.xml --recursive

# With proportional scaling (max dimension 64px)
SVG2DrawIOLib create icons/ -o library.xml --max-size 64 -R

# With fixed dimensions
SVG2DrawIOLib create icons/*.svg -o library.xml -w 50 -h 50

# Enable color editing in DrawIO
SVG2DrawIOLib create icons/ -o library.xml --css
```

#### Manage Existing Libraries
```bash
# Add individual icons to existing library
SVG2DrawIOLib add my-library.xml new-icon1.svg new-icon2.svg

# Add all SVGs from a directory
SVG2DrawIOLib add my-library.xml icons/

# Add all SVGs from directory and subdirectories
SVG2DrawIOLib add my-library.xml icons/ --recursive

# Replace existing icons with same names
SVG2DrawIOLib add my-library.xml icons/ --replace

# Add duplicates with modified names (icon_2, icon_3, etc.)
SVG2DrawIOLib add my-library.xml icons/ --add-dupes

# Add with fixed dimensions
SVG2DrawIOLib add my-library.xml icons/ -w 50 -h 50

# Remove icons by name
SVG2DrawIOLib remove my-library.xml old-icon1 old-icon2

# List all icons in library
SVG2DrawIOLib list my-library.xml
```

### CLI Commands

#### create
Create a new DrawIO library from SVG files or directories.

```bash
SVG2DrawIOLib create [OPTIONS] PATHS...

Options:
  -o, --output PATH       Output library file path (required)
  -s, --max-size FLOAT    Maximum dimension (proportional scaling)
  -w, --width FLOAT       Fixed width in pixels
  -h, --height FLOAT      Fixed height in pixels
  -c, --css               Add CSS classes for color editing
  --css-color TEXT        Default CSS fill color (default: #000000)
  -n, --namespace TEXT    XML namespace (default: http://www.w3.org/2000/svg)
  -t, --tag TEXT          XML tag for CSS classes (default: path)
  -R, --recursive         Recursively search directories for SVG files
  -v, --verbose           Enable debug logging
  -q, --quiet             Suppress output except errors
```

#### add
Add SVG icons to an existing DrawIO library.

```bash
SVG2DrawIOLib add [OPTIONS] LIBRARY_FILE PATHS...

Options:
  -r, --replace           Replace icons with duplicate names
  -d, --add-dupes         Add duplicate icons with modified names
  -s, --max-size FLOAT    Maximum dimension for new icons
  -w, --width FLOAT       Fixed width in pixels
  -h, --height FLOAT      Fixed height in pixels
  -c, --css               Add CSS classes to new icons
  -R, --recursive         Recursively search directories for SVG files
  -v, --verbose           Enable debug logging
  -q, --quiet             Suppress output except errors
```

#### remove
Remove icons from a DrawIO library by name.

```bash
SVG2DrawIOLib remove [OPTIONS] LIBRARY_FILE ICON_NAMES...

Options:
  -v, --verbose           Enable debug logging
  -q, --quiet             Suppress output except errors
```

#### list
List all icons in a DrawIO library.

```bash
SVG2DrawIOLib list [OPTIONS] LIBRARY_FILE

Options:
  -v, --verbose           Enable debug logging
  -q, --quiet             Suppress output except errors
```

## For Developers

### Setup
```bash
# Clone repository
git clone <repo-url>
cd SVG2DrawIOLib

# Install uv (if needed)
pip install uv

# Create virtual environment and install
uv venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Development Commands
```bash
make test       # Run tests
make cov        # Run tests with coverage
make lint       # Run linting
make format     # Format code
make type       # Type checking
make security   # Security scanning
make build      # Build package
make check-dist # Build and check distribution
make all        # Run all checks
make clean      # Clean build artifacts
```

### Running Tests
```bash
# All tests
uv run pytest tests/

# Specific test file
uv run pytest tests/test_cli.py

# With coverage
uv run pytest --cov=src/SVG2DrawIOLib tests/

# Verbose
uv run pytest tests/ -v
```

### Code Quality
```bash
# Format code
uv run ruff format src tests

# Lint code
uv run ruff check src tests

# Fix linting issues
uv run ruff check --fix src tests

# Type check
uv run mypy src

# Security scan
uv run bandit -r src -ll
```

### Pre-commit
```bash
# Run all hooks manually
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
```

## Python API

### Basic Example
```python
from pathlib import Path
from SVG2DrawIOLib.svg_processor import SVGProcessor
from SVG2DrawIOLib.library_manager import LibraryManager
from SVG2DrawIOLib.models import SVGProcessingOptions

# Create processor with options
options = SVGProcessingOptions(
    add_css=True,
    css_color="#000000",
    xml_namespace="http://www.w3.org/2000/svg",
    css_tag="path"
)
processor = SVGProcessor(options)

# Process a single SVG file
icon = processor.process_svg_file(
    Path("icon.svg"),
    max_dimension=64  # Proportional scaling
)

# Create library
manager = LibraryManager()
metadata = manager.create_library([icon], Path("output.xml"))

print(f"Created library with {metadata.icon_count} icons")
```

### Batch Processing
```python
from pathlib import Path
from SVG2DrawIOLib.svg_processor import SVGProcessor
from SVG2DrawIOLib.library_manager import LibraryManager
from SVG2DrawIOLib.models import SVGProcessingOptions

# Setup
options = SVGProcessingOptions(add_css=True)
processor = SVGProcessor(options)
icons = []

# Process all SVG files in directory
for svg_path in Path("icons").glob("*.svg"):
    icon = processor.process_svg_file(svg_path, max_dimension=64)
    icons.append(icon)

# Create library
manager = LibraryManager()
metadata = manager.create_library(icons, Path("library.xml"))

print(f"Created library with {metadata.icon_count} icons")
```

### Working with Existing Libraries
```python
from pathlib import Path
from SVG2DrawIOLib.library_manager import LibraryManager
from SVG2DrawIOLib.svg_processor import SVGProcessor
from SVG2DrawIOLib.models import SVGProcessingOptions

manager = LibraryManager()

# Load existing library
metadata = manager.load_library(Path("my-library.xml"))
print(f"Library has {metadata.icon_count} icons")

# Add new icons
processor = SVGProcessor(SVGProcessingOptions())
new_icon = processor.process_svg_file(Path("new-icon.svg"))
metadata = manager.add_icons_to_library(
    Path("my-library.xml"),
    [new_icon],
    replace_duplicates=False
)

# Remove icons
metadata = manager.remove_icons_from_library(
    Path("my-library.xml"),
    ["old-icon-name"]
)

# List icons
icon_names = manager.list_icons(Path("my-library.xml"))
for name in icon_names:
    print(name)
```

### Custom Dimensions
```python
from SVG2DrawIOLib.models import SVGDimensions

# Proportional scaling from max dimension
dims = SVGDimensions.from_max_dimension(
    original_width=100,
    original_height=200,
    max_dimension=64
)
print(f"Scaled to: {dims.width}x{dims.height}")  # 32x64

# Fixed dimensions
dims = SVGDimensions(width=50, height=50)
```

## Common Tasks

### Add New CLI Command
1. Create new file in `src/SVG2DrawIOLib/cli/` (e.g., `mycommand.py`)
2. Define function with same name as file: `def mycommand():`
3. Decorate with `@rc.command()` and add options with `@rc.option()`
4. Command will be auto-discovered and registered
5. See `CLI_STRUCTURE.md` for detailed guide

### Add New Test
1. Open appropriate test file in `tests/`
2. Add test function with `test_` prefix
3. Run `uv run pytest tests/` to verify

### Fix Linting Issues
```bash
# Auto-fix most issues
uv run ruff check --fix src tests

# Format code
uv run ruff format src tests
```

### Update Dependencies
```bash
# Edit pyproject.toml
# Then reinstall
uv pip install -e ".[dev]"
```

### Create Release
1. Update version in `src/SVG2DrawIOLib/__about__.py`
2. Update `CHANGELOG.md` with release notes
3. Run `make all` to verify quality
4. Commit changes
5. Tag release: `git tag v1.0.1`
6. Push: `git push && git push --tags`
7. GitHub Actions will build and publish to PyPI

## Troubleshooting

### Import Error
```bash
# Reinstall package
uv pip install -e .
```

### Tests Failing
```bash
# Run with verbose output
uv run pytest tests/ -v

# Run specific test
uv run pytest tests/test_cli.py::TestCreateCommand::test_create_single_file -v
```

### Type Errors
```bash
# Check specific file
uv run mypy src/SVG2DrawIOLib/svg_processor.py

# Check all
uv run mypy src
```

### Pre-commit Issues
```bash
# Update hooks
pre-commit autoupdate

# Clear cache
pre-commit clean

# Reinstall
pre-commit install --install-hooks
```

### Colors Not Showing in CLI
The CLI uses rich-click for colorful output. If colors aren't showing:
- Ensure terminal supports ANSI colors
- Check that `rich-click` is installed: `uv pip list | grep rich-click`
- Try running with `--help` to see formatted output

## Architecture Overview

The project follows a modular, class-based architecture:

- **models.py**: Dataclasses for type-safe data structures
  - `SVGDimensions`: Width/height with scaling logic
  - `DrawIOIcon`: Icon representation with metadata
  - `SVGProcessingOptions`: Configuration for SVG processing
  - `LibraryMetadata`: Library file metadata

- **svg_processor.py**: `SVGProcessor` class for SVG operations
  - Load and parse SVG files
  - Add CSS classes for color editing
  - Calculate dimensions and scaling
  - Convert to data URIs

- **library_manager.py**: `LibraryManager` class for library operations
  - Create new libraries
  - Load existing libraries
  - Add/remove icons
  - List icons

- **cli/**: Modular CLI with dynamic command loading
  - `__init__.py`: Main entry point with auto-discovery
  - `helpers.py`: Shared utilities (console, logging)
  - Individual command files: `create.py`, `add.py`, `remove.py`, `list.py`

See `ARCHITECTURE.md` for detailed architecture documentation.

## Resources

- [Click Documentation](https://click.palletsprojects.com/)
- [Rich-Click Documentation](https://github.com/ewels/rich-click)
- [Rich Documentation](https://rich.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Pytest Documentation](https://docs.pytest.org/)
- [DrawIO Documentation](https://www.diagrams.net/doc/)
- [UV Documentation](https://docs.astral.sh/uv/)

## Getting Help

1. Check this guide and `ARCHITECTURE.md`
2. Review test files for usage examples
3. Run commands with `--help` for detailed options
4. Check `CLI_STRUCTURE.md` for CLI development guide
5. Open an issue on GitHub
