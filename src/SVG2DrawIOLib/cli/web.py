"""CLI command for launching the web UI."""

import logging
import threading
import time
import webbrowser
from pathlib import Path

import rich_click as rc

from SVG2DrawIOLib.cli.helpers import console, setup_logging

logger = logging.getLogger(__name__)

# Bundled UI path — present after `pip install SVG2DrawIOLib[web]` + `make build-release`
_BUNDLED_UI = Path(__file__).parent.parent / "web"
# Dev UI path — present after `make build-web` from source checkout
_DEV_UI = Path("web-ui/out")


@rc.command()
@rc.option("--host", default="localhost", show_default=True, help="Host to bind to.")
@rc.option("--port", default=8000, show_default=True, help="Port to listen on.")
@rc.option(
    "--ui-dir",
    default=None,
    envvar="SVG2DRAWIO_UI_DIR",
    help="Path to the pre-built Next.js static export directory.",
)
@rc.option(
    "--no-browser", is_flag=True, default=False, help="Do not open the browser automatically."
)
@rc.option("--verbose", "-v", is_flag=True, default=False)
@rc.option("--quiet", "-q", is_flag=True, default=False)
def web(
    host: str,
    port: int,
    ui_dir: str | None,
    no_browser: bool,
    verbose: bool,
    quiet: bool,
) -> None:
    """[bold cyan]Start the web UI (FastAPI API + built Next.js frontend)[/].

    \b
    \nInstall with web support and run:

        pip install 'SVG2DrawIOLib[web]'
        svg2drawio web

    \b
    Or build from source first:

        cd web-ui && npm run build
        svg2drawio web
    """
    setup_logging(verbose, quiet)

    try:
        import uvicorn  # noqa: PLC0415
    except ImportError as exc:
        raise rc.ClickException(
            "uvicorn is not installed. Install with:\n\n    pip install 'SVG2DrawIOLib[web]'"
        ) from exc

    # Resolve the UI directory
    if ui_dir is not None:
        ui_path = Path(ui_dir)
    elif _BUNDLED_UI.is_dir():
        ui_path = _BUNDLED_UI
    else:
        ui_path = _DEV_UI

    if not ui_path.is_dir():
        raise rc.ClickException(
            f"Web UI build not found at '{ui_path}'.\n\n"
            "Install with web support:\n\n"
            "    pip install 'SVG2DrawIOLib[web]'\n\n"
            "Or build from source:\n\n"
            "    cd web-ui && npm run build"
        )

    url = f"http://{host}:{port}"
    console.print(f"[bold green]SVG2DrawIO Web UI[/bold green]  →  {url}")
    console.print(f"Serving UI from [dim]{ui_path.resolve()}[/dim]")
    console.print("Press [bold]Ctrl+C[/bold] to stop.\n")

    if not no_browser:

        def _open() -> None:
            time.sleep(1.2)
            webbrowser.open(url)

        threading.Thread(target=_open, daemon=True).start()

    uvicorn.run(
        "SVG2DrawIOLib.api.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="warning" if quiet else ("debug" if verbose else "info"),
    )
