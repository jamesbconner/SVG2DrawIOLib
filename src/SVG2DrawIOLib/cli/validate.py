"""Validate command - Validate DrawIO library files for correctness and integrity."""

import logging
from pathlib import Path

import rich_click as rc
from rich.table import Table

from SVG2DrawIOLib.cli.helpers import console, setup_logging
from SVG2DrawIOLib.validator import LibraryValidator


@rc.command()
@rc.argument(
    "library_file",
    type=rc.Path(exists=True, dir_okay=False, path_type=Path),
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
def validate(
    library_file: Path,
    verbose: bool,
    quiet: bool,
) -> None:
    """[bold cyan]Validate a DrawIO library file.[/]

    \b
    \nValidates library file structure, XML schema, mxGraphModel integrity,
    compression/decompression, and SVG content.

    \b
    Examples:
        Validate a library:
        $ SVG2DrawIOLib validate my-library.xml


        Validate with verbose output:
        $ SVG2DrawIOLib validate my-library.xml --verbose
    """
    setup_logging(verbose, quiet)
    logger = logging.getLogger(__name__)

    try:
        logger.debug(f"Validating library: {library_file}")

        # Run validation
        validator = LibraryValidator()
        results = validator.validate(library_file)

        # Display results
        _display_validation_results(results, library_file)

        # Exit with error if validation failed
        if not results["valid"]:
            raise rc.ClickException("Library validation failed")

    except rc.ClickException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate library: {e}")
        if verbose:
            raise
        raise rc.ClickException(f"Failed to validate library: {e}") from e


def _display_validation_results(results: dict, library_path: Path) -> None:
    """Display validation results in a formatted table.

    Args:
        results: Validation results dictionary.
        library_path: Path to the library file.
    """
    # Summary
    if results["valid"]:
        console.print(f"\n[green]✓ Library validation passed:[/green] {library_path}")
    else:
        console.print(f"\n[red]✗ Library validation failed:[/red] {library_path}")

    # Checks table
    table = Table(title="Validation Checks", show_header=True)
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Details", style="dim")

    # XML structure
    status = "[green]✓ Pass[/green]" if results["checks"]["xml_structure"] else "[red]✗ Fail[/red]"
    table.add_row("XML Structure", status, "Valid mxlibrary format")

    # JSON format
    status = "[green]✓ Pass[/green]" if results["checks"]["json_format"] else "[red]✗ Fail[/red]"
    table.add_row("JSON Format", status, "Valid JSON array")

    # Icon validation
    icon_count = results["checks"]["icon_count"]
    validated = results["checks"]["icons_validated"]
    failed = results["checks"]["icons_failed"]

    if icon_count == 0:
        status = "[yellow]⚠ Empty[/yellow]"
        details = "No icons in library"
    elif failed == 0:
        status = "[green]✓ Pass[/green]"
        details = f"All {validated} icon(s) valid"
    else:
        status = "[yellow]⚠ Issues[/yellow]" if validated > 0 else "[red]✗ Fail[/red]"
        details = f"{validated} passed, {failed} with issues"

    table.add_row("Icon Validation", status, details)

    console.print(table)

    # Errors
    if results["errors"]:
        console.print("\n[red bold]Errors:[/red bold]")
        for error in results["errors"]:
            console.print(f"  [red]✗[/red] {error}")

    # Warnings
    if results["warnings"]:
        console.print("\n[yellow bold]Warnings:[/yellow bold]")
        for warning in results["warnings"]:
            console.print(f"  [yellow]⚠[/yellow] {warning}")

    # Icon issues
    if results["icon_issues"]:
        console.print("\n[yellow bold]Icon Issues:[/yellow bold]")
        for issue in results["icon_issues"]:
            severity_color = "red" if issue["severity"] == "error" else "yellow"
            severity_icon = "✗" if issue["severity"] == "error" else "⚠"
            console.print(
                f"  [{severity_color}]{severity_icon}[/{severity_color}] "
                f"[cyan]{issue['icon']}[/cyan]: {issue['message']}"
            )

    console.print()
