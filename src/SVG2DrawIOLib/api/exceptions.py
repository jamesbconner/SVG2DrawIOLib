"""Exception handlers for the FastAPI application."""

import xml.etree.ElementTree as ET

from fastapi import Request
from fastapi.responses import JSONResponse


async def file_not_found_handler(request: Request, exc: FileNotFoundError) -> JSONResponse:
    """Handle FileNotFoundError as HTTP 404."""
    return JSONResponse(status_code=404, content={"detail": str(exc)})


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Handle ValueError as HTTP 400."""
    return JSONResponse(status_code=400, content={"detail": str(exc)})


async def parse_error_handler(request: Request, exc: ET.ParseError) -> JSONResponse:
    """Handle XML ParseError as HTTP 422."""
    return JSONResponse(status_code=422, content={"detail": f"Invalid XML: {exc}"})


async def import_error_handler(request: Request, exc: ImportError) -> JSONResponse:
    """Handle ImportError (missing optional dependency) as HTTP 503."""
    return JSONResponse(
        status_code=503,
        content={"detail": f"Required dependency not available: {exc}"},
    )
