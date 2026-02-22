"""Router for extracting SVG icons from a DrawIO library."""

import io
import json
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from SVG2DrawIOLib.api.dependencies import get_temp_dir
from SVG2DrawIOLib.cli.helpers import safe_path_join
from SVG2DrawIOLib.icon_analyzer import IconAnalyzer
from SVG2DrawIOLib.library_manager import LibraryManager

router = APIRouter()


@router.post("/extract")
async def extract_icons(
    library_file: UploadFile,
    icon_names: str = Form("[]"),
    tmp: Path = Depends(get_temp_dir),
) -> StreamingResponse:
    """Extract icons from a DrawIO library as SVG files in a ZIP archive.

    Args:
        library_file: The DrawIO library .xml file.
        icon_names: JSON-encoded list of icon names to extract. Pass an
            empty array ``[]`` to extract all icons.
        tmp: Temporary directory (injected dependency).

    Returns:
        StreamingResponse containing a ZIP archive of SVG files.

    Raises:
        HTTPException: 422 if icon_names is not valid JSON.
    """
    try:
        names_parsed = json.loads(icon_names)
        if not isinstance(names_parsed, list):
            raise HTTPException(
                status_code=422,
                detail=f"icon_names must be a JSON array, got {type(names_parsed).__name__}",
            )
        names: list[str] = names_parsed
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=422, detail=f"icon_names must be a JSON array: {exc}"
        ) from exc

    lib_path = safe_path_join(tmp, library_file.filename or "library.xml")
    lib_path.write_bytes(await library_file.read())

    try:
        icons = LibraryManager().load_library(lib_path)
    except ValueError as exc:
        error_msg = str(exc)
        # Library format/parsing errors should return 422
        if "Invalid library" in error_msg:
            raise HTTPException(status_code=422, detail=error_msg) from exc
        # Otherwise, it's an internal error - let it propagate as 500
        raise

    analyzer = IconAnalyzer()

    # Filter to requested icons; empty list means all
    if names:
        names_set = set(names)
        icons = [icon for icon in icons if icon.name in names_set]

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for icon in icons:
            svg_content = analyzer.extract_svg(icon.xml_data)
            zf.writestr(f"{icon.name}.svg", svg_content)

    zip_buffer.seek(0)
    archive_name = f"{lib_path.stem}-icons.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{archive_name}"',
        },
    )
