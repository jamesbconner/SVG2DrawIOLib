# Architecture Overview

This document describes the modular architecture of SVG2DrawIOLib.

## Architecture Principles

### 1. Separation of Concerns
- **Models**: Data structures and validation
- **Processors**: Business logic for SVG processing
- **Managers**: Library file management
- **CLI**: User interface layer

### 2. Type Safety
- Full type annotations with mypy
- Dataclasses for structured data
- No implicit type conversions

### 3. Testability
- Dependency injection
- Clear interfaces
- 84% test coverage (51 tests)

## Module Structure

```
src/SVG2DrawIOLib/
├── __init__.py              # Public API exports
├── __about__.py             # Version information
├── models.py                # Data models (dataclasses)
├── svg_processor.py         # SVG processing logic
├── library_manager.py       # Library file management
└── cli/                     # Modular CLI with dynamic loading
    ├── __init__.py          # CLI entry point with dynamic command discovery
    ├── helpers.py           # Shared CLI utilities
    ├── create.py            # Create command
    ├── add.py               # Add command
    ├── remove.py            # Remove command
    └── list.py              # List command
```

## Core Components

### 1. Data Models (`models.py`)

#### SVGDimensions
Represents icon dimensions with scaling support.

```python
@dataclass
class SVGDimensions:
    width: float
    height: float

    @classmethod
    def from_max_dimension(cls, max_dimension: float, aspect_ratio: float)

    @classmethod
    def from_fixed_dimensions(cls, width: float, height: float)
```

**Key Features:**
- Proportional scaling based on aspect ratio
- Automatic calculation of longest dimension
- Support for fixed dimensions

#### DrawIOIcon
Represents a single icon in a DrawIO library.

```python
@dataclass
class DrawIOIcon:
    name: str
    xml_data: bytes
    dimensions: SVGDimensions

    def to_dict(self) -> dict[str, str | int | float]
```

#### SVGProcessingOptions
Configuration for SVG processing.

```python
@dataclass
class SVGProcessingOptions:
    add_css: bool = False
    css_color: str = "#000000"
    xml_namespace: str = "http://www.w3.org/2000/svg"
    css_tag: str = "path"

    @property
    def namespaced_tag(self) -> str
```

#### LibraryMetadata
Metadata about a DrawIO library.

```python
@dataclass
class LibraryMetadata:
    name: str
    icon_count: int
    source_files: list[Path]
```

### 2. SVG Processor (`svg_processor.py`)

Handles all SVG file processing operations.

```python
class SVGProcessor:
    def __init__(self, options: SVGProcessingOptions)

    def load_svg(self, filepath: Path) -> ET.ElementTree
    def add_css_classes(self, svg_tree: ET.ElementTree) -> ET.ElementTree
    def get_svg_dimensions(self, svg_tree: ET.ElementTree) -> tuple[float, float] | None
    def calculate_dimensions(self, svg_tree: ET.ElementTree, max_dimension: float | None) -> SVGDimensions
    def svg_to_data_uri(self, svg_tree: ET.ElementTree) -> str
    def process_svg_file(self, filepath: Path, max_dimension: float | None) -> DrawIOIcon
```

**Key Features:**
- Automatic dimension extraction from SVG
- Proportional scaling support
- CSS class injection for color editing
- Data URI generation
- mxGraphModel creation
- Compression and encoding

### 3. Library Manager (`library_manager.py`)

Manages DrawIO library files.

```python
class LibraryManager:
    def create_library(self, icons: list[DrawIOIcon], output_path: Path) -> LibraryMetadata
    def load_library(self, library_path: Path) -> list[DrawIOIcon]
    def add_icons_to_library(self, library_path: Path, new_icons: list[DrawIOIcon], replace_duplicates: bool) -> LibraryMetadata
    def remove_icons_from_library(self, library_path: Path, icon_names: list[str]) -> LibraryMetadata
    def list_icons(self, library_path: Path) -> list[str]
```

