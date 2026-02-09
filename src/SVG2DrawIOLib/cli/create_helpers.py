"""Helper functions for create command."""

import logging
from collections import defaultdict
from pathlib import Path

from SVG2DrawIOLib.models import DrawIOIcon, SVGProcessingOptions
from SVG2DrawIOLib.svg_processor import SVGProcessor

logger = logging.getLogger(__name__)


def collect_svg_files(
    paths: tuple[Path, ...],
    recursive: bool = False,
) -> list[Path]:
    """Collect SVG files from given paths.

    Args:
        paths: Tuple of file and/or directory paths.
        recursive: Whether to search directories recursively.

    Returns:
        List of SVG file paths.
    """
    svg_files = []

    for path in paths:
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

    return svg_files


def group_files_by_folder(
    svg_files: list[Path],
    base_dirs: list[Path],
) -> dict[str, list[Path]]:
    """Group SVG files by their immediate subdirectory.

    Args:
        svg_files: List of SVG file paths.
        base_dirs: List of base directory paths.

    Returns:
        Dictionary mapping folder names to lists of SVG files.

    Note:
        Files not relative to any base_dir are silently skipped.
        This is intentional for --split-by-folder mode.
    """
    folder_groups: dict[str, list[Path]] = defaultdict(list)
    skipped_files: list[Path] = []

    for svg_file in svg_files:
        # Find which base_dir this file belongs to
        matched = False
        for base_dir in base_dirs:
            try:
                relative = svg_file.relative_to(base_dir)
                # Get the immediate subdirectory name (first part of relative path)
                if len(relative.parts) > 1:
                    folder_name = relative.parts[0]
                    folder_groups[folder_name].append(svg_file)
                else:
                    # File is directly in base_dir, use base_dir name
                    folder_groups[base_dir.name].append(svg_file)
                matched = True
                break
            except ValueError:
                # Not relative to this base_dir, try next
                continue

        if not matched:
            skipped_files.append(svg_file)

    # Log warning if files were skipped
    if skipped_files:
        logger.warning(
            f"Skipped {len(skipped_files)} file(s) not relative to any base directory: "
            f"{', '.join(str(f) for f in skipped_files[:3])}"
            + (f" and {len(skipped_files) - 3} more" if len(skipped_files) > 3 else "")
        )

    return dict(folder_groups)


def determine_sizing_strategy(
    width: float | None,
    height: float | None,
    max_size: float | None,
) -> tuple[float | None, bool]:
    """Determine the sizing strategy based on provided options.

    Args:
        width: Fixed width in pixels.
        height: Fixed height in pixels.
        max_size: Maximum dimension for proportional scaling.

    Returns:
        Tuple of (max_dimension, has_warning) where max_dimension is None
        for fixed dimensions or default sizing, and has_warning indicates
        if a warning should be shown.
    """
    has_warning = False

    if width is not None and height is not None:
        # Fixed dimensions - will be handled per-icon
        max_dimension = None
        logger.info(f"Using fixed dimensions: {width}x{height}")
    elif width is not None or height is not None:
        # Only one dimension specified - warn user
        has_warning = True
        max_dimension = None
        logger.warning("Only one dimension specified, using default sizing")
    elif max_size is not None:
        max_dimension = max_size
        logger.info(f"Using proportional scaling with max dimension: {max_size}")
    else:
        max_dimension = None
        logger.info("Using default sizing: max dimension 40 (aspect ratio preserved)")

    return max_dimension, has_warning


def process_svg_files(
    svg_files: list[Path],
    options: SVGProcessingOptions,
    width: float | None = None,
    height: float | None = None,
    max_dimension: float | None = None,
) -> list[DrawIOIcon]:
    """Process SVG files into DrawIO icons.

    Args:
        svg_files: List of SVG file paths to process.
        options: SVG processing options.
        width: Fixed width in pixels (optional).
        height: Fixed height in pixels (optional).
        max_dimension: Maximum dimension for proportional scaling (optional).

    Returns:
        List of processed DrawIO icons.

    Raises:
        Exception: If any SVG file fails to process.
    """
    processor = SVGProcessor(options)
    icons = []

    logger.info(f"Processing {len(svg_files)} SVG file(s)")

    for svg_path in svg_files:
        # If fixed dimensions specified, pass them to processor
        if width is not None and height is not None:
            icon = processor.process_svg_file(svg_path, fixed_dimensions=(width, height))
        else:
            icon = processor.process_svg_file(svg_path, max_dimension=max_dimension)

        icons.append(icon)

    return icons


def generate_output_path(base_output: Path, folder_name: str) -> Path:
    """Generate output path with folder name suffix.

    Args:
        base_output: Base output path (e.g., FontAwesome.xml).
        folder_name: Folder name to append (e.g., "Regular").

    Returns:
        Modified output path (e.g., FontAwesome-Regular.xml).
    """
    output_stem = base_output.stem
    output_suffix = base_output.suffix
    return base_output.parent / f"{output_stem}-{folder_name}{output_suffix}"
