"""FastAPI application for SVG2DrawIOLib web UI."""

import os
import xml.etree.ElementTree as ET
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from SVG2DrawIOLib.__about__ import __version__
from SVG2DrawIOLib.api.exceptions import (
    ConflictError,
    conflict_error_handler,
    file_not_found_handler,
    import_error_handler,
    parse_error_handler,
    value_error_handler,
)
from SVG2DrawIOLib.api.models.responses import HealthResponse
from SVG2DrawIOLib.api.routers import (
    add,
    create,
    extract,
    inspect,
    remove,
    rename,
    split_paths,
    validate,
)
from SVG2DrawIOLib.api.routers import list as list_router

app = FastAPI(
    title="SVG2DrawIOLib API",
    description="Browser-based UI for converting SVG files into DrawIO shape libraries.",
    version=__version__,
)

# CORS — allow origins from env var, defaulting to local Next.js dev server
allow_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Exception handlers
app.add_exception_handler(FileNotFoundError, file_not_found_handler)  # type: ignore[arg-type]
app.add_exception_handler(ConflictError, conflict_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(ValueError, value_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(ET.ParseError, parse_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(ImportError, import_error_handler)  # type: ignore[arg-type]

# Routers
app.include_router(create.router, prefix="/api")
app.include_router(add.router, prefix="/api")
app.include_router(remove.router, prefix="/api")
app.include_router(rename.router, prefix="/api")
app.include_router(list_router.router, prefix="/api")
app.include_router(extract.router, prefix="/api")
app.include_router(inspect.router, prefix="/api")
app.include_router(validate.router, prefix="/api")
app.include_router(split_paths.router, prefix="/api")


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint.

    Returns:
        Service status and current package version.
    """
    return HealthResponse(status="ok", version=__version__)


# Mount the pre-built Next.js static export when available.
# This is mounted AFTER all /api/* routes so API routes always take priority.
#
# Resolution order:
#   1. SVG2DRAWIO_UI_DIR env var (explicit override)
#   2. Bundled web/ directory next to this package (pip install SVG2DrawIOLib[web])
#   3. web-ui/out/ relative to CWD (source checkout / make start-web)
_env_ui = os.getenv("SVG2DRAWIO_UI_DIR")
if _env_ui:
    _ui_dir = Path(_env_ui)
else:
    _pkg_ui = Path(__file__).parent.parent / "web"
    _ui_dir = _pkg_ui if _pkg_ui.is_dir() else Path("web-ui/out")

if _ui_dir.is_dir():
    app.mount("/", StaticFiles(directory=_ui_dir, html=True), name="ui")
