"""Create command - Create a new DrawIO library from SVG files."""

import logging
from pathlib import Path

import rich_click as rc

from SVG2DrawIOLib.cli.create_helpers import (
    collect_svg_files,
    determine_sizing_strategy,
    generate_output_path,
    group_files_by_folder,
    process_svg_files,
)
from SVG2DrawIOLib.cli.helpers import console, setup_logging
from SVG2DrawIOLib.library_manager import LibraryManager
from SVG2DrawIOLib.models import SVGProcessingOptions


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
@rc.option(
    "--split-by-folder",
    "-S",
    is_flag=True,
    help="Create separate libraries for each subdirectory (requires --recursive). "
    "Output filename will be modified with subdirectory name (e.g., lib.xml -> lib-FolderName.xml).",
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
    split_by_folder: bool,
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


        Create separate libraries per subdirectory:
        $ SVG2DrawIOLib create icons/ -o FontAwesome.xml -R --split-by-folder
        # Creates: FontAwesome-Regular.xml, FontAwesome-Solid.xml, etc.


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
        # Validate conflicting options
        if split_by_folder and not recursive:
            console.print("[red]Error:[/red] --split-by-folder requires --recursive", style="bold")
            raise rc.ClickException("--split-by-folder requires --recursive")

        # Collect all SVG files from paths
        svg_files = collect_svg_files(svg_paths, recursive)
        base_dirs = [p for p in svg_paths if p.is_dir()]

        # Validate we found files
        if not svg_files:
            console.print("[red]Error:[/red] No SVG files found in specified paths", style="bold")
            raise rc.ClickException("No SVG files found in specified paths")

        # If split-by-folder, group files by their immediate subdirectory
        folder_groups: dict[str, list[Path]] = {}
        if split_by_folder:
            if not base_dirs:
                console.print(
                    "[red]Error:[/red] --split-by-folder requires at least one directory path",
                    style="bold",
                )
                raise rc.ClickException("--split-by-folder requires at least one directory path")

            folder_groups = group_files_by_folder(svg_files, base_dirs)

            if not folder_groups:
                console.print(
                    "[yellow]Warning:[/yellow] No subdirectories found, creating single library",
                    style="bold",
                )
                split_by_folder = False
            else:
                logger.info(
                    f"Split by folder: found {len(folder_groups)} subdirectories with SVG files"
                )

        # Determine sizing strategy
        max_dimension, has_sizing_warning = determine_sizing_strategy(width, height, max_size)
        if has_sizing_warning:
            console.print(
                "[yellow]Warning:[/yellow] Both --width and --height must be specified for fixed dimensions. "
                "Using default sizing instead.",
                style="bold",
            )

        # Create processing options
        options = SVGProcessingOptions(
            add_css=css,
            css_color=css_color,
            xml_namespace=namespace,
            css_tag=tag,
        )

        # Initialize library manager
        manager = LibraryManager()

        if split_by_folder:
            # Create separate libraries for each folder
            created_libraries = []

            for folder_name, folder_files in sorted(folder_groups.items()):
                logger.info(f"Processing folder '{folder_name}' with {len(folder_files)} file(s)")

                try:
                    icons = process_svg_files(folder_files, options, width, height, max_dimension)
                except Exception as e:
                    logger.error(f"Failed to process folder '{folder_name}': {e}")
                    if verbose:
                        raise
                    raise rc.ClickException(f"Failed to process folder '{folder_name}': {e}") from e

                # Generate output filename with folder name
                folder_output = generate_output_path(output, folder_name)

                # Create library for this folder
                metadata = manager.create_library(icons, folder_output, source_files=folder_files)
                created_libraries.append((folder_output, metadata.icon_count))

                logger.info(f"Created library: {folder_output} with {metadata.icon_count} icon(s)")

            # Summary
            console.print(f"[green]✓[/green] Created {len(created_libraries)} libraries by folder:")
            for lib_path, icon_count in created_libraries:
                console.print(f"  [cyan]{lib_path.name}[/cyan]: {icon_count} icon(s)")

        else:
            # Create single library with all files
            try:
                icons = process_svg_files(svg_files, options, width, height, max_dimension)
            except Exception as e:
                logger.error(f"Failed to process SVG files: {e}")
                if verbose:
                    raise
                raise rc.ClickException(f"Failed to process SVG files: {e}") from e

            # Create library
            metadata = manager.create_library(icons, output, source_files=svg_files)

            logger.info(f"Successfully created library: {output}")
            console.print(
                f"[green]✓[/green] Created library with {metadata.icon_count} icon(s): "
                f"[cyan]{output}[/cyan]"
            )

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise rc.Abort() from None
    except rc.ClickException:
        # Re-raise ClickException from inner handlers without wrapping
        raise
    except Exception as e:
        logger.error(f"Failed to create library: {e}")
        if verbose:
            raise
        raise rc.ClickException(f"Failed to create library: {e}") from e