**Key Features:**
- Create new libraries
- Load existing libraries
- Add icons (with duplicate handling)
- Remove icons by name
- List all icons
- Automatic alphabetical sorting

### 4. CLI (`cli/`)

Modular command-line interface with dynamic command loading.

**Structure:**
```python
# cli/__init__.py - Entry point with dynamic discovery
@click.group()
def cli()

# Dynamic command loading
for filepath in COMMAND_DIR.iterdir():
    if filepath.suffix == ".py" and filepath.stem not in ("__init__", "helpers"):
        module = importlib.import_module(f"SVG2DrawIOLib.cli.{filepath.stem}")
        cli_function = getattr(module, filepath.stem, None)
        if cli_function and callable(cli_function):
            cli.add_command(cli_function)
```

**Commands:**
- `cli/create.py` - Create new library
- `cli/add.py` - Add icons to library
- `cli/remove.py` - Remove icons from library
- `cli/list.py` - List icons in library
- `cli/helpers.py` - Shared utilities (console, setup_logging)

**Key Features:**
- Automatic command discovery
- Each command in separate file
- Easy to add new commands
- Shared helpers module
- Consistent error handling

## CLI Commands

### create
Create a new DrawIO library from SVG files.

```bash
SVG2DrawIOLib create icons/*.svg -o library.xml [OPTIONS]
```

**Options:**
- `--max-size, -s`: Scale proportionally (longest side = max-size)
- `--width, -w`: Fixed width (overrides max-size)
- `--height, -h`: Fixed height (overrides max-size)
- `--css, -c`: Enable color editing
- `--css-color`: CSS fill color
- `--namespace, -n`: XML namespace
- `--tag, -t`: XML tag for CSS
- `--verbose, -v`: Debug logging
- `--quiet, -q`: Suppress output

### add
Add SVG icons to an existing library.

```bash
SVG2DrawIOLib add library.xml new-icon.svg [OPTIONS]
```

**Options:**
- `--replace, -r`: Replace duplicates
- `--max-size, -s`: Scale new icons
- `--css, -c`: Enable color editing
- `--verbose, -v`: Debug logging
- `--quiet, -q`: Suppress output

### remove
Remove icons from a library by name.

```bash
SVG2DrawIOLib remove library.xml icon1 icon2 [OPTIONS]
```

**Options:**
- `--verbose, -v`: Debug logging
- `--quiet, -q`: Suppress output

### list
List all icons in a library.

```bash
SVG2DrawIOLib list library.xml [OPTIONS]
```

**Options:**
- `--verbose, -v`: Debug logging
- `--quiet, -q`: Suppress output

## Scaling Behavior

### Proportional Scaling (--max-size)

When `--max-size` is specified, icons are scaled proportionally:

1. Extract original dimensions from SVG (viewBox or width/height)
2. Calculate aspect ratio (width / height)
3. Scale so longest dimension equals max-size
4. Calculate other dimension to maintain aspect ratio

**Example:**
```bash
# Original: 100x50 (aspect ratio 2:1)
# --max-size 64
# Result: 64x32 (longest side = 64, aspect maintained)
```

### Fixed Dimensions (--width and --height)

When both `--width` and `--height` are specified:
- Ignores aspect ratio
- Sets exact dimensions
- All icons have same size

**Example:**
```bash
# Original: 100x50
# --width 50 --height 50
# Result: 50x50 (square, aspect ratio ignored)
```

### Default Behavior

When neither option is specified:
- Uses default 40x40 pixels
- Ignores original dimensions

## Data Flow

### Creating a Library

```
SVG Files
    ↓
SVGProcessor.load_svg()
    ↓
SVGProcessor.add_css_classes() [optional]
    ↓
SVGProcessor.calculate_dimensions()
    ↓
SVGProcessor.svg_to_data_uri()
    ↓
SVGProcessor._create_mxgraph_model()
    ↓
SVGProcessor._compress_and_encode()
    ↓
DrawIOIcon
    ↓
LibraryManager.create_library()
    ↓
Library XML File
```

