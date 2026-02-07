# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-02-07

### Added

- **Accurate Bounding Box Calculation**: Integrated `svgelements` library for pixel-perfect bounding box calculation that matches DrawIO's native behavior (within 0.000003 pixels). This completely eliminates padding issues by using the same calculation method as browsers.
- **svgelements Dependency**: Added `svgelements>=1.9.0` as a required dependency.

### Fixed

- **ViewBox Padding Issues**: Replaced manual path bounds calculation with `svgelements` library, which provides browser-accurate bounding box calculation. This fixes all padding and clipping issues by matching DrawIO's native `getBBox()` behavior exactly.
- **CSS Color Preservation**: Fixed CSS class feature to preserve original fill colors instead of overriding all paths with the default color. Each path now gets a CSS class with its original fill color.
- **Aspect Ratio Preservation**: Fixed default dimension calculation to maintain SVG aspect ratio instead of forcing square 40x40 dimensions. Now uses max dimension of 40 while preserving aspect ratio.
- **Library Dimension Rounding**: Changed from truncation (`int()`) to proper rounding (`round()`) to match DrawIO's rendering behavior.
- **Dimension Consistency**: Fixed inconsistency where library JSON metadata used `round()` but embedded geometry used `int()` (truncation), ensuring both use consistent rounding.
- **Arc Command Multiple Segments**: Fixed path bounds calculation for arc commands with multiple segments. Previously only captured the last segment's endpoint; now properly iterates through all arc segments (7 parameters each) and correctly handles relative positioning.
- **Temp File Cleanup**: Fixed potential temp file leak in `_adjust_viewbox_with_svgelements` when SVG write operation fails. Temp file is now properly cleaned up even if an exception occurs during write.

### Changed

- **ViewBox Adjustment**: Now uses `svgelements` for accurate bounds calculation on simple SVGs, with intelligent fallback to manual calculation for complex SVGs with transforms or non-rendering containers.
- **Default Dimensions**: Changed default behavior to maintain aspect ratio with max dimension of 40, instead of fixed 40x40 square dimensions.

### Removed

- **Padding Threshold**: Removed the 5% padding threshold - now always adjusts viewBox to actual content bounds.

## [1.0.0] - 2026-02-06

### Initial Release

A complete rewrite and modernization of the SVG to DrawIO library converter with a focus on maintainability, type safety, and user experience.

#### Features

- **Modular CLI Architecture**: Command-line interface with subcommands (create, add, remove, list) using Click and rich-click for colorful output
- **Class-Based Design**: Clean separation of concerns with dedicated classes:
  - `SVGProcessor`: Handles SVG file processing and transformations
  - `LibraryManager`: Manages DrawIO library file operations
  - Dataclasses for type-safe data structures (SVGDimensions, DrawIOIcon, SVGProcessingOptions, LibraryMetadata)
- **Proportional Scaling**: Intelligent icon scaling that maintains aspect ratio with `--max-size` option
- **Fixed Dimensions**: Support for custom width/height with `--width` and `--height` options
- **CSS Color Editing**: Optional CSS class injection for color customization in DrawIO
- **Library Management**: Add, remove, and list icons in existing library files
- **Rich Output**: Colorful CLI with emojis, formatted tables, and clear status messages

#### Developer Experience

- **Type Safety**: Full type annotations with mypy strict mode compliance
- **Documentation**: Google-style docstrings throughout codebase
- **Testing**: Comprehensive test suite with 51 tests and 85% coverage
- **Code Quality**: Automated checks with ruff, mypy, bandit, and pre-commit hooks
- **Structured Logging**: Rich-formatted logging with configurable verbosity
- **CI/CD**: GitHub Actions workflows for testing, building, and publishing to PyPI
- **Modern Tooling**: Uses uv for dependency management and hatchling for packaging

#### Requirements

- Python 3.13+
- Modern dependency stack with rich-click, rich, and lxml

#### Architecture

The project follows SOLID principles with clear module boundaries:
- `models.py`: Data structures and validation
- `svg_processor.py`: SVG processing logic
- `library_manager.py`: Library file management
- `cli/`: Modular CLI with dynamic command loading

[1.0.1]: https://github.com/jamesbconner/SVG2DrawIOLib/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/jamesbconner/SVG2DrawIOLib/releases/tag/v1.0.0
