"""Remove command - Remove icons from a DrawIO library by name."""

import logging
import sys
from pathlib import Path

import rich_click as rc

from SVG2DrawIOLib.cli.helpers import console, setup_logging
from SVG2DrawIOLib.library_manager import LibraryManager


@rc.command()
@rc.argument(
    "library_file",
    type=rc.Path(exists=True, dir_okay=False, path_type=Path),
)
@rc.argument("icon_names", nargs=-1, required=True, metavar="ICON_NAMES...")
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
def remove(
    library_file: Path,
    icon_names: tuple[str, ...],
    verbose: bool,
    quiet: bool,
) -> None:
    """Remove icons from a DrawIO library by name.

    Removes one or more icons from an existing library file.

    Examples:
        Remove single icon:
        $ SVG2DrawIOLib remove my-library.xml old-icon


        Remove multiple icons:
        $ SVG2DrawIOLib remove my-library.xml icon1 icon2 icon3
    """
    setup_logging(verbose, quiet)
    logger = logging.getLogger(__name__)

    try:
        logger.debug(f"Removing icons from library: {library_file}")
        logger.debug(f"Icons to remove: {', '.join(icon_names)}")

        manager = LibraryManager()
        metadata, removed_count = manager.remove_icons_from_library(library_file, list(icon_names))

        if removed_count == 0:
            logger.warning("No icons were removed")
            console.print(
                "[yellow]Warning:[/yellow] No icons were removed. "
                "Requested icons not found in library."
            )
        else:
            logger.info(f"Successfully removed {removed_count} icon(s) from library")
            console.print(
                f"[green]✓[/green] Removed {removed_count} icon(s). "
                f"Library now has {metadata.icon_count} icon(s): [cyan]{library_file}[/cyan]"
            )

    except Exception as e:
        logger.error(f"Error: {e}")
        if verbose:
            raise
        sys.exit(1)
