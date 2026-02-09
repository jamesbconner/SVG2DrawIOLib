"""Extract icons from DrawIO library to SVG files."""

import logging
from pathlib import Path

import rich_click as rc
from rich.console import Console

from SVG2DrawIOLib.cli.helpers import safe_path_join, setup_logging
from SVG2DrawIOLib.icon_analyzer import IconAnalyzer
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
    "--output",
    "-o",
    "output_dir",
    type=rc.Path(file_okay=False, path_type=Path),
    required=True,
    help="Output directory for extracted SVG files",
)
@rc.option(
    "--icons",
    "-i",
    "icon_names",
    multiple=True,
    help="Specific icon names to extract (can be used multiple times). If not specified, extracts all icons.",
)
@rc.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite existing SVG files in output directory",
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
def extract(
    library_file: Path,
    output_dir: Path,
    icon_names: tuple[str, ...],
    overwrite: bool,
    verbose: bool,
    quiet: bool,
) -> None:
    """
    [bold cyan]Extract icons from a DrawIO library to individual SVG files[/bold cyan]

    \b
    \nExtracts one or more icons from a DrawIO shape library (.xml) and saves them
    as individual SVG files. This is the inverse operation of the 'create' command.

    \b
    Examples:
      # Extract all icons from library
      SVG2DrawIOLib extract -l icons.xml -o ./output


      # Extract specific icons
      SVG2DrawIOLib extract -l icons.xml -o ./output -i icon1 -i icon2


      # Overwrite existing files
      SVG2DrawIOLib extract -l icons.xml -o ./output --overwrite
    """
    setup_logging(verbose, quiet)
    logger = logging.getLogger(__name__)

    try:
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Output directory: {output_dir}")

        # Load library
        manager = LibraryManager()
        icons = manager.load_library(library_file)

        if not icons:
            console.print("[yellow]Warning:[/yellow] Library is empty", style="bold")
            return

        # Filter icons if specific names requested
        if icon_names:
            icon_names_set = set(icon_names)
            filtered_icons = [icon for icon in icons if icon.name in icon_names_set]

            # Check for requested icons that weren't found
            found_names = {icon.name for icon in filtered_icons}
            missing_names = icon_names_set - found_names
            if missing_names:
                console.print(
                    f"[yellow]Warning:[/yellow] Icons not found in library: {', '.join(sorted(missing_names))}",
                    style="bold",
                )

            icons = filtered_icons

        if not icons:
            console.print("[red]Error:[/red] No matching icons found in library", style="bold")
            raise rc.ClickException("No matching icons found in library")

        logger.info(f"Extracting {len(icons)} icon(s) from library")

        # Create analyzer
        analyzer = IconAnalyzer()

        # Extract each icon
        extracted_count = 0
        skipped_count = 0

        for icon in icons:
            output_path = safe_path_join(output_dir, f"{icon.name}.svg")

            try:
                # Extract icon to file
                was_extracted = analyzer.extract_to_file(icon, output_path, overwrite)

                if was_extracted:
                    extracted_count += 1
                else:
                    skipped_count += 1

            except ValueError as e:
                logger.error(f"Failed to extract {icon.name}: {e}")
                if verbose:
                    raise
                raise rc.ClickException(f"Failed to extract {icon.name}: {e}") from e

        # Summary
        logger.info(f"Successfully extracted {extracted_count} icon(s)")
        if skipped_count > 0:
            logger.info(f"Skipped {skipped_count} existing file(s) (use --overwrite to replace)")

        console.print(
            f"[green]✓[/green] Extracted {extracted_count} icon(s) to [cyan]{output_dir}[/cyan]"
        )
        if skipped_count > 0:
            console.print(
                f"[yellow]⚠[/yellow] Skipped {skipped_count} existing file(s) (use --overwrite to replace)"
            )

    except rc.ClickException:
        # Re-raise ClickException from inner handlers without wrapping
        raise
    except Exception as e:
        logger.error(f"Failed to extract icons: {e}")
        if verbose:
            raise
        raise rc.ClickException(f"Failed to extract icons: {e}") from e
