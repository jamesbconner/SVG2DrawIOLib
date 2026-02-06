"""Helper functions and utilities for CLI commands."""

import logging

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
