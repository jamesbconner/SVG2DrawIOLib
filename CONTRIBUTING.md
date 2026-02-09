# Contributing to SVG2DrawIOLib

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow

## Getting Started

### Prerequisites

- Python 3.13 or higher
- uv (Python package manager)
- Git

### Setup Development Environment

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/SVG2DrawIOLib.git
   cd SVG2DrawIOLib
   ```

2. **Create virtual environment and install dependencies**
   ```bash
   uv venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   make dev
   ```

   This will install the package with development dependencies and set up pre-commit hooks automatically.

3. **Verify setup**
   ```bash
   make test
   ```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

Follow these guidelines:

- **Code Style**: Use ruff for formatting and linting
- **Type Hints**: Add type annotations to all functions
- **Docstrings**: Use Google-style docstrings
- **Logging**: Use structured logging with the `logging` module
- **Tests**: Write tests for new functionality

### 3. Run Quality Checks

```bash
# Format code
make format

# Run all checks (format, lint, type, security, test)
make all

# Run pre-commit hooks manually
make pre-commit

# Or run checks individually
make lint      # Linting with ruff
make type      # Type checking with mypy
make security  # Security scanning with bandit
make test      # Run tests
make cov       # Run tests with coverage report
```

**Available Make Commands:**
- `make help` - Show all available commands
- `make dev` - Install with dev dependencies and set up pre-commit
- `make format` - Format code with ruff
- `make lint` - Run linting checks
- `make type` - Run type checking
- `make security` - Run security checks
- `make test` - Run tests
- `make cov` - Run tests with coverage
- `make all` - Run all checks and tests
- `make pre-commit` - Run pre-commit hooks on all files
- `make build` - Build package distribution
- `make clean` - Clean build artifacts and caches

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions or changes
- `refactor:` Code refactoring
- `style:` Code style changes
- `chore:` Maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Code Guidelines

### Python Style and Best Practices

This project follows modern Python best practices with a focus on maintainability, type safety, and testability.

#### Core Principles

1. **SOLID Principles**
   - **Single Responsibility**: Each class/function should have one clear purpose
   - **Open/Closed**: Open for extension, closed for modification
   - **Liskov Substitution**: Subtypes must be substitutable for their base types
   - **Interface Segregation**: Many specific interfaces over one general interface
   - **Dependency Inversion**: Depend on abstractions, not concretions

2. **Separation of Concerns**
   - **Models** (`models.py`): Data structures and validation only
   - **Services** (`svg_processor.py`, `library_manager.py`, etc.): Business logic
   - **CLI** (`cli/`): User interface layer, thin orchestration
   - **Helpers** (`cli/helpers.py`, `cli/create_helpers.py`): Reusable utilities

3. **Type Safety**
   - Use type hints for all function parameters and return values
   - Use modern Python 3.13+ type syntax: `list[str]`, `dict[str, int]`
   - Run `mypy --strict` and fix all type errors
   - Avoid `Any` unless absolutely necessary

#### Code Style

**Formatting and Linting:**
- Use `ruff` for both formatting and linting (replaces black, isort, flake8)
- Line length: 100 characters
- Follow PEP 8 conventions
- Run `make format` before committing

**Naming Conventions:**
- Classes: `PascalCase` (e.g., `SVGProcessor`, `LibraryManager`)
- Functions/methods: `snake_case` (e.g., `process_svg_file`, `add_css_classes`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_MAX_SIZE`)
- Private methods: `_leading_underscore` (e.g., `_compress_and_encode`)

**Imports:**
- Standard library imports first
- Third-party imports second
- Local imports last
- Alphabetically sorted within each group
- Use absolute imports for project modules

#### Documentation

**Docstrings:**
Use Google-style docstrings for all public functions, classes, and methods:

