# SVG2DrawIOLib

[![PyPI - Version](https://img.shields.io/pypi/v/SVG2DrawIOLib.svg)](https://pypi.org/project/SVG2DrawIOLib)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/SVG2DrawIOLib.svg)](https://pypi.org/project/SVG2DrawIOLib)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/SVG2DrawIOLib)](https://pypi.org/project/SVG2DrawIOLib)
[![CI](https://github.com/jamesbconner/SVG2DrawIOLib/workflows/CI/badge.svg)](https://github.com/jamesbconner/SVG2DrawIOLib/actions)
[![Publish to PyPI](https://github.com/jamesbconner/SVG2DrawIOLib/actions/workflows/publish.yml/badge.svg)](https://github.com/jamesbconner/SVG2DrawIOLib/actions/workflows/publish.yml)
[![codecov](https://codecov.io/gh/jamesbconner/SVG2DrawIOLib/branch/main/graph/badge.svg)](https://codecov.io/gh/jamesbconner/SVG2DrawIOLib)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)

Convert SVG files into DrawIO/diagrams.net shape libraries with support for colorable icons.

## Features

- ✨ **Batch Conversion**: Process individual files, entire directories, or recursive folder structures
- 🎯 **Pixel-Perfect Rendering**: Browser-accurate bounding box calculation (via `svgelements`) eliminates padding and ensures icons render exactly as designed
- 🎨 **Color Customization**: Inject CSS classes to enable color editing directly in DrawIO's interface
- 📏 **Flexible Sizing**: Proportional scaling with aspect ratio preservation, or fixed dimensions
- 📚 **Library Management**: Create new libraries, add/remove icons, and list contents
- 🚀 **Modern CLI**: Beautiful, colorful output with rich-click
- 🔧 **Modern Python Stack**: Built with ruff, mypy, bandit, pytest, and pre-commit hooks

---

## Quick Start

### Installation

```bash
pip install SVG2DrawIOLib
```

### Basic Usage

```bash
# Convert individual SVG files to DrawIO library
SVG2DrawIOLib create icon1.svg icon2.svg -o my-library.xml

# Convert all SVGs in a directory
SVG2DrawIOLib create icons/ -o my-library.xml

# Convert all SVGs in directory and subdirectories
SVG2DrawIOLib create icons/ -o my-library.xml --recursive

# Enable color editing in DrawIO
SVG2DrawIOLib create icons/ --css -o colorable-icons.xml

# Custom dimensions with proportional scaling
SVG2DrawIOLib create icons/ --max-size 64 -o large-icons.xml -R
```

## Documentation

- [Quick Start Guide](QUICKSTART.md) - Get started quickly for users and developers
- [Architecture](ARCHITECTURE.md) - Technical details and implementation
- [Contributing Guide](CONTRIBUTING.md) - Development workflow
- [Changelog](CHANGELOG.md) - Version history

## Commands

### Create a Library

Create a new DrawIO library from SVG files:

```bash
# Basic usage
SVG2DrawIOLib create icon1.svg icon2.svg -o my-library.xml

# From directory
SVG2DrawIOLib create icons/ -o my-library.xml

# Recursive directory scan
SVG2DrawIOLib create icons/ -o my-library.xml --recursive
```

### Add Icons to Library

Add new icons to an existing library:

```bash
# Add single icon
SVG2DrawIOLib add my-library.xml new-icon.svg

# Add multiple icons
SVG2DrawIOLib add my-library.xml icon1.svg icon2.svg

# Replace duplicates
SVG2DrawIOLib add my-library.xml icon.svg --replace
```

### Remove Icons

Remove icons from a library by name:

```bash
SVG2DrawIOLib remove my-library.xml icon-name1 icon-name2
```

### List Icons

List all icons in a library:

```bash
SVG2DrawIOLib list my-library.xml
```

### Split Compound Paths

Split SVG paths with multiple shapes into separate paths for per-path color control:

```bash
# Split compound paths in an SVG
SVG2DrawIOLib split-paths icon.svg -o icon-split.svg

# Then create library with CSS enabled
SVG2DrawIOLib create icon-split.svg --css -o colorable-icon.xml
```

This command:
- Detects paths with multiple M/m (moveto) commands
- Splits them into separate path elements
- Automatically preserves "donut holes" (nested paths)
- Adds CSS classes for individual color control

Useful for icons that have a single compound path but multiple distinct shapes.

## Advanced Features

### Color Editing

Enable color customization in DrawIO by injecting CSS classes:

```bash
SVG2DrawIOLib create icons/ --css -o colorable-icons.xml
```

This allows users to change icon colors directly in DrawIO's interface. For icons with compound paths (single path containing multiple shapes), use `split-paths` first to enable per-shape color control.

### Proportional Scaling

Scale icons proportionally while maintaining aspect ratio:

```bash
# Scale so longest side is 64px
SVG2DrawIOLib create icons/ --max-size 64 -o large-icons.xml
```

### Fixed Dimensions

Set exact dimensions for all icons:

```bash
SVG2DrawIOLib create icons/ --width 50 --height 50 -o square-icons.xml
```

### Custom Configuration

```bash
# Custom XML namespace
SVG2DrawIOLib create icons/ --namespace "http://custom.ns" -o library.xml

# Custom CSS tag for color editing
SVG2DrawIOLib create icons/ --css --tag "circle" -o library.xml

# Custom CSS color
SVG2DrawIOLib create icons/ --css --css-color "#FF0000" -o library.xml
```

## How It Works

SVG2DrawIOLib converts SVG files into DrawIO's custom library format:

1. **Parses SVG files** and extracts dimensions
2. **Optionally injects CSS classes** for color editing support
3. **Encodes SVG as data URI** with base64 encoding
4. **Wraps in mxGraphModel XML** structure
5. **Compresses using zlib** deflate algorithm
6. **Generates library XML** compatible with DrawIO

For technical details about the conversion process, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Python API

Use SVG2DrawIOLib programmatically:

```python
from pathlib import Path
from SVG2DrawIOLib import SVGProcessor, LibraryManager, SVGProcessingOptions

# Configure processing options
options = SVGProcessingOptions(add_css=True, css_color="#000000")

# Process SVG file
processor = SVGProcessor(options)
icon = processor.process_svg_file(Path("icon.svg"), max_dimension=64)

# Create library
manager = LibraryManager()
metadata = manager.create_library([icon], Path("library.xml"))

print(f"Created library with {metadata.icon_count} icons")
```

For complete API documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

## License

`SVG2DrawIOLib` is distributed under the terms of the [MIT](LICENSE.txt) license.
