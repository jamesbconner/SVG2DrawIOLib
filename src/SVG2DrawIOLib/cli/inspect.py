"""Inspect command - Display detailed information about icons in a DrawIO library."""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import rich_click as rc
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from SVG2DrawIOLib.cli.helpers import console, setup_logging
from SVG2DrawIOLib.icon_analyzer import IconAnalyzer
from SVG2DrawIOLib.library_manager import LibraryManager

if TYPE_CHECKING:
    from SVG2DrawIOLib.models import DrawIOIcon


@rc.command()
@rc.option(
    "--library",
    "-l",
    type=rc.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to the DrawIO library file.",
)
@rc.option(
    "--icons",
    "-i",
    multiple=True,
    help="Specific icon name(s) to inspect. If not provided, inspects all icons.",
)
@rc.option(
    "--show-svg",
    "-s",
    is_flag=True,
    help="Display the decoded SVG content for each icon.",
)
@rc.option(
    "--json",
    "-j",
    "output_json",
    is_flag=True,
    help="Output results in JSON format.",
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
def inspect(
    library: Path,
    icons: tuple[str, ...],
    show_svg: bool,
    output_json: bool,
    verbose: bool,
    quiet: bool,
) -> None:
    """[bold cyan]Inspect icons in a DrawIO library.[/]

    \b
    \nDisplays detailed information about icons including dimensions, style/CSS hooks,
    and optionally the decoded SVG content.

    \b
    Examples:
        Inspect all icons:
        $ SVG2DrawIOLib inspect -l my-library.xml


        Inspect specific icons:
        $ SVG2DrawIOLib inspect -l my-library.xml -i icon1 -i icon2


        Inspect with SVG content:
        $ SVG2DrawIOLib inspect -l my-library.xml --show-svg


        Output as JSON:
        $ SVG2DrawIOLib inspect -l my-library.xml --json
    """
    setup_logging(verbose, quiet)
    logger = logging.getLogger(__name__)

    try:
        logger.debug(f"Inspecting library: {library}")

        # Load library
        manager = LibraryManager()
        icons_list = manager.load_library(library)

        if not icons_list:
            logger.info("Library is empty")
            if output_json:
                print(
                    json.dumps(
                        {
                            "library": str(library),
                            "total_icons": 0,
                            "inspected_count": 0,
                            "icons": [],
                        }
                    )
                )
            else:
                console.print(f"[yellow]Library is empty:[/yellow] {library}")
            return

        # Filter icons if specific names provided
        icons_to_inspect = icons_list
        missing_icons = []
        if icons:
            icon_set = set(icons)
            icons_to_inspect = [icon for icon in icons_list if icon.name in icon_set]

            # Warn about missing icons
            found_names = {icon.name for icon in icons_to_inspect}
            missing = icon_set - found_names
            if missing:
                missing_icons = sorted(missing)
                logger.warning(f"Icons not found: {', '.join(missing_icons)}")
                if not output_json:
                    console.print(
                        f"[yellow]⚠ Warning:[/yellow] Icons not found: {', '.join(missing_icons)}"
                    )

        if not icons_to_inspect:
            logger.error("No icons to inspect")
            raise rc.ClickException("No icons found matching the specified names")

        logger.info(f"Inspecting {len(icons_to_inspect)} icon(s)")

        # Collect icon data
        if output_json:
            # JSON output mode
            icons_data = []
            for icon in icons_to_inspect:
                icon_info = _collect_icon_info(icon, show_svg, logger)
                icons_data.append(icon_info)

            result = {
                "library": str(library),
                "total_icons": len(icons_list),
                "inspected_count": len(icons_to_inspect),
                "icons": icons_data,
            }
            if missing_icons:
                result["missing_icons"] = missing_icons

            print(json.dumps(result, indent=2))
        else:
            # Rich console output mode
            for idx, icon in enumerate(icons_to_inspect, 1):
                if idx > 1:
                    console.print()  # Add spacing between icons

                _display_icon_info(icon, show_svg, logger)

            # Summary
            console.print()
            console.print(
                f"[green]✓[/green] Inspected {len(icons_to_inspect)} of {len(icons_list)} icon(s)"
            )

    except rc.ClickException:
        raise
    except Exception as e:
        logger.error(f"Failed to inspect library: {e}")
        if verbose:
            raise
        raise rc.ClickException(f"Failed to inspect library: {e}") from e


def _collect_icon_info(
    icon: "DrawIOIcon", show_svg: bool, logger: logging.Logger
) -> dict[str, Any]:
    """Collect detailed information about a single icon as a dictionary.

    Args:
        icon: DrawIOIcon to inspect.
        show_svg: Whether to include the decoded SVG content.
        logger: Logger instance for debug output.

    Returns:
        Dictionary containing icon information.
    """
    try:
        # Use IconAnalyzer to extract icon information
        analyzer = IconAnalyzer()
        icon_data = analyzer.get_icon_info(icon, include_svg=show_svg)
        logger.debug(f"Collected info for icon: {icon.name}")
        return icon_data

    except Exception as e:
        logger.error(f"Failed to collect info for icon {icon.name}: {e}")
        return {
            "name": icon.name,
            "error": str(e),
        }


def _display_icon_info(icon: "DrawIOIcon", show_svg: bool, logger: logging.Logger) -> None:
    """Display detailed information about a single icon.

    Args:
        icon: DrawIOIcon to inspect.
        show_svg: Whether to display the decoded SVG content.
        logger: Logger instance for debug output.
    """
    try:
        # Use IconAnalyzer to extract icon information
        analyzer = IconAnalyzer()
        svg_content, style_info = analyzer.extract_details(icon.xml_data)

        # Create info table
        table = Table(title=f"[bold cyan]{icon.name}[/bold cyan]", show_header=False, box=None)
        table.add_column("Property", style="bold yellow", width=15)
        table.add_column("Value", style="white")

        # Add dimensions
        table.add_row("Width", f"{icon.dimensions.width:.1f} px")
        table.add_row("Height", f"{icon.dimensions.height:.1f} px")

        # Add style information
        if style_info.shape:
            table.add_row("Shape Type", style_info.shape)

        if style_info.css_classes:
            table.add_row("CSS Classes", ", ".join(style_info.css_classes))

        if style_info.inline_styles:
            table.add_row("Inline Styles", style_info.inline_styles)

        console.print(table)

        # Display SVG content if requested
        if show_svg and svg_content:
            syntax = Syntax(svg_content, "xml", theme="monokai", line_numbers=False)
            panel = Panel(
                syntax,
                title=f"[bold cyan]SVG Content: {icon.name}[/bold cyan]",
                border_style="cyan",
            )
            console.print(panel)

        logger.debug(f"Inspected icon: {icon.name}")

    except Exception as e:
        logger.error(f"Failed to inspect icon {icon.name}: {e}")
        console.print(f"[red]✗ Error inspecting {icon.name}:[/red] {e}")