```python
def process_svg_file(
    self,
    filepath: Path,
    max_dimension: float | None = None,
    width: float | None = None,
    height: float | None = None,
) -> DrawIOIcon:
    """Process an SVG file and create a DrawIO icon.

    Loads the SVG, optionally adds CSS classes, calculates dimensions,
    and generates the compressed mxGraphModel XML.

    Args:
        filepath: Path to the SVG file to process.
        max_dimension: Maximum dimension for proportional scaling (optional).
        width: Fixed width in pixels (optional, overrides max_dimension).
        height: Fixed height in pixels (optional, overrides max_dimension).

    Returns:
        DrawIOIcon with processed SVG data and dimensions.

    Raises:
        FileNotFoundError: If the SVG file doesn't exist.
        ET.ParseError: If the SVG file is not valid XML.
        ValueError: If dimensions cannot be determined.

    Example:
        >>> processor = SVGProcessor(SVGProcessingOptions())
        >>> icon = processor.process_svg_file(Path("icon.svg"), max_dimension=64)
        >>> print(f"{icon.name}: {icon.dimensions.width}x{icon.dimensions.height}")
        icon: 64x64
    """
```

**Comments:**
- Use comments to explain *why*, not *what*
- Avoid obvious comments that restate the code
- Use comments for complex algorithms or non-obvious decisions

#### Error Handling

**Exceptions:**
- Use specific exception types (avoid bare `except`)
- Provide actionable error messages
- Include context in error messages (file paths, values, etc.)
- Log errors before raising

```python
if not filepath.exists():
    logger.error(f"SVG file not found: {filepath}")
    raise FileNotFoundError(f"SVG file not found: {filepath}")
```

**Logging:**
- Use the `logging` module, not `print()`
- Use appropriate log levels:
  - `DEBUG`: Detailed diagnostic information
  - `INFO`: General informational messages
  - `WARNING`: Warning messages for recoverable issues
  - `ERROR`: Error messages for failures
- Include context in log messages

```python
logger.debug(f"Processing SVG: {filepath}")
logger.info(f"Created library with {icon_count} icons")
logger.warning(f"Icon '{name}' already exists, skipping")
logger.error(f"Failed to parse SVG {filepath}: {error}")
```

#### Testing

**Test Structure:**
- One test file per module (e.g., `test_svg_processor.py` for `svg_processor.py`)
- Use descriptive test names that explain what is being tested
- Group related tests in classes
- Use pytest fixtures for common setup

```python
class TestSVGProcessor:
    """Tests for SVGProcessor class."""

    @pytest.fixture
    def processor(self) -> SVGProcessor:
        """Create a processor with default options."""
        return SVGProcessor(SVGProcessingOptions())

    @pytest.fixture
    def sample_svg(self, tmp_path: Path) -> Path:
        """Create a sample SVG file for testing."""
        svg_path = tmp_path / "test.svg"
        svg_path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">'
            '<path d="M10,0L20,20L0,20Z" fill="#000"/>'
            '</svg>'
        )
        return svg_path

    def test_process_svg_file_basic(
        self, processor: SVGProcessor, sample_svg: Path
    ) -> None:
        """Test basic SVG file processing."""
        icon = processor.process_svg_file(sample_svg)
        assert icon.name == "test"
        assert icon.dimensions.width > 0
        assert icon.dimensions.height > 0

    def test_process_svg_file_not_found(self, processor: SVGProcessor) -> None:
        """Test processing non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            processor.process_svg_file(Path("nonexistent.svg"))
```

**Coverage:**
- Aim for 90%+ coverage on all modules
- Test both success and failure paths
- Test edge cases and boundary conditions
- Use `make cov` to generate coverage reports

#### CLI Development

**Command Structure:**
- Each command in its own file (e.g., `cli/create.py`)
- Function name must match filename (e.g., `def create()` in `create.py`)
- Keep CLI commands thin - delegate to service classes
- Extract complex logic into helper modules (e.g., `create_helpers.py`)

**CLI Best Practices:**
- Use `rich_click` for colorful output
- Use `console.print()` for user-facing messages
- Use `logger` for diagnostic messages
- Provide clear error messages with context
- Support `--verbose` and `--quiet` flags
- Use `rc.ClickException` for user errors, not `sys.exit()`

