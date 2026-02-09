# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2026-02-09

### Changed

- **Documentation Improvements**: Significantly improved documentation for v1.2.0 features in README.md, QUICKSTART.md, ARCHITECTURE.md, and CONTRIBUTING.md:
  - Added documentation for new commands: `extract`, `rename`, `inspect`, `validate`
  - Enhanced CSS feature documentation with detailed explanations of `--css-mode`, `--css-stroke-color`, and `--preserve-current-color` options
  - Added `--split-by-folder` feature documentation with directory structure examples
  - Reorganized command documentation into three logical groups: Library Management, Library Inspection, and SVG Processing
  - Clarified `--tag` option with practical examples showing when and how to target different SVG element types (path, circle, rect, ellipse)
  - Updated Python API examples to demonstrate new features including `IconAnalyzer` service and `rename_icon()` method
  - Enhanced architecture overview with descriptions of new service classes (`IconAnalyzer`, `LibraryValidator`, `PathSplitter`) and helper modules (`create_helpers.py`)
  - Updated module structure diagram to reflect all new files and commands
  - Documented CSS mode behavior and special value handling in detail
  - Expanded CONTRIBUTING.md with coding guidelines, providing detailed inline guidance on:
    - SOLID principles and separation of concerns
    - Code style, naming conventions, and formatting rules
    - Documentation standards with Google-style docstring examples
    - Error handling and logging best practices
    - Testing structure and coverage requirements
    - CLI development patterns and best practices
    - Performance and security considerations

## [1.2.0] - 2026-02-08

### Added

- **Improved ViewBox Adjustment with Transforms**: Significantly improved viewBox adjustment accuracy for SVGs with transforms. The svgelements-based bbox calculation now correctly handles transformed elements (translate, scale, rotate, skew, matrix) while still excluding non-rendering containers (defs, clipPath, mask, symbol, pattern, marker). This reduces unnecessary padding in many real-world icons that use transforms, which are common in exported SVGs. The manual fallback still conservatively skips transforms for compatibility.
- **Enhanced CSS Injection**: Significantly improved CSS class generation for color editing in DrawIO with support for real-world SVG authoring patterns:
  - **CSS Modes**: New `--css-mode` option with three modes:
    - `fill` (default): Generate CSS rules for fill colors only
    - `stroke`: Generate CSS rules for stroke colors only
    - `both`: Generate CSS rules for both fill and stroke colors
  - **Style Attribute Parsing**: Now parses `style="fill:#fff;stroke:#000"` attributes in addition to direct `fill` and `stroke` attributes
  - **fill="none" Handling**: Properly respects `fill="none"` and `stroke="none"` - no longer forces colors on stroke-only or fill-only paths
  - **currentColor Support**: New `--preserve-current-color` flag (default: true) to preserve `currentColor` values for theme-aware icons
  - **Default Stroke Color**: New `--css-stroke-color` option to set default stroke color (used with `--css-mode stroke` or `both`)
  - Available in both `create` and `add` commands
  - Makes split-paths workflow more consistently colorable in DrawIO
- **Extract Command**: New `extract` CLI command for extracting icons from DrawIO libraries back to individual SVG files. This is the inverse operation of `create`, allowing users to recover SVG files from library files. Supports extracting all icons or specific icons by name, with optional overwrite functionality.
- **Rename Command**: New `rename` CLI command for renaming icons within a DrawIO library. Allows renaming a single icon while preserving its content. Supports optional `--overwrite` flag to replace an existing icon with the new name.
- **Inspect Command**: New `inspect` CLI command for displaying detailed information about icons in a DrawIO library. Shows dimensions, shape type, CSS classes, and inline styles for each icon. Supports inspecting all icons or specific icons by name, with optional `--show-svg` flag to display the decoded SVG content. Includes `--json` flag for machine-readable JSON output.
- **Validate Command**: New `validate` CLI command for comprehensive validation of DrawIO library files. Validates XML structure, JSON format, icon integrity (required fields, dimensions, base64 encoding, compression), mxGraphModel structure, and SVG content (namespace, viewBox/dimensions, empty SVG detection). Provides detailed error and warning messages with color-coded status output. Includes `LibraryValidator` service class following SOLID principles for separation of concerns.
- **CLI Command Groups**: Reorganized CLI commands into three logical groups for better discoverability: Library Management Commands (create, add, remove, extract, rename), Library Inspection Commands (list, inspect, validate), and SVG Processing Commands (split-paths).
- **Split by Folder**: New `--split-by-folder` flag for `create` command that creates separate library files for each subdirectory when used with `--recursive`. Output filename is modified with subdirectory name (e.g., `FontAwesome.xml` becomes `FontAwesome-Regular.xml`, `FontAwesome-Solid.xml`, `FontAwesome-Brands.xml`). This is useful for organizing icon sets that are already grouped by category in the filesystem.

