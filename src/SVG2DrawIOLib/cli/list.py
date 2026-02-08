"""List command - List all icons in a DrawIO library."""

import logging
import sys
from pathlib import Path

import rich_click as rc
from rich.table import Table

from SVG2DrawIOLib.cli.helpers import console, setup_logging
from SVG2DrawIOLib.library_manager import LibraryManager


@rc.command(name="list")
@rc.argument(
    "library_file",
    type=rc.Path(exists=True, dir_okay=False, path_type=Path),
)
@rc.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose debug logging.",
)
@rc.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress all output except errors.",
)
def list(
    library_file: Path,
    verbose: bool,
    quiet: bool,
) -> None:
    """[bold cyan]List all icons in a DrawIO library.[/]

    \b
    \nDisplays all icon names in the specified library file.

    \b
    Example:
        List all icons:
        $ SVG2DrawIOLib list my-library.xml
    """
    setup_logging(verbose, quiet)
    logger = logging.getLogger(__name__)

    try:
        logger.debug(f"Listing icons in library: {library_file}")

        manager = LibraryManager()
        icon_names = manager.list_icons(library_file)

        if not icon_names:
            logger.info("Library is empty")
            console.print(f"[yellow]Library is empty:[/yellow] {library_file}")
            return

        logger.info(f"Found {len(icon_names)} icon(s) in library")

        # Create a nice table
        table = Table(title=f"Icons in {library_file.name}", show_header=True)
        table.add_column("Icon Name", style="cyan")

        for name in sorted(icon_names):
            table.add_row(name)

        console.print(table)
        console.print(f"\n[green]Total:[/green] {len(icon_names)} icon(s)")

    except Exception as e:
        logger.error(f"Failed to list icons: {e}")
        if verbose:
            raise
        sys.exit(1)
