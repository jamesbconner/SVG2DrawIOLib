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

### Python Style

Follow the project's Python rules (see `.kiro/steering/python.rules.md`):

- Use Python 3.13+ features
- Follow SOLID principles
- Write modular, testable code
- Use type hints everywhere
- Add comprehensive docstrings

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
