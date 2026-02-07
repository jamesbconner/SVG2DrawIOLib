# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-02-07

### Fixed

- **ViewBox Padding Detection**: Fixed padding calculation to correctly account for non-zero viewBox origins (vb_x, vb_y). Previously falsely detected padding when content filled viewBox completely with non-zero origin coordinates.
- **SVG Path Parsing**: Completely rewrote path bounds calculation to properly handle H (horizontal), V (vertical), C/S (cubic bezier), Q/T (quadratic bezier), and A (arc) commands. Now supports both absolute and relative command variants.
- **ViewBox Clamping**: Added clamping logic to prevent viewBox from expanding beyond original bounds. Ensures the method only shrinks viewBox to remove padding, never expands it to reveal clipped content.
- **Relative Bezier Curves**: Fixed bezier curve handling to properly process multiple segments in a single command. Now correctly updates current position after each segment, preventing incorrect offset calculations for subsequent curves.
- **Negative Dimensions**: Added validation to ensure content dimensions are positive after clamping. Prevents invalid viewBox with negative width/height when content is entirely outside viewBox bounds.
- **Non-Rendering Containers**: Fixed bounds calculation to skip elements inside non-rendering containers (`<defs>`, `<clipPath>`, `<mask>`, `<symbol>`, `<pattern>`, `<marker>`). Previously included definition elements in bounds, inflating calculated bounds and preventing viewBox adjustment.
- **Transform Attributes**: Added conservative handling for elements with transform attributes. Elements with transforms (or inside transformed groups) are now skipped during bounds calculation to avoid incorrect coordinate space calculations.
- **Unsupported SVG Elements**: Added support for additional SVG element types in viewBox adjustment: `<ellipse>`, `<line>`, `<polyline>`, and `<polygon>`. Previously only `<path>`, `<circle>`, and `<rect>` were considered, potentially causing visible content to be clipped.
- **Parent Map Performance**: Optimized parent map construction to build once per viewBox adjustment instead of rebuilding for every element check. Reduced complexity from O(elements × tree_size) to O(tree_size), significantly improving performance for complex SVGs.
- **Dead Code Removal**: Removed unused `calculate_svg_bounds()` method and redundant dimension calculations to improve code clarity.

### Changed

- **SVG Content Bounds**: ViewBox adjustment now calculates actual content bounds from all supported SVG elements (paths, circles, rects, ellipses, lines, polylines, polygons) and only adjusts when padding exceeds 5% threshold on any side.
- **Test Coverage**: Increased test coverage from 88% to 95% with comprehensive tests for edge cases and bug scenarios (160 tests total, 82 for svg_processor).

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