### Changed

- **Refactored CLI Commands**: Improved separation of concerns following SOLID principles. Business logic has been extracted from CLI commands into reusable service classes:
  - Created `IconAnalyzer` service for extracting and analyzing icon content (used by `extract` and `inspect` commands)
  - Added `LibraryManager.rename_icon()` method for icon renaming logic (used by `rename` command)
  - CLI commands are now thin orchestration layers that delegate to service classes
  - All business logic is now testable independently of the CLI layer
- **Test Organization**: Improved test file organization for consistency. Each CLI command now has its own dedicated test file (`test_cli_extract.py`, `test_cli_rename.py`, etc.) following the same pattern as other command tests.

### Fixed

- **List Command Table Width**: Fixed table width calculation in `list` command to prevent title text wrapping. The table now properly sizes to accommodate whichever is wider: the title text, column header, or icon names. This ensures clean, readable output regardless of filename or icon name length.
- **Type Checking Configuration**: Fixed mypy configuration inconsistency between local pre-commit and GitHub CI. Removed CLI directory exclusion from local pre-commit config and added tests directory to both local and CI mypy checks. All 107 type errors across test files have been resolved with proper type annotations and assertions. Both local and CI environments now run `mypy --strict src tests` consistently.

## [1.1.2] - 2026-02-08

### Fixed

- **SVG Namespace Correctness**: Fixed `<style>` element creation in `add_css_classes()` to use proper SVG namespace. The style element is now created as `{http://www.w3.org/2000/svg}style` instead of a non-namespaced element, improving standards compliance and compatibility with strict XML parsers. The style element is now inserted inside `<defs>` if it exists, or at the top of the document otherwise, following SVG best practices.
- **Compression Robustness**: Fixed `_compress_and_encode()` to use `wbits=-15` for generating raw DEFLATE directly instead of manually stripping zlib header and checksum bytes. This "correct by construction" approach is more robust and follows zlib best practices, eliminating assumptions about wrapper structure.

### Changed

- **Error Handling**: Refactored all CLI commands to use `rich_click.ClickException` and `rich_click.Abort()` instead of `sys.exit()` for better error handling and consistency with the Click framework. This provides cleaner exception handling and more idiomatic Click code.
- **String Encoding Consistency**: Updated all string encoding/decoding operations to use UTF-8 instead of ASCII for better consistency and future-proofing. This affects `DrawIOIcon.to_dict()`, `LibraryManager.load_library()`, and `SVGProcessor.svg_to_data_uri()`. While base64 strings are ASCII-safe, UTF-8 is more explicit and handles any future character set requirements.

### Added

- **Source Files Tracking**: Added optional `source_files` parameter to `create_library()` and `add_icons_to_library()` methods in `LibraryManager`. CLI commands (`create` and `add`) now pass source file lists to enable programmatic tracking of which SVG files were used to create library icons. This metadata is stored in the returned `LibraryMetadata` object for use by programmatic consumers.
- **Windows Makefile Support**: Added `make clean-win` target for cleaning build artifacts and caches on Windows systems using native Windows commands (rmdir, del) instead of Unix commands (rm, find).
- **Source Archive Creation**: Added `make zip` target to create a clean source archive (`SVG2DrawIOLib-source.zip`) that respects `.gitignore` configuration using `git archive`.
- **Lowercase Command Alias**: Added `svg2drawiolib` as a lowercase alias for the main `SVG2DrawIOLib` command. Both commands are functionally identical and can be used interchangeably.

