"""Add command - Add SVG icons to an existing DrawIO library."""

import logging
import sys
from pathlib import Path

import rich_click as rc

from SVG2DrawIOLib.cli.helpers import console, setup_logging
from SVG2DrawIOLib.library_manager import LibraryManager
from SVG2DrawIOLib.models import SVGProcessingOptions
from SVG2DrawIOLib.svg_processor import SVGProcessor


@rc.command()
@rc.argument(
    "library_file",
    type=rc.Path(exists=True, dir_okay=False, path_type=Path),
)
@rc.argument(
    "svg_paths",
    nargs=-1,
    required=True,
    type=rc.Path(exists=True, path_type=Path),
    metavar="PATHS...",
)
@rc.option(
    "--replace",
    "-r",
    is_flag=True,
    help="Replace icons with duplicate names (default: skip duplicates).",
)
@rc.option(
    "--add-dupes",
    "-d",
    is_flag=True,
    help="Add duplicate icons with modified names instead of skipping.",
)
@rc.option(
    "--max-size",
    "-s",
    type=float,
    help="Maximum dimension for new icons (scaled proportionally).",
)
@rc.option(
    "--width",
    "-w",
    type=float,
    help="Fixed width in pixels (overrides --max-size).",
)
@rc.option(
    "--height",
    "-h",
    type=float,
    help="Fixed height in pixels (overrides --max-size).",
)
@rc.option(
    "--css/--no-css",
    "-c/-C",
    default=False,
    help="Add CSS classes to new icons for color editing.",
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
@rc.option(
    "--recursive",
    "-R",
    is_flag=True,
    help="Recursively search directories for SVG files.",
)
def add(
    library_file: Path,
    svg_paths: tuple[Path, ...],
    replace: bool,
    add_dupes: bool,
    max_size: float | None,
    width: float | None,
    height: float | None,
    css: bool,
    verbose: bool,
    quiet: bool,
    recursive: bool,
) -> None:
    """Add SVG icons to an existing DrawIO library.

    Processes SVG files and adds them to an existing library.
    By default, skips icons with duplicate names.

    Accepts individual SVG files, directories, or a mix of both.
    Use --recursive to search subdirectories.

    \b
    Duplicate Handling:
        Default: Skip icons with duplicate names
        --replace: Replace existing icons with same names
        --add-dupes: Add duplicates with modified names (e.g., icon_2, icon_3)

    \b
    Scaling Options:
        --max-size: Scale icons proportionally (longest side = max-size)
        --width/--height: Set fixed dimensions (ignores aspect ratio)
        Neither: Use original dimensions or library defaults

    Examples:
        Add individual files:
        $ SVG2DrawIOLib add my-library.xml new-icon1.svg new-icon2.svg


        Add from directory:
        $ SVG2DrawIOLib add my-library.xml icons/


        Add from directory recursively:
        $ SVG2DrawIOLib add my-library.xml icons/ --recursive


        Replace existing icons with same names:
        $ SVG2DrawIOLib add my-library.xml icons/ --replace


        Add duplicates with modified names:
        $ SVG2DrawIOLib add my-library.xml icons/ --add-dupes


        Add with proportional scaling:
        $ SVG2DrawIOLib add my-library.xml icons/ --max-size 64 -R


        Add with fixed dimensions:
        $ SVG2DrawIOLib add my-library.xml icons/ -w 50 -h 50
    """
    setup_logging(verbose, quiet)
    logger = logging.getLogger(__name__)

    try:
        # Validate conflicting options
        if replace and add_dupes:
            console.print(
                "[red]Error:[/red] Cannot use both --replace and --add-dupes", style="bold"
            )
            sys.exit(1)

        # Collect all SVG files from paths (files and/or directories)
        svg_files = []
        for path in svg_paths:
            if path.is_file():
                if path.suffix.lower() == ".svg":
                    svg_files.append(path)
                else:
                    logger.warning(f"Skipping non-SVG file: {path}")
            elif path.is_dir():
                if recursive:
                    # Recursively find all .svg files
                    found = list(path.rglob("*.svg"))
                    svg_files.extend(found)
                    logger.debug(f"Found {len(found)} SVG file(s) in {path} (recursive)")
                else:
                    # Only direct children
                    found = list(path.glob("*.svg"))
                    svg_files.extend(found)
                    logger.debug(f"Found {len(found)} SVG file(s) in {path}")
            else:
                logger.warning(f"Path does not exist or is not accessible: {path}")

        # Validate we found files
        if not svg_files:
            console.print("[red]Error:[/red] No SVG files found in specified paths", style="bold")
            sys.exit(1)

        # Determine sizing strategy
        if width is not None and height is not None:
            # Fixed dimensions - will be handled per-icon
            max_dimension = None
            logger.info(f"Using fixed dimensions: {width}x{height}")
        elif max_size is not None:
            max_dimension = max_size
            logger.info(f"Using proportional scaling with max dimension: {max_size}")
        else:
            max_dimension = None
            logger.info("Using original dimensions")

        # Create processing options
        options = SVGProcessingOptions(add_css=css)

        # Process new SVG files
        processor = SVGProcessor(options)
        new_icons = []

        logger.info(f"Processing {len(svg_files)} SVG file(s)")

        for svg_path in svg_files:
            try:
                # If fixed dimensions specified, override max_dimension
                if width is not None and height is not None:
                    icon = processor.process_svg_file(svg_path, max_dimension=None)
                    # Override dimensions
                    from SVG2DrawIOLib.models import SVGDimensions

                    icon.dimensions = SVGDimensions(width=width, height=height)
                else:
                    icon = processor.process_svg_file(svg_path, max_dimension=max_dimension)

                new_icons.append(icon)
            except Exception as e:
                logger.error(f"Failed to process {svg_path}: {e}")
                if verbose:
                    raise
                sys.exit(1)

        # Add to library
        manager = LibraryManager()

        # Determine duplicate handling strategy
        if add_dupes:
            # TODO: Implement add_dupes functionality in LibraryManager
            # For now, use replace_duplicates=False (skip)
            logger.warning("--add-dupes functionality not yet implemented, skipping duplicates")
            metadata = manager.add_icons_to_library(
                library_file, new_icons, replace_duplicates=False
            )
        else:
            metadata = manager.add_icons_to_library(
                library_file, new_icons, replace_duplicates=replace
            )

        console.print(
            f"[green]✓[/green] Updated library with {metadata.icon_count} total icon(s): "
            f"[cyan]{library_file}[/cyan]"
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        if verbose:
            raise
        sys.exit(1)
