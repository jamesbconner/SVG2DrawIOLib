"""Rename icons in a DrawIO library."""

import logging
from pathlib import Path

import rich_click as rc
from rich.console import Console

from SVG2DrawIOLib.cli.helpers import setup_logging
from SVG2DrawIOLib.library_manager import LibraryManager

console = Console()


@rc.command()
@rc.option(
    "--library",
    "-l",
    "library_file",
    type=rc.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to the DrawIO library file (.xml)",
)
@rc.option(
    "--old-name",
    "-o",
    "old_name",
    type=str,
    required=True,
    help="Current name of the icon to rename",
)
@rc.option(
    "--new-name",
    "-n",
    "new_name",
    type=str,
    required=True,
    help="New name for the icon",
)
@rc.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite if an icon with the new name already exists",
)
@rc.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
@rc.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Suppress all output except errors",
)
def rename(
    library_file: Path,
    old_name: str,
    new_name: str,
    overwrite: bool,
    verbose: bool,
    quiet: bool,
) -> None:
    """
    [bold cyan]Rename an icon in a DrawIO library[/bold cyan]

    \b
    \nRenames a single icon within a DrawIO shape library. The icon's content
    remains unchanged, only its name is updated.

    \b
    Examples:
      # Rename an icon
      SVG2DrawIOLib rename -l icons.xml -o old-icon-name -n new-icon-name


      # Rename with verbose output
      SVG2DrawIOLib rename -l icons.xml -o icon1 -n icon2 -v


      # Overwrite existing icon with the new name
      SVG2DrawIOLib rename -l icons.xml -o icon1 -n icon2 --overwrite
    """
    setup_logging(verbose, quiet)
    logger = logging.getLogger(__name__)

    try:
        manager = LibraryManager()

        # Rename the icon using the service
        try:
            metadata, was_overwritten = manager.rename_icon(
                library_file, old_name, new_name, overwrite
            )

            # Check if names were identical (no actual rename)
            if old_name == new_name:
                console.print(
                    "[yellow]Warning:[/yellow] Old and new names are identical. No changes made.",
                    style="bold",
                )
                return

            logger.info(f"Successfully renamed icon in library: {library_file}")
            console.print(
                f"[green]✓[/green] Renamed icon '{old_name}' to '{new_name}' in [cyan]{library_file}[/cyan]"
            )
            if was_overwritten:
                console.print(f"    [yellow]⚠[/yellow] Replaced existing icon '{new_name}'")
            console.print(f"    Library contains {metadata.icon_count} icon(s)")

        except ValueError as e:
            # Convert ValueError to ClickException with appropriate message
            error_msg = str(e)
            # Fix the error message to mention --overwrite flag instead of overwrite=True
            if "Use overwrite=True" in error_msg:
                error_msg = error_msg.replace("Use overwrite=True", "Use --overwrite")
            console.print(f"[red]Error:[/red] {error_msg}", style="bold")
            raise rc.ClickException(error_msg) from e

    except rc.ClickException:
        # Re-raise ClickException from inner handlers without wrapping
        raise
    except Exception as e:
        logger.error(f"Failed to rename icon: {e}")
        if verbose:
            raise
        raise rc.ClickException(f"Failed to rename icon: {e}") from e
