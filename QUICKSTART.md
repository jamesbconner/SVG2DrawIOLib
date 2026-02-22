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

# Split by folder (creates separate libraries per subdirectory)
SVG2DrawIOLib create icons/ -o FontAwesome.xml -R --split-by-folder

# With proportional scaling (max dimension 64px)
SVG2DrawIOLib create icons/ -o library.xml --max-size 64 -R

# With fixed dimensions
SVG2DrawIOLib create icons/*.svg -o library.xml -w 50 -h 50

# Enable color editing in DrawIO (fill colors)
SVG2DrawIOLib create icons/ -o library.xml --css

# Enable stroke color editing
SVG2DrawIOLib create icons/ -o library.xml --css --css-mode stroke

# Enable both fill and stroke color editing
SVG2DrawIOLib create icons/ -o library.xml --css --css-mode both --css-stroke-color "#0000FF"

# Target different SVG element types for color editing
# (useful when icons use <circle>, <rect>, etc. instead of <path>)
SVG2DrawIOLib create icons/ -o library.xml --css --tag circle
SVG2DrawIOLib create icons/ -o library.xml --css --tag rect
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

# Rename an icon
SVG2DrawIOLib rename my-library.xml -o old-name -n new-name

# Extract icons back to SVG files
SVG2DrawIOLib extract my-library.xml -o output-dir/

# Extract specific icons
SVG2DrawIOLib extract my-library.xml -o output-dir/ icon1 icon2

# List all icons in library
SVG2DrawIOLib list my-library.xml

# Inspect icon details
SVG2DrawIOLib inspect my-library.xml

# Inspect specific icons with SVG content
SVG2DrawIOLib inspect my-library.xml icon1 icon2 --show-svg

# Validate library integrity
SVG2DrawIOLib validate my-library.xml
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
  --css-mode TEXT         CSS mode: fill, stroke, or both (default: fill)
  --css-color TEXT        Default CSS fill color (default: #000000)
  --css-stroke-color TEXT Default CSS stroke color (default: #000000)
  --preserve-current-color/--no-preserve-current-color
                          Preserve currentColor values (default: true)
  -n, --namespace TEXT    XML namespace (default: http://www.w3.org/2000/svg)
  -t, --tag TEXT          SVG element type to target for CSS classes (default: path)
                          Common values: path, circle, rect, ellipse, line, polygon
                          Only affects CSS injection (requires --css flag)
  -R, --recursive         Recursively search directories for SVG files
  -S, --split-by-folder   Create separate libraries per subdirectory (requires -R)
  -v, --verbose           Enable debug logging
  -q, --quiet             Suppress output except errors
```

**About the --tag option:**
The `--tag` option specifies which SVG element type should receive CSS classes for color editing. Most icon libraries use `<path>` elements (the default), but some icons may use `<circle>`, `<rect>`, or other element types. Only elements matching the specified tag will be colorable in DrawIO. This option has no effect without the `--css` flag.

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
  --css-mode TEXT         CSS mode: fill, stroke, or both (default: fill)
  --css-color TEXT        Default CSS fill color (default: #000000)
  --css-stroke-color TEXT Default CSS stroke color (default: #000000)
  --preserve-current-color/--no-preserve-current-color
                          Preserve currentColor values (default: true)
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

#### extract
Extract icons from a DrawIO library back to individual SVG files.

```bash
SVG2DrawIOLib extract [OPTIONS] LIBRARY_FILE

Options:
  -o, --output-dir PATH   Output directory for SVG files (required)
  -i, --icons TEXT        Specific icon names to extract (optional)
  --overwrite             Overwrite existing SVG files
  -v, --verbose           Enable debug logging
  -q, --quiet             Suppress output except errors
```

#### rename
Rename an icon within a DrawIO library.

```bash
SVG2DrawIOLib rename [OPTIONS] LIBRARY_FILE

Options:
  -o, --old-name TEXT     Current icon name (required)
  -n, --new-name TEXT     New icon name (required)
  --overwrite             Overwrite if new name already exists
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

#### inspect
Display detailed information about icons in a library.

```bash
SVG2DrawIOLib inspect [OPTIONS] LIBRARY_FILE [ICON_NAMES]...

Options:
  --show-svg              Display decoded SVG content
  --json                  Output in JSON format
  -v, --verbose           Enable debug logging
  -q, --quiet             Suppress output except errors
```

#### validate
Validate DrawIO library file integrity.

```bash
SVG2DrawIOLib validate [OPTIONS] LIBRARY_FILE

Options:
  -v, --verbose           Enable debug logging
  -q, --quiet             Suppress output except errors
```

#### split-paths
Split compound SVG paths into separate path elements.

```bash
SVG2DrawIOLib split-paths [OPTIONS] SVG_FILE

Options:
  -o, --output PATH       Output SVG file path (required)
  -v, --verbose           Enable debug logging
  -q, --quiet             Suppress output except errors
```

## Web UI

### Installation
```bash
pip install "SVG2DrawIOLib[web]"
```

### Launch
```bash
svg2drawio web
# Opens http://127.0.0.1:8000 in your browser automatically
```

### Options
```bash
svg2drawio web --port 9000          # Use a different port
svg2drawio web --host 0.0.0.0       # Listen on all interfaces
svg2drawio web --no-browser         # Don't auto-open the browser
svg2drawio web --ui-dir /path/to/ui # Use a custom pre-built UI directory
```

### Tabs
| Tab | Equivalent CLI Command |
|-----|----------------------|
| Create | `svg2drawio create` |
| Manage → Add Icons | `svg2drawio add` |
| Manage → Remove Icons | `svg2drawio remove` |
| Manage → Rename Icon | `svg2drawio rename` |
| Extract | `svg2drawio extract` |
| Inspect | `svg2drawio inspect` |
| Validate | `svg2drawio validate` |
| Split Paths | `svg2drawio split-paths` |

---

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

### Web UI Development
```bash
# Install web dependencies and start FastAPI + Next.js dev servers
make dev-api    # FastAPI only on port 8000 (with --reload)
make dev-web    # Next.js dev server only (port 3000)

# Build the static export and copy into the Python package
make build-release   # Runs npm build + copies output to src/SVG2DrawIOLib/web/

# Build and launch the web UI from the source tree
make start-web
```

The `web-ui/` directory contains the Next.js frontend source. The built static export
is copied to `src/SVG2DrawIOLib/web/` (gitignored — generated artifact) for bundling
into the Python wheel via `make build-release`. The FastAPI server at
`SVG2DrawIOLib.api.main:app` serves both the API (`/api/*`) and the static UI (`/`).

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
    css_mode="both",  # Enable both fill and stroke color editing
    css_color="#000000",
    css_stroke_color="#0000FF",
    preserve_current_color=True,
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
from SVG2DrawIOLib.icon_analyzer import IconAnalyzer

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

# Rename an icon
metadata = manager.rename_icon(
    Path("my-library.xml"),
    old_name="old-icon-name",
    new_name="new-icon-name",
    overwrite=False
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

# Extract and analyze icons
analyzer = IconAnalyzer()
icons_data = analyzer.extract_icons(Path("my-library.xml"))
for icon_data in icons_data:
    print(f"Icon: {icon_data['name']}")
    print(f"  Dimensions: {icon_data['width']}x{icon_data['height']}")
    print(f"  Shape type: {icon_data['shape_type']}")
```

### Custom Dimensions
```python
from SVG2DrawIOLib.models import SVGDimensions

# Proportional scaling from max dimension
dims = SVGDimensions.from_max_dimension(
    max_dimension=64,
    aspect_ratio=2.0  # width/height ratio
)
print(f"Scaled to: {dims.width}x{dims.height}")  # 64x32

# Fixed dimensions
dims = SVGDimensions.from_fixed_dimensions(width=50, height=50)
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

The project follows a modular, class-based architecture with SOLID principles:

- **models.py**: Dataclasses for type-safe data structures
  - `SVGDimensions`: Width/height with scaling logic
  - `DrawIOIcon`: Icon representation with metadata
  - `SVGProcessingOptions`: Configuration for SVG processing (including CSS modes)
  - `LibraryMetadata`: Library file metadata

- **svg_processor.py**: `SVGProcessor` class for SVG operations
  - Load and parse SVG files
  - Add CSS classes for color editing (fill, stroke, or both modes)
  - Parse style attributes and handle special values (none, currentColor)
  - Calculate dimensions and scaling
  - Adjust viewBox to content bounds (with svgelements integration)
  - Convert to data URIs

- **library_manager.py**: `LibraryManager` class for library operations
  - Create new libraries
  - Load existing libraries
  - Add/remove/rename icons
  - List icons

- **icon_analyzer.py**: `IconAnalyzer` service for icon inspection
  - Extract icon content from libraries
  - Analyze SVG structure (CSS classes, inline styles)
  - Decode and decompress icon data

- **path_splitter.py**: `PathSplitter` class for SVG path operations
  - Split compound paths into separate elements
  - Detect and preserve nested paths (donut holes)
  - Generate unique CSS classes for split paths

- **library_validator.py**: `LibraryValidator` service for validation
  - Validate XML structure and JSON format
  - Check icon integrity (dimensions, encoding, compression)
  - Validate mxGraphModel structure
  - Verify SVG content (namespace, viewBox, empty detection)

- **cli/**: Modular CLI with dynamic command loading
  - `__init__.py`: Main entry point with auto-discovery and command groups
  - `helpers.py`: Shared utilities (console, logging)
  - Individual command files: `create.py`, `add.py`, `remove.py`, `list.py`, `extract.py`, `rename.py`, `inspect.py`, `validate.py`, `split_paths.py`
  - `create_helpers.py`: Business logic extracted from create command

**Command Groups:**
- **Library Management**: create, add, remove, extract, rename
- **Library Inspection**: list, inspect, validate
- **SVG Processing**: split-paths

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
