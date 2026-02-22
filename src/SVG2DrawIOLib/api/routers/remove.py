"""Router for removing icons from a DrawIO library."""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, UploadFile
from fastapi.responses import Response

from SVG2DrawIOLib.api.dependencies import get_temp_dir
from SVG2DrawIOLib.api.services.processing import handle_library_value_error, parse_icon_names
from SVG2DrawIOLib.cli.helpers import safe_path_join, sanitize_filename
from SVG2DrawIOLib.library_manager import LibraryManager

router = APIRouter()


@router.post("/remove")
async def remove_icons(
    library_file: UploadFile,
    icon_names: str = Form(...),
    tmp: Path = Depends(get_temp_dir),
) -> Response:
    """Remove icons from a DrawIO library.

    Args:
        library_file: The DrawIO library .xml file.
        icon_names: JSON-encoded list of icon names to remove.
        tmp: Temporary directory (injected dependency).

    Returns:
        Response containing the updated library with an
        ``X-Icons-Removed`` header indicating how many icons were removed.

    Raises:
        HTTPException: 422 if icon_names is not valid JSON.
    """
    names = parse_icon_names(icon_names)

    lib_path = safe_path_join(tmp, library_file.filename or "library.xml")
    lib_path.write_bytes(await library_file.read())

    try:
        _, removed_count = LibraryManager().remove_icons_from_library(lib_path, names)
    except ValueError as exc:
        handle_library_value_error(exc)

    out_name = sanitize_filename(lib_path.stem) or "library"
    return Response(
        content=lib_path.read_bytes(),
        media_type="application/xml",
        headers={
            "Content-Disposition": f'attachment; filename="{out_name}.xml"',
            "X-Icons-Removed": str(removed_count),
            "Access-Control-Expose-Headers": "X-Icons-Removed",
        },
    )
