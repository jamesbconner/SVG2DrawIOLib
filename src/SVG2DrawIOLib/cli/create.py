"""Create command - Create a new DrawIO library from SVG files."""

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
    "svg_paths",
    nargs=-1,
    required=True,
    type=rc.Path(exists=True, path_type=Path),
    metavar="PATHS...",
)
@rc.option(
    "--output",
    "-o",
    type=rc.Path(path_type=Path),
    required=True,
    help="Output library file path (e.g., my-library.xml).",
)
@rc.option(
    "--max-size",
    "-s",
    type=float,
    help="Maximum dimension (width or height) in pixels. Icons are scaled proportionally.",
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
    help="Add CSS classes to enable color editing in DrawIO.",
)
@rc.option(
    "--css-color",
    default="#000000",
    show_default=True,
    help="Default CSS fill color (requires --css).",
)
@rc.option(
    "--namespace",
    "-n",
    default="http://www.w3.org/2000/svg",
    show_default=True,
    help="XML namespace for SVG elements.",
)
@rc.option(
    "--tag",
    "-t",
    default="path",
    show_default=True,
    help="XML tag to add CSS classes to (requires --css).",
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
def create(
    svg_paths: tuple[Path, ...],
    output: Path,
    max_size: float | None,
    width: float | None,
    height: float | None,
    css: bool,
    css_color: str,
    namespace: str,
    tag: str,
    verbose: bool,
    quiet: bool,
    recursive: bool,
) -> None:
    """[bold cyan]Create a new DrawIO library from SVG files.[/]

    \b
    \nConverts one or more SVG files into a DrawIO library XML file.
    Icons can be scaled proportionally or set to fixed dimensions.

    \b
    Accepts individual SVG files, directories, or a mix of both.
    Use --recursive to search subdirectories.

    \b
    Scaling Options:
        --max-size: Scale icons proportionally (longest side = max-size)
        --width/--height: Set fixed dimensions (ignores aspect ratio)
        Neither: Use default 40x40 pixels

    \b
    Examples:
        Create from individual files:
        $ SVG2DrawIOLib create icon1.svg icon2.svg -o lib.xml


        Create from directory:
        $ SVG2DrawIOLib create icons/ -o lib.xml


        Create from directory recursively:
        $ SVG2DrawIOLib create icons/ -o lib.xml --recursive


        Create with proportional scaling (max 64px):
        $ SVG2DrawIOLib create icons/ -o lib.xml --max-size 64 -R


        Create with fixed dimensions:
        $ SVG2DrawIOLib create icons/*.svg -o lib.xml -w 50 -h 50


        Enable color editing:
        $ SVG2DrawIOLib create icons/ -o lib.xml --css
    """
    setup_logging(verbose, quiet)
    logger = logging.getLogger(__name__)

    try:
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
        elif width is not None or height is not None:
            # Only one dimension specified - warn user
            console.print(
                "[yellow]Warning:[/yellow] Both --width and --height must be specified for fixed dimensions. "
                "Using default sizing instead.",
                style="bold",
            )
            max_dimension = None
            logger.warning("Only one dimension specified, using default sizing")
        elif max_size is not None:
            max_dimension = max_size
            logger.info(f"Using proportional scaling with max dimension: {max_size}")
        else:
            max_dimension = None
            logger.info("Using default sizing: max dimension 40 (aspect ratio preserved)")

        # Create processing options
        options = SVGProcessingOptions(
            add_css=css,
            css_color=css_color,
            xml_namespace=namespace,
            css_tag=tag,
        )

        # Process SVG files
        processor = SVGProcessor(options)
        icons = []

        logger.info(f"Processing {len(svg_files)} SVG file(s)")

        for svg_path in svg_files:
            try:
                # If fixed dimensions specified, pass them to processor
                if width is not None and height is not None:
                    icon = processor.process_svg_file(svg_path, fixed_dimensions=(width, height))
                else:
                    icon = processor.process_svg_file(svg_path, max_dimension=max_dimension)

                icons.append(icon)

            except Exception as e:
                logger.error(f"Failed to process {svg_path}: {e}")
                if verbose:
                    raise
                sys.exit(1)

        # Create library
        manager = LibraryManager()
        metadata = manager.create_library(icons, output)

        logger.info(f"Successfully created library: {output}")
        console.print(
            f"[green]✓[/green] Created library with {metadata.icon_count} icon(s): "
            f"[cyan]{output}[/cyan]"
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Failed to create library: {e}")
        if verbose:
            raise
        sys.exit(1)
