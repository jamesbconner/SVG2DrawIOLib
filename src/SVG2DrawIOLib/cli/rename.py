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
        # Validate names
        if not old_name.strip():
            console.print("[red]Error:[/red] Old name cannot be empty", style="bold")
            raise rc.ClickException("Old name cannot be empty")

        if not new_name.strip():
            console.print("[red]Error:[/red] New name cannot be empty", style="bold")
            raise rc.ClickException("New name cannot be empty")

        if old_name == new_name:
            console.print(
                "[yellow]Warning:[/yellow] Old and new names are identical. No changes made.",
                style="bold",
            )
            return

        # Load library
        manager = LibraryManager()
        icons = manager.load_library(library_file)

        if not icons:
            console.print("[red]Error:[/red] Library is empty", style="bold")
            raise rc.ClickException("Library is empty")

        # Find the icon to rename
        icon_to_rename = None
        icon_index = -1
        for i, icon in enumerate(icons):
            if icon.name == old_name:
                icon_to_rename = icon
                icon_index = i
                break

        if icon_to_rename is None:
            console.print(
                f"[red]Error:[/red] Icon '{old_name}' not found in library", style="bold"
            )
            raise rc.ClickException(f"Icon '{old_name}' not found in library")

        # Check if new name already exists
        existing_icon_index = -1
        for i, icon in enumerate(icons):
            if icon.name == new_name:
                existing_icon_index = i
                break

        if existing_icon_index != -1:
            if not overwrite:
                console.print(
                    f"[red]Error:[/red] Icon '{new_name}' already exists in library. Use --overwrite to replace it.",
                    style="bold",
                )
                raise rc.ClickException(
                    f"Icon '{new_name}' already exists in library. Use --overwrite to replace it."
                )
            # Remove the existing icon with the new name
            icons.pop(existing_icon_index)
            # Adjust icon_index if needed
            if existing_icon_index < icon_index:
                icon_index -= 1
            logger.debug(f"Removed existing icon '{new_name}' (overwrite mode)")

        # Rename the icon
        from SVG2DrawIOLib.models import DrawIOIcon

        renamed_icon = DrawIOIcon(
            name=new_name,
            xml_data=icon_to_rename.xml_data,
            dimensions=icon_to_rename.dimensions,
        )
        icons[icon_index] = renamed_icon

        logger.debug(f"Renamed icon: {old_name} -> {new_name}")

        # Save the updated library
        metadata = manager.create_library(icons, library_file)

        logger.info(f"Successfully renamed icon in library: {library_file}")
        console.print(
            f"[green]✓[/green] Renamed icon '{old_name}' to '{new_name}' in [cyan]{library_file}[/cyan]"
        )
        console.print(f"    Library contains {metadata.icon_count} icon(s)")

    except rc.ClickException:
        # Re-raise ClickException from inner handlers without wrapping
        raise
    except Exception as e:
        logger.error(f"Failed to rename icon: {e}")
        if verbose:
            raise
        raise rc.ClickException(f"Failed to rename icon: {e}") from e
