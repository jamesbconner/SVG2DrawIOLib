"""Command-line interface for SVG2DrawIOLib with dynamic command loading."""

import importlib
import logging
from pathlib import Path

import rich_click as rc

from SVG2DrawIOLib.__about__ import __version__

# Configure rich-click for beautiful, colorful help output
rc.rich_click.TEXT_MARKUP = "rich"
rc.rich_click.SHOW_ARGUMENTS = True
rc.rich_click.GROUP_ARGUMENTS_OPTIONS = True
rc.rich_click.OPTIONS_TABLE_COLUMN_TYPES = ["required", "opt_short", "opt_long", "help"]
rc.rich_click.OPTIONS_TABLE_HELP_SECTIONS = ["help", "deprecated", "envvar", "default", "required"]
rc.rich_click.STYLE_ERRORS_SUGGESTION = "magenta italic"
rc.rich_click.ERRORS_SUGGESTION = "Try running the '--help' flag for more information."
rc.rich_click.ERRORS_EPILOGUE = ""
rc.rich_click.MAX_WIDTH = 100
rc.rich_click.COLOR_SYSTEM = "auto"

# Style configuration
rc.rich_click.STYLE_OPTION = "bold cyan"
rc.rich_click.STYLE_ARGUMENT = "bold yellow"
rc.rich_click.STYLE_COMMAND = "bold green"
rc.rich_click.STYLE_SWITCH = "bold blue"
rc.rich_click.STYLE_METAVAR = "bold magenta"
rc.rich_click.STYLE_METAVAR_APPEND = "dim"
rc.rich_click.STYLE_METAVAR_SEPARATOR = "dim"
rc.rich_click.STYLE_HEADER_TEXT = "bold"
rc.rich_click.STYLE_FOOTER_TEXT = "dim"
rc.rich_click.STYLE_USAGE = "bold yellow"
rc.rich_click.STYLE_USAGE_COMMAND = "bold"
rc.rich_click.STYLE_DEPRECATED = "red"
rc.rich_click.STYLE_HELPTEXT_FIRST_LINE = "bold"
rc.rich_click.STYLE_HELPTEXT = ""
rc.rich_click.STYLE_OPTION_HELP = ""
rc.rich_click.STYLE_OPTION_DEFAULT = "dim"
rc.rich_click.STYLE_REQUIRED_SHORT = "red"
rc.rich_click.STYLE_REQUIRED_LONG = "red"
rc.rich_click.ALIGN_OPTIONS_PANEL = "left"
rc.rich_click.ALIGN_ARGUMENTS_PANEL = "left"

# Command groups for organized help
rc.rich_click.COMMAND_GROUPS = {
    "SVG2DrawIOLib": [
        {
            "name": "Library Management Commands",
            "commands": ["create", "add", "remove", "list", "extract"],
            "table_styles": {
                "show_lines": True,
                "row_styles": ["none"],
                "border_style": "blue",
                "box": "ROUNDED",
            },
        },
        {
            "name": "SVG Processing Commands",
            "commands": ["split-paths"],
            "table_styles": {
                "show_lines": True,
                "row_styles": ["none"],
                "border_style": "green",
                "box": "ROUNDED",
            },
        },
    ]
}

# Option groups for better organization
rc.rich_click.OPTION_GROUPS = {
    "SVG2DrawIOLib create": [
        {
            "name": "Required Options",
            "options": ["--output"],
        },
        {
            "name": "Sizing Options",
            "options": ["--max-size", "--width", "--height"],
        },
        {
            "name": "Styling Options",
            "options": ["--css", "--css-color", "--namespace", "--tag"],
        },
        {
            "name": "General Options",
            "options": ["--recursive", "--verbose", "--quiet", "--help"],
        },
    ],
    "SVG2DrawIOLib add": [
        {
            "name": "Duplicate Handling",
            "options": ["--replace", "--add-dupes"],
        },
        {
            "name": "Sizing Options",
            "options": ["--max-size", "--width", "--height"],
        },
        {
            "name": "Styling Options",
            "options": ["--css"],
        },
        {
            "name": "General Options",
            "options": ["--recursive", "--verbose", "--quiet", "--help"],
        },
    ],
    "SVG2DrawIOLib remove": [
        {
            "name": "Options",
            "options": ["--verbose", "--quiet", "--help"],
        },
    ],
    "SVG2DrawIOLib list": [
        {
            "name": "Options",
            "options": ["--verbose", "--quiet", "--help"],
        },
    ],
    "SVG2DrawIOLib split-paths": [
        {
            "name": "Required Options",
            "options": ["--output"],
        },
        {
            "name": "General Options",
            "options": ["--verbose", "--help"],
        },
    ],
}

logger = logging.getLogger(__name__)


@rc.group()
@rc.version_option(version=__version__, prog_name="SVG2DrawIOLib")
def cli() -> None:
    """[bold cyan]SVG2DrawIOLib - Manage DrawIO/diagrams.net shape libraries.[/]

    \b
    \nConvert SVG files into DrawIO libraries and manage existing libraries.
    Supports color-editable icons and proportional scaling.

    \b
    Examples:
        Create a new library from SVG files:
        $ SVG2DrawIOLib create icons/*.svg -o my-library.xml


        Add icons to an existing library:
        $ SVG2DrawIOLib add my-library.xml new-icon.svg


        List icons in a library:
        $ SVG2DrawIOLib list my-library.xml
    """
    pass


# Dynamic discovery: auto-register all CLI commands from cli/ directory
COMMAND_DIR = Path(__file__).parent
if COMMAND_DIR.exists():
    for filepath in COMMAND_DIR.iterdir():
        # Only import .py files that are not __init__.py or helpers.py
        if filepath.suffix == ".py" and filepath.stem not in ("__init__", "helpers"):
            command_name = filepath.stem
            module_name = f"SVG2DrawIOLib.cli.{command_name}"
            try:
                module = importlib.import_module(module_name)
                # Look for a function with the same name as the module
                cli_function = getattr(module, command_name, None)
                if cli_function and callable(cli_function):
                    cli.add_command(cli_function)
                    logger.debug(f"Registered command: {command_name}")
                else:
                    logger.debug(f"No command function found in {module_name}")
            except Exception as e:
                logger.debug(f"Failed to import {module_name}: {e}")


if __name__ == "__main__":
    cli()
