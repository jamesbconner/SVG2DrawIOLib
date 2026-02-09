"""Helper functions and utilities for CLI commands."""

import logging
import re
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

console = Console()


def setup_logging(verbose: bool, quiet: bool) -> None:
    """Configure logging with rich output.

    Args:
        verbose: Enable debug-level logging.
        quiet: Suppress all but error-level logging.
    """
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_time=False)],
    )


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """Sanitize a filename to prevent path traversal attacks.

    Removes or replaces characters that could be used for path traversal,
    including directory separators, parent directory references, and other
    potentially dangerous characters.

    Args:
        filename: The filename to sanitize.
        replacement: Character to use as replacement for invalid characters.

    Returns:
        Sanitized filename safe for use in file paths.

    Examples:
        >>> sanitize_filename("../../etc/passwd")
        '_.._.._.._etc_passwd'
        >>> sanitize_filename("icon<name>.svg")
        'icon_name_.svg'
        >>> sanitize_filename("/absolute/path/file.svg")
        '_absolute_path_file.svg'
    """
    # Remove null bytes
    filename = filename.replace("\x00", "")

    # Replace path separators (both forward and back slashes)
    filename = filename.replace("/", replacement).replace("\\", replacement)

    # Replace other potentially dangerous characters
    # This includes: < > : " | ? * and control characters
    filename = re.sub(r'[<>:"|?*\x00-\x1f]', replacement, filename)

    # Remove leading/trailing dots and spaces (Windows issues)
    filename = filename.strip(". ")

    # Ensure filename is not empty after sanitization
    if not filename:
        filename = "unnamed"

    # Ensure filename doesn't exceed reasonable length (255 is typical filesystem limit)
    if len(filename) > 255:
        # Keep extension if present
        name_parts = filename.rsplit(".", 1)
        if len(name_parts) == 2:
            name, ext = name_parts
            max_name_len = 255 - len(ext) - 1  # -1 for the dot
            filename = name[:max_name_len] + "." + ext
        else:
            filename = filename[:255]

    return filename


def safe_path_join(base_dir: Path, filename: str) -> Path:
    """Safely join a base directory with a filename, preventing path traversal.

    Args:
        base_dir: The base directory path.
        filename: The filename to join (will be sanitized).

    Returns:
        Safe path within the base directory.

    Raises:
        ValueError: If the resulting path would escape the base directory.

    Examples:
        >>> safe_path_join(Path("/output"), "icon.svg")
        Path('/output/icon.svg')
        >>> safe_path_join(Path("/output"), "../../etc/passwd")
        Path('/output/_.._.._.._etc_passwd')
    """
    # Sanitize the filename first
    safe_filename = sanitize_filename(filename)

    # Join paths
    result_path = (base_dir / safe_filename).resolve()
    base_dir_resolved = base_dir.resolve()

    # Verify the result is within base_dir
    try:
        result_path.relative_to(base_dir_resolved)
    except ValueError as e:
        raise ValueError(
            f"Path traversal detected: '{filename}' would escape base directory"
        ) from e

    return result_path