## [1.1.1] - 2026-02-08

### Fixed

- **Version Display**: Fixed `--version` flag to display the correct SVG2DrawIOLib version (1.1.1) instead of the rich-click library version (1.9.7). The CLI now imports and displays the version from `__about__.py`, which is the single source of truth for the package version.

### Changed

- **Logging Consistency**: Standardized logging styles across all CLI commands for better consistency and clarity.
  - Updated `split-paths` command to use `setup_logging()` helper function instead of `logging.basicConfig()`, matching all other CLI commands.
  - Made error messages more descriptive with operation context (e.g., "Failed to create library" instead of "Unexpected error").
  - Moved logger initialization in `split-paths` from module-level to function-level for consistency with other commands.
- **CLI Framework Consistency**: Updated `split-paths` command to use `rich_click` instead of plain `click`, matching all other CLI commands.
- **CLI Help Text Formatting**: Reformatted docstrings for all CLI commands to provide consistent, well-structured help output with:
  - Bold cyan command titles with rich markup
  - Preserved formatting using literal blocks (`\b`)
  - Structured sections (e.g., "Duplicate Handling:", "Scaling Options:", "Examples:")

## [1.1.0] - 2026-02-08

### Added

- **Path Splitting Command**: New `split-paths` subcommand for splitting compound SVG paths into separate path elements for per-path color control.
  - Automatically detects paths with multiple M/m (moveto) commands
  - Splits them into separate path elements with individual CSS classes
  - Intelligently preserves "donut holes" by detecting nested paths via bounding box containment
  - Enables per-path color customization when combined with `--css` flag with the `create` or `add` commands
- **PathSplitter Class**: New `path_splitter.py` module with hole detection algorithm
- **Comprehensive Test Suite**: Added 7 new tests for path splitting functionality

### Fixed

- **CSS Class Preservation**: Fixed `add_css_classes()` method to preserve existing CSS class attributes instead of overwriting them. This allows split paths to maintain their assigned classes through the processing pipeline.
- **Multi-Class CSS Selectors**: Fixed CSS selector generation for elements with multiple space-separated classes. Now uses only the first class for the selector instead of creating invalid descendant selectors.
- **Duplicate CSS Selectors**: Fixed duplicate CSS selector generation when multiple elements share the same class. Now only generates one CSS rule per unique class, using the first occurrence's fill color.
- **Duplicate ID Attributes**: Fixed path splitting to create unique IDs (`originalid-0`, `originalid-1`, etc.) when the original path has an `id` attribute, preventing SVG/XML validation errors.
- **Whitespace-Only Class Attribute**: Fixed IndexError when an SVG element has a class attribute containing only whitespace. Now properly handles empty/whitespace-only class attributes by generating a new class name.
- **Class Name Collision in Path Splitting**: Fixed duplicate class names when splitting multiple compound paths. Now uses a global counter to ensure all split paths get unique class names (path0, path1, path2, etc.) instead of resetting the counter for each compound path.
- **Subpath Data Loss**: Fixed silent data loss in `_group_paths_with_holes` when `bbox()` returns `None` without raising an exception. Now all subpaths are preserved in the output, even those with empty or invalid geometry that return `None` from `bbox()`.
- **Path Data Loss on Exception**: Fixed data loss when exceptions occur during path splitting. Original paths are now preserved if split fails, preventing silent data loss. The original path is only removed after all new split paths are successfully created.
- **Unreachable Code in CLI**: Removed unreachable else branch in `split_paths` CLI command. The `split_svg_paths` method now correctly returns `dict[str, int]` instead of `dict[str, int] | None`, as it never actually returned `None`.

### Changed

- **CLI Command Groups**: Updated CLI help to include new "SVG Processing Commands" group for `split-paths`
- **Namespace Handling**: Improved SVG namespace registration to avoid `ns0:` prefixes in output files

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

### Known Limitations

- **Arc Bounds Approximation**: Manual path bounds calculation (fallback for SVGs with transforms or `<defs>`) approximates arc bounds using start and end points only. Arcs that curve significantly beyond their endpoints (e.g., large semicircles) may have underestimated bounds. The primary `svgelements` path handles this correctly for most SVGs.

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