```python
@rc.command()
@rc.argument("svg_paths", nargs=-1, required=True, type=rc.Path(exists=True, path_type=Path))
@rc.option("--output", "-o", type=rc.Path(path_type=Path), required=True)
@rc.option("--verbose", "-v", is_flag=True, help="Enable debug logging.")
@rc.option("--quiet", "-q", is_flag=True, help="Suppress output except errors.")
def create(svg_paths: tuple[Path, ...], output: Path, verbose: bool, quiet: bool) -> None:
    """Create a new DrawIO library from SVG files.

    \b
    Example:
        SVG2DrawIOLib create icon1.svg icon2.svg -o library.xml
    """
    setup_logging(verbose, quiet)
    logger = logging.getLogger(__name__)

    try:
        # Delegate to service classes
        manager = LibraryManager()
        # ... implementation
        console.print(f"[green]✓[/green] Created library: [cyan]{output}[/cyan]")
    except Exception as e:
        logger.error(f"Failed to create library: {e}")
        if verbose:
            raise
        raise rc.ClickException(f"Failed to create library: {e}") from e
```

#### Performance Considerations

- Use generators for large datasets
- Avoid loading entire files into memory when possible
- Cache expensive computations when appropriate
- Profile code before optimizing (don't guess)

#### Security

- Validate all user inputs
- Use `Path` objects for file operations (prevents path traversal)
- Never execute shell commands with user input
- Use safe XML parsing (no external entities)
- Run `make security` to check for security issues

### Example Function

```python
def process_svg(filepath: Path, options: dict[str, Any]) -> ET.ElementTree:
    """Process an SVG file with given options.

    Args:
        filepath: Path to the SVG file.
        options: Processing options including namespace and CSS settings.

    Returns:
        Processed ElementTree object.

    Raises:
        FileNotFoundError: If the SVG file doesn't exist.
        ValueError: If options are invalid.

    Example:
        >>> svg = process_svg(Path("icon.svg"), {"css": True})
        >>> print(svg.getroot().tag)
        '{http://www.w3.org/2000/svg}svg'
    """
    if not filepath.exists():
        logger.error(f"SVG file not found: {filepath}")
        raise FileNotFoundError(f"SVG file not found: {filepath}")

    logger.debug(f"Processing SVG: {filepath}")
    # Implementation...
```

### Testing Guidelines

1. **Write tests for all new code**
   - Unit tests for individual functions
   - Integration tests for workflows
   - Edge cases and error conditions

2. **Test structure**
   ```python
   class TestFeatureName:
       """Tests for feature_name functionality."""

       def test_basic_case(self) -> None:
           """Test basic functionality."""
           result = function_under_test(input_data)
           assert result == expected_output

       def test_edge_case(self) -> None:
           """Test edge case handling."""
           with pytest.raises(ValueError):
               function_under_test(invalid_input)
   ```

3. **Aim for 90%+ coverage**
   ```bash
   make cov
   ```

### Documentation

- Update docstrings for changed functions
- Update README.md if adding user-facing features
- Update CHANGELOG.md with your changes
- Add examples for new features

## Pull Request Process

1. **Ensure all checks pass**
   ```bash
   make all
   # or
   make pre-commit
   ```
   - All tests pass
   - Code coverage maintained or improved (90%+ target)
   - Linting passes (ruff)
   - Type checking passes (mypy)
   - Security scanning passes (bandit)
   - Pre-commit hooks pass

2. **Update documentation**
   - Add/update docstrings
   - Update README if needed
   - Update CHANGELOG.md

3. **Write a clear PR description**
   - What changes were made
   - Why the changes were needed
   - How to test the changes
   - Any breaking changes

4. **Request review**
   - Tag relevant maintainers
   - Respond to feedback promptly
   - Make requested changes

5. **Squash commits if needed**
   - Keep commit history clean
   - One logical change per commit

## Release Process

Releases are handled by maintainers:

1. Update version in `src/SVG2DrawIOLib/__about__.py`
2. Update CHANGELOG.md
3. Create release via GitHub Actions workflow
4. Automatic PyPI publication on release

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Check existing issues and PRs first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