### Adding to Library

```
Existing Library
    ↓
LibraryManager.load_library()
    ↓
List[DrawIOIcon]
    ↓
+ New SVG Files (processed)
    ↓
Merge (with duplicate handling)
    ↓
LibraryManager.create_library()
    ↓
Updated Library XML File
```

## Output Format Details

### CSS Class Injection

To enable color editing in DrawIO, SVG elements need CSS classes with embedded styles (see [DrawIO documentation](https://www.diagrams.net/doc/faq/svg-edit-colours)).

**Input SVG:**
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
  <path d="M10,0C4.48,0,0,4.48,0,10..." />
</svg>
```

**Output with CSS (--css flag):**
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
  <path d="M10,0C4.48,0,0,4.48,0,10..." class="path0" />
  <style type="text/css">.path0{fill:#000000;}</style>
</svg>
```

### Data URI Encoding

SVG is encoded as a data URI using base64. Note: `;base64` is omitted from the MIME type as it conflicts with DrawIO's style syntax.

**Format:**
```
data:image/svg+xml,<base64-encoded-svg>
```

**Example:**
```
data:image/svg+xml,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZlcnNpb249IjEuMSI...
```

### DrawIO Style JSON

Each icon has an associated style object with DrawIO-specific properties:

```json
{
  "shape": "image",
  "verticalLabelPosition": "bottom",
  "labelBackgroundColor": "#ffffff",
  "verticalAlign": "top",
  "aspect": "fixed",
  "imageAspect": 0,
  "image": "data:image/svg+xml,<encoded-svg>",
  "editableCssRules": ".*"
}
```

The `editableCssRules` property enables GUI-based color editing in DrawIO.

### mxGraphModel XML

DrawIO uses mxGraphModel XML structure with three mxCell instances:

```xml
<mxGraphModel>
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />
    <mxCell id="2" parent="1" vertex="1" value=""
            style="shape=image;...;image=data:image/svg+xml,...;editableCssRules=.*">
      <mxGeometry width="40" height="40" as="geometry" />
    </mxCell>
  </root>
</mxGraphModel>
```

### XML Compression

DrawIO compresses XML using zlib deflate algorithm (see [DrawIO documentation](https://drawio-app.com/extracting-the-xml-from-mxfiles/)).

**Process:**
1. Generate mxGraphModel XML
2. Compress with zlib.compress()
3. Base64 encode
4. Store in library JSON

**Example compressed output:**
```
bVRtk6I4EP4rU963m6sbRNzSc9gqXhzEBdQBBfkWIRuiQSwTJfLrt4GZ2dqqo6orD91Pd56kOv1a...
```

### Library JSON Format

Icons are stored as JSON array with metadata:

```json
[
  {
    "xml": "<compressed-mxGraphModel>",
    "w": 40,
    "h": 40,
    "aspect": "fixed",
    "title": "icon-name"
  }
]
```

### Library XML Format

Final library file wraps JSON in XML structure:

```xml
<mxlibrary>
[
  {
    "xml": "bVRtk6I4EP4rU963m6sbRNzSc9gqXhzEBdQBBfkWIRuiQSwTJfLrt4GZ...",
    "w": 40,
    "h": 40,
    "aspect": "fixed",
    "title": "icon-name"
  }
]
</mxlibrary>
```

This format can be imported directly into DrawIO/diagrams.net.

## Error Handling

### File Operations
- `FileNotFoundError`: SVG or library file not found
- `ET.ParseError`: Invalid XML in SVG or library
- `ValueError`: Invalid library format

### Processing
- Graceful handling of missing dimensions
- Fallback to defaults when needed
- Clear error messages with context

### CLI
- Exit code 0: Success
- Exit code 1: Error
- Exit code 130: User interrupt (Ctrl+C)

## Logging

Structured logging with rich output:

```python
logger.debug("Detailed information")
logger.info("General information")
logger.warning("Warning messages")
logger.error("Error messages")
```

**Log Levels:**
- `--quiet`: ERROR only
- Default: INFO
- `--verbose`: DEBUG

## Testing Strategy

### Unit Tests
- Models: Data structure validation
- SVGProcessor: Individual method testing
- LibraryManager: File operations

### Integration Tests
- CLI: End-to-end command testing
- Complete workflows

### Coverage
- 84% overall coverage
- 100% coverage on models
- 91-92% coverage on core logic
- 71% coverage on CLI (error paths)

## Public API

```python
from SVG2DrawIOLib import (
    # Models
    DrawIOIcon,
    SVGDimensions,
    SVGProcessingOptions,
    LibraryMetadata,

    # Processors
    SVGProcessor,
    LibraryManager,

    # Version
    __version__,
)
```

## Design Decisions

### Why Dataclasses?
- Type safety
- Immutability (frozen=False for flexibility)
- Built-in __repr__ and __eq__
- Clear data structure

### Why Class-Based?
- Encapsulation of related functionality
- Dependency injection for testing
- State management (options, configuration)
- Extensibility

### Why Subcommands?
- Scalability (easy to add new commands)
- Clear separation of concerns
- Better help organization
- Industry standard (git, docker, etc.)

### Why Proportional Scaling?
- Maintains visual quality
- Respects original design
- More intuitive than fixed dimensions
- Common use case

## Future Enhancements

Potential additions for future versions:

1. **Batch Operations**
   - Process entire directories
   - Recursive directory scanning
   - Glob pattern support

2. **Library Merging**
   - Combine multiple libraries
   - Conflict resolution strategies

3. **Icon Modification**
   - Resize existing icons
   - Change CSS colors
   - Update metadata

4. **Export Formats**
   - Export to other formats
   - Generate previews
   - Create documentation

5. **Validation**
   - Validate library files
   - Check for broken references
   - Verify icon integrity

## Adding New CLI Commands

The CLI uses dynamic command discovery, making it easy to add new commands:

### Step 1: Create Command File

Create a new file in `src/SVG2DrawIOLib/cli/` (e.g., `merge.py`):

```python
"""Merge command - Merge multiple DrawIO libraries."""

import logging
import sys
from pathlib import Path

import click

from SVG2DrawIOLib.cli.helpers import console, setup_logging
from SVG2DrawIOLib.library_manager import LibraryManager


@click.command()
@click.argument("output", type=click.Path(path_type=Path))
@click.argument("libraries", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging.")
def merge(output: Path, libraries: tuple[Path, ...], verbose: bool) -> None:
    """Merge multiple DrawIO libraries into one.

    \b
    Example:
        SVG2DrawIOLib merge output.xml lib1.xml lib2.xml lib3.xml
    """
    setup_logging(verbose, False)
    logger = logging.getLogger(__name__)

    try:
        # Implementation here
        console.print(f"[green]✓[/green] Merged {len(libraries)} libraries")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
```

### Step 2: That's It!

The command is automatically discovered and registered. No need to modify `__init__.py`.

### Requirements:

1. **File name** = **function name** (e.g., `merge.py` → `def merge()`)
2. Function must be decorated with `@click.command()`
3. File must be in `src/SVG2DrawIOLib/cli/` directory
4. File must not be named `__init__.py` or `helpers.py`

### Testing New Commands:

```bash
# Command is automatically available
SVG2DrawIOLib merge --help
```

## Performance Considerations

- **Lazy Loading**: Libraries loaded only when needed
- **Streaming**: Large files processed incrementally
- **Caching**: Repeated operations cached where appropriate
- **Parallel Processing**: Future enhancement for batch operations

## Security

- **Input Validation**: All file paths validated
- **XML Parsing**: Safe XML parsing (no external entities)
- **Path Traversal**: Prevented through Path validation
- **Injection**: No shell command execution

## Compatibility

- **Python**: 3.13+
- **Operating Systems**: Windows, macOS, Linux
- **DrawIO**: Compatible with diagrams.net format
- **SVG**: Standard SVG 1.1 format
