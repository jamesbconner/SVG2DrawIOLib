# SVG2DrawIOLib

[![PyPI - Version](https://img.shields.io/pypi/v/SVG2DrawIOLib.svg)](https://pypi.org/project/SVG2DrawIOLib)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/SVG2DrawIOLib.svg)](https://pypi.org/project/SVG2DrawIOLib)
[![CI](https://github.com/jamesbconner/SVG2DrawIOLib/workflows/CI/badge.svg)](https://github.com/jamesbconner/SVG2DrawIOLib/actions)
[![Publish to PyPI](https://github.com/jamesbconner/SVG2DrawIOLib/actions/workflows/publish.yml/badge.svg)](https://github.com/jamesbconner/SVG2DrawIOLib/actions/workflows/publish.yml)
[![codecov](https://codecov.io/gh/jamesbconner/SVG2DrawIOLib/branch/main/graph/badge.svg)](https://codecov.io/gh/jamesbconner/SVG2DrawIOLib)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

Convert SVG files into DrawIO/diagrams.net shape libraries with support for colorable icons.

---

## Features

✨ **Easy Conversion**: Transform SVG files into DrawIO libraries with a single command
🎨 **Color Editing**: Optional CSS injection for color customization in DrawIO
📏 **Customizable**: Configure icon dimensions, namespaces, and more
🚀 **Modern CLI**: Beautiful, colorful output with rich-click
🔒 **Type Safe**: Full type annotations with mypy

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

## Advanced Features

### Color Editing

Enable color customization in DrawIO by injecting CSS classes:

```bash
SVG2DrawIOLib create icons/ --css -o colorable-icons.xml
```

This allows users to change icon colors directly in DrawIO's interface.

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
6. **Generates library JSON/XML** compatible with DrawIO

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
