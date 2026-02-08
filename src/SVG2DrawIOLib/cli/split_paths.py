"""Split compound SVG paths into individual subpaths for color customization."""

import logging
import sys
from pathlib import Path

import click

from SVG2DrawIOLib.cli.helpers import setup_logging
from SVG2DrawIOLib.path_splitter import PathSplitter


@click.command(name="split-paths")
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    required=True,
    help="Output SVG file path",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
def split_paths(input_file: Path, output: Path, verbose: bool) -> None:
    """Split compound SVG paths into individual subpaths.

    This command splits SVG paths that contain multiple shapes (indicated by
    multiple M/m commands) into separate path elements. This enables per-path
    color customization when used with DrawIO's CSS editing feature.

    The command automatically detects and preserves "donut holes" (paths contained
    within other paths) to maintain cutout effects.

    Example:

        SVG2DrawIOLib split-paths icon.svg -o icon-split.svg

    The output SVG can then be used with the 'create' or 'add' commands with
    the --css flag to enable color editing in DrawIO.
    """
    setup_logging(verbose, quiet=False)
    logger = logging.getLogger(__name__)

    logger.info(f"Splitting paths in: {input_file}")

    try:
        splitter = PathSplitter()
        result = splitter.split_svg_paths(input_file, output)

        logger.info(f"Successfully split {result['paths_processed']} path(s)")
        logger.info(f"Created {result['subpaths_created']} subpath(s)")
        logger.info(f"Preserved {result['holes_preserved']} hole(s)")
        logger.info(f"Output written to: {output}")

    except ImportError as e:
        logger.error(f"Missing required dependency: {e}")
        logger.error("Path splitting requires svgelements library")
        raise click.Abort() from e
    except Exception as e:
        logger.error(f"Failed to split paths: {e}")
        if verbose:
            raise
        sys.exit(1)
